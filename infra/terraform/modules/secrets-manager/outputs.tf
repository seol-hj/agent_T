output "db_credentials_secret_arn" {
  description = "RDS 인증 정보를 저장하는 시크릿의 ARN (Pod IRSA 정책에 사용)."
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "db_credentials_secret_name" {
  description = "RDS 인증 정보를 저장하는 시크릿의 이름 (RDS 모듈이 값 주입 시 사용)."
  value       = aws_secretsmanager_secret.db_credentials.name
}

output "app_secrets_secret_arn" {
  description = "애플리케이션 시크릿 ARN (Pod IRSA 정책에 사용)."
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "app_secrets_secret_name" {
  description = "애플리케이션 시크릿 이름."
  value       = aws_secretsmanager_secret.app_secrets.name
}

output "bedrock_config_secret_arn" {
  description = "Bedrock 설정 시크릿 ARN (LLM Gateway Pod IRSA 정책에 사용)."
  value       = aws_secretsmanager_secret.bedrock_config.arn
}

output "bedrock_config_secret_name" {
  description = "Bedrock 설정 시크릿 이름."
  value       = aws_secretsmanager_secret.bedrock_config.name
}

output "redis_auth_secret_arn" {
  description = "Redis auth token 시크릿 ARN (create_redis_auth_secret=false면 빈 문자열)."
  value       = var.create_redis_auth_secret ? aws_secretsmanager_secret.redis_auth[0].arn : ""
}

output "redis_auth_secret_name" {
  description = "Redis auth token 시크릿 이름."
  value       = var.create_redis_auth_secret ? aws_secretsmanager_secret.redis_auth[0].name : ""
}
