output "redis_endpoint" {
  description = "Redis configuration endpoint (cluster mode disabled) 또는 primary endpoint."
  value       = aws_elasticache_replication_group.this.configuration_endpoint_address != "" ? aws_elasticache_replication_group.this.configuration_endpoint_address : aws_elasticache_replication_group.this.primary_endpoint_address
}

output "redis_primary_endpoint" {
  description = "Redis primary endpoint address."
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint address (replica 있을 때만)."
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "redis_port" {
  description = "Redis 포트."
  value       = aws_elasticache_replication_group.this.port
}

output "redis_security_group_id" {
  description = "Redis security group ID."
  value       = aws_security_group.redis.id
}

output "redis_auth_secret_arn" {
  description = "Redis AUTH token이 저장된 Secrets Manager secret ARN (auth_token_enabled=false면 빈 문자열)."
  value       = var.auth_token_secret_arn
}

output "replication_group_id" {
  description = "Redis replication group ID."
  value       = aws_elasticache_replication_group.this.id
}

output "replication_group_arn" {
  description = "Redis replication group ARN."
  value       = aws_elasticache_replication_group.this.arn
}
