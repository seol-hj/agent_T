# ============================================================================
# module: secrets-manager
# 책임: AWS Secrets Manager 시크릿 컨테이너(메타데이터만) 생성.
# 활성화 단계: 4
#
# 주의:
#   - 시크릿 "값"은 Terraform으로 관리하지 않는다 (state 노출 위험).
#   - RDS 비밀번호: rds 모듈에서 random_password → secret_version으로 1회 주입
#   - 외부 API 키: 운영자가 콘솔/CLI로 수동 주입
#   - lifecycle { ignore_changes = [secret_string] } 로 표류 방지
# ============================================================================

locals {
  base_tags = var.tags
}

# ==== DB Credentials Secret =================================================
# RDS 모듈이 random_password 생성 후 이 secret에 값을 주입한다.
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project_name}-${var.env}-db-credentials"
  description = "RDS PostgreSQL master credentials for ${var.env} environment"

  kms_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null

  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(local.base_tags, {
    Name    = "${var.project_name}-${var.env}-db-credentials"
    Purpose = "rds-postgres"
  })
}

# ==== Application Secrets ===================================================
# 애플리케이션이 사용하는 API 키, 토큰 등을 저장하는 컨테이너.
# 값은 운영자가 수동으로 주입한다.
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.project_name}-${var.env}-app-secrets"
  description = "Application secrets (API keys, tokens) for ${var.env} environment"

  kms_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null

  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(local.base_tags, {
    Name    = "${var.project_name}-${var.env}-app-secrets"
    Purpose = "application"
  })
}

# ==== Bedrock Config Secret =================================================
# Bedrock 모델 설정, 엔드포인트, 리전 등을 저장.
# 값은 운영자가 수동으로 주입한다.
resource "aws_secretsmanager_secret" "bedrock_config" {
  name        = "${var.project_name}-${var.env}-bedrock-config"
  description = "Bedrock model configuration for ${var.env} environment"

  kms_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null

  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(local.base_tags, {
    Name    = "${var.project_name}-${var.env}-bedrock-config"
    Purpose = "llm-gateway"
  })
}

# ==== Redis Auth Token Secret (Optional) ====================================
# Redis auth token을 저장. 값은 운영자 또는 redis 모듈이 주입.
resource "aws_secretsmanager_secret" "redis_auth" {
  count = var.create_redis_auth_secret ? 1 : 0

  name        = "${var.project_name}-${var.env}-redis-auth"
  description = "Redis auth token for ${var.env} environment"

  kms_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null

  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(local.base_tags, {
    Name    = "${var.project_name}-${var.env}-redis-auth"
    Purpose = "redis"
  })
}
