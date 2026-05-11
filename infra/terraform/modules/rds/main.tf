# ============================================================================
# module: rds
# 책임: RDS PostgreSQL 인스턴스 + 서브넷그룹 + 파라미터그룹 + SG.
# 활성화 단계: 4
#
# 설계:
#   - private_db_subnet_ids (intra subnet) 에 배치 → NAT 미경유
#   - 비밀번호: random_password 생성 → Secrets Manager 저장
#   - EKS private-app subnet에서만 접근 가능한 security group
#   - dev: db.t4g.micro / Multi-AZ off / 백업 7일
#   - prod: db.r7g.large+ / Multi-AZ on / 백업 30일 / 삭제 보호 on
# ============================================================================

locals {
  base_tags = var.tags

  db_identifier = "${var.project_name}-${var.env}-postgres"
  db_port       = 5432
}

# ==== Random Password =======================================================
# RDS master password를 자동 생성. Secrets Manager에 저장 후 애플리케이션이 참조.
resource "random_password" "master" {
  length  = 32
  special = true
  # RDS 비밀번호 특수문자 제약: @, /, ", ' 제외
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# ==== DB Subnet Group =======================================================
resource "aws_db_subnet_group" "this" {
  name       = "${local.db_identifier}-subnet-group"
  subnet_ids = var.private_db_subnet_ids

  tags = merge(local.base_tags, {
    Name = "${local.db_identifier}-subnet-group"
  })
}

# ==== Security Group ========================================================
# RDS 전용 SG. EKS 노드 SG 또는 private-app subnet CIDR에서만 PostgreSQL 포트 허용.
resource "aws_security_group" "rds" {
  name        = "${local.db_identifier}-sg"
  description = "Security group for RDS PostgreSQL ${var.env}"
  vpc_id      = var.vpc_id

  tags = merge(local.base_tags, {
    Name = "${local.db_identifier}-sg"
  })
}

# Ingress: EKS 노드 SG에서 PostgreSQL 포트
resource "aws_vpc_security_group_ingress_rule" "from_eks_sg" {
  count = length(var.allowed_security_group_ids)

  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = var.allowed_security_group_ids[count.index]
  from_port                    = local.db_port
  to_port                      = local.db_port
  ip_protocol                  = "tcp"
  description                  = "PostgreSQL from EKS SG ${count.index}"
}

# Ingress: private-app subnet CIDR에서 PostgreSQL 포트
resource "aws_vpc_security_group_ingress_rule" "from_cidr" {
  count = length(var.allowed_cidr_blocks)

  security_group_id = aws_security_group.rds.id
  cidr_ipv4         = var.allowed_cidr_blocks[count.index]
  from_port         = local.db_port
  to_port           = local.db_port
  ip_protocol       = "tcp"
  description       = "PostgreSQL from CIDR ${var.allowed_cidr_blocks[count.index]}"
}

# Egress: 전체 허용 (응답 트래픽)
resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.rds.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound"
}

# ==== Parameter Group =======================================================
resource "aws_db_parameter_group" "this" {
  name   = "${local.db_identifier}-params"
  family = "postgres16"

  # PostgreSQL 성능 튜닝 파라미터 (환경에 따라 조정)
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "log_statement"
    value = "all"
    # dev: all, prod: ddl 또는 mod 권장
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000" # 1초 이상 쿼리 로깅
  }

  tags = merge(local.base_tags, {
    Name = "${local.db_identifier}-params"
  })
}

# ==== RDS Instance ==========================================================
resource "aws_db_instance" "this" {
  identifier = local.db_identifier

  # Engine
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  # Storage
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage > 0 ? var.max_allocated_storage : null
  storage_type          = "gp3"
  storage_encrypted     = true

  # Database
  db_name  = var.db_name
  username = var.master_username
  password = random_password.master.result
  port     = local.db_port

  # Network
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # High Availability
  multi_az = var.multi_az

  # Backup
  backup_retention_period = var.backup_retention_days
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window

  # Deletion
  deletion_protection = var.deletion_protection
  skip_final_snapshot = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${local.db_identifier}-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Parameter Group
  parameter_group_name = aws_db_parameter_group.this.name

  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  tags = merge(local.base_tags, {
    Name = local.db_identifier
  })
}

# ==== Secrets Manager에 인증 정보 저장 ======================================
# secrets-manager 모듈이 생성한 secret에 값을 주입.
resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = var.db_secret_arn

  secret_string = jsonencode({
    username = var.master_username
    password = random_password.master.result
    engine   = "postgres"
    host     = aws_db_instance.this.address
    port     = aws_db_instance.this.port
    dbname   = var.db_name
  })
}
