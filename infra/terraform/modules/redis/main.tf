# ============================================================================
# module: redis
# 책임: ElastiCache Redis (replication group) + SG + 서브넷그룹.
# 활성화 단계: 4
#
# 설계:
#   - private_db_subnet_ids (intra subnet) 에 배치 → NAT 미경유
#   - EKS private-app subnet에서만 접근 가능한 security group
#   - dev: cache.t4g.micro / single node
#   - prod: cache.r7g.large+ / replication group / Multi-AZ / failover on
#   - 전송 중 + 저장 데이터 암호화 활성화
#   - AUTH token (optional) → Secrets Manager에 저장
# ============================================================================

locals {
  base_tags = var.tags

  replication_group_id = "${var.project_name}-${var.env}-redis"
  redis_port           = 6379
}

# ==== Random Password for AUTH Token ========================================
# transit_encryption_enabled=true + auth_token_enabled=true 시 AUTH token 생성.
resource "random_password" "auth_token" {
  count = var.auth_token_enabled ? 1 : 0

  length  = 64
  special = false # Redis AUTH token은 영숫자만 허용
}

# ==== Subnet Group ==========================================================
resource "aws_elasticache_subnet_group" "this" {
  name       = "${local.replication_group_id}-subnet-group"
  subnet_ids = var.private_db_subnet_ids

  tags = merge(local.base_tags, {
    Name = "${local.replication_group_id}-subnet-group"
  })
}

# ==== Security Group ========================================================
# Redis 전용 SG. EKS 노드 SG 또는 private-app subnet CIDR에서만 Redis 포트 허용.
resource "aws_security_group" "redis" {
  name        = "${local.replication_group_id}-sg"
  description = "Security group for Redis ${var.env}"
  vpc_id      = var.vpc_id

  tags = merge(local.base_tags, {
    Name = "${local.replication_group_id}-sg"
  })
}

# Ingress: EKS 노드 SG에서 Redis 포트
resource "aws_vpc_security_group_ingress_rule" "from_eks_sg" {
  count = length(var.allowed_security_group_ids)

  security_group_id            = aws_security_group.redis.id
  referenced_security_group_id = var.allowed_security_group_ids[count.index]
  from_port                    = local.redis_port
  to_port                      = local.redis_port
  ip_protocol                  = "tcp"
  description                  = "Redis from EKS SG ${count.index}"
}

# Ingress: private-app subnet CIDR에서 Redis 포트
resource "aws_vpc_security_group_ingress_rule" "from_cidr" {
  count = length(var.allowed_cidr_blocks)

  security_group_id = aws_security_group.redis.id
  cidr_ipv4         = var.allowed_cidr_blocks[count.index]
  from_port         = local.redis_port
  to_port           = local.redis_port
  ip_protocol       = "tcp"
  description       = "Redis from CIDR ${var.allowed_cidr_blocks[count.index]}"
}

# Egress: 전체 허용 (응답 트래픽)
resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.redis.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound"
}

# ==== Parameter Group =======================================================
resource "aws_elasticache_parameter_group" "this" {
  name   = "${local.replication_group_id}-params"
  family = "redis7"

  # Redis 설정 파라미터 (필요 시 추가)
  parameter {
    name  = "timeout"
    value = "300"
  }

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru" # LRU 캐시 정책
  }

  tags = merge(local.base_tags, {
    Name = "${local.replication_group_id}-params"
  })
}

# ==== Replication Group =====================================================
resource "aws_elasticache_replication_group" "this" {
  replication_group_id = local.replication_group_id
  description          = "Redis replication group for ${var.env}"

  # Engine
  engine               = "redis"
  engine_version       = var.engine_version
  node_type            = var.node_type
  parameter_group_name = aws_elasticache_parameter_group.this.name
  port                 = local.redis_port

  # Cluster configuration
  num_cache_clusters         = var.num_cache_clusters
  multi_az_enabled           = var.multi_az_enabled
  automatic_failover_enabled = var.automatic_failover_enabled

  # Network
  subnet_group_name  = aws_elasticache_subnet_group.this.name
  security_group_ids = [aws_security_group.redis.id]

  # Encryption
  at_rest_encryption_enabled = var.at_rest_encryption_enabled
  transit_encryption_enabled = var.transit_encryption_enabled
  auth_token                 = var.auth_token_enabled ? random_password.auth_token[0].result : null

  # Backup
  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window          = var.snapshot_window
  maintenance_window       = var.maintenance_window

  # Logging (CloudWatch Logs)
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_engine_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "engine-log"
  }

  tags = merge(local.base_tags, {
    Name = local.replication_group_id
  })
}

# ==== CloudWatch Log Groups =================================================
resource "aws_cloudwatch_log_group" "redis_slow_log" {
  name              = "/aws/elasticache/redis/${local.replication_group_id}/slow-log"
  retention_in_days = 7

  tags = merge(local.base_tags, {
    Name = "${local.replication_group_id}-slow-log"
  })
}

resource "aws_cloudwatch_log_group" "redis_engine_log" {
  name              = "/aws/elasticache/redis/${local.replication_group_id}/engine-log"
  retention_in_days = 7

  tags = merge(local.base_tags, {
    Name = "${local.replication_group_id}-engine-log"
  })
}

# ==== Secrets Manager에 AUTH Token 저장 =====================================
# auth_token_enabled=true 시 Secrets Manager에 AUTH token 저장.
resource "aws_secretsmanager_secret_version" "redis_auth" {
  count = var.auth_token_enabled && var.auth_token_secret_arn != "" ? 1 : 0

  secret_id = var.auth_token_secret_arn

  secret_string = jsonencode({
    auth_token = random_password.auth_token[0].result
    host       = aws_elasticache_replication_group.this.configuration_endpoint_address
    port       = aws_elasticache_replication_group.this.port
  })
}
