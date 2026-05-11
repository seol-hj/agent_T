# ============================================================================
# module: vpc-endpoints
# 책임:
#   - S3 Gateway endpoint → private route table 에 attach
#   - Interface endpoint 8 종 → private-app subnet 에 ENI, 자체 SG, private DNS 활성
#   - Bedrock service name 은 region 기반 자동 도출 (override 변수 제공)
# 활성화 단계: 3
# ============================================================================

locals {
  name_prefix = "${var.project_name}-${var.env}"
  base_tags   = var.tags

  # --- Bedrock service name 자동 도출 (필요 시 override) ---------------------
  bedrock_runtime_service = (
    var.bedrock_runtime_service_name != ""
    ? var.bedrock_runtime_service_name
    : "com.amazonaws.${var.region}.bedrock-runtime"
  )
  bedrock_service = (
    var.bedrock_service_name != ""
    ? var.bedrock_service_name
    : "com.amazonaws.${var.region}.bedrock"
  )

  # --- Interface endpoint 카탈로그 (key = 짧은 라벨) -------------------------
  # always_on 은 사용자가 비활성화 못하게 — 운영상 핵심.
  interface_endpoints_all = {
    "ecr-api" = {
      service_name = "com.amazonaws.${var.region}.ecr.api"
      enabled      = true
    }
    "ecr-dkr" = {
      service_name = "com.amazonaws.${var.region}.ecr.dkr"
      enabled      = true
    }
    "secretsmanager" = {
      service_name = "com.amazonaws.${var.region}.secretsmanager"
      enabled      = true
    }
    "sts" = {
      service_name = "com.amazonaws.${var.region}.sts"
      enabled      = true
    }
    "logs" = {
      service_name = "com.amazonaws.${var.region}.logs"
      enabled      = var.enable_cloudwatch_endpoint
    }
    "kms" = {
      service_name = "com.amazonaws.${var.region}.kms"
      enabled      = var.enable_kms_endpoint
    }
    "bedrock-runtime" = {
      service_name = local.bedrock_runtime_service
      enabled      = var.enable_bedrock_endpoint
    }
    "bedrock" = {
      service_name = local.bedrock_service
      enabled      = var.enable_bedrock_endpoint
    }
  }

  # 활성화된 endpoint 만 추출 → for_each
  interface_endpoints = {
    for k, v in local.interface_endpoints_all : k => v if v.enabled
  }
}

# ==== Security Group =========================================================
# Interface endpoint 의 ENI 가 사용. VPC 내부에서 443 으로만 도달 가능.
resource "aws_security_group" "endpoints" {
  name        = "${local.name_prefix}-vpce-sg"
  description = "VPC Interface Endpoint SG - HTTPS from within VPC"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from within VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }

  egress {
    description = "Allow endpoint ENI to respond to clients"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-vpce-sg"
  })
}

# ==== S3 Gateway Endpoint ====================================================
# private_route_table_ids 에 0.0.0.0/0 을 우회하는 prefix-list 라우트가 자동 추가된다.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.private_route_table_ids

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-vpce-s3"
    Type = "Gateway"
  })
}

# ==== Interface Endpoints (for_each) =========================================
resource "aws_vpc_endpoint" "interface" {
  for_each = local.interface_endpoints

  vpc_id              = var.vpc_id
  service_name        = each.value.service_name
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.private_app_subnet_ids
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = true

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-vpce-${each.key}"
    Type = "Interface"
  })
}
