output "db_endpoint" {
  description = "RDS 엔드포인트 (host:port)."
  value       = aws_db_instance.this.endpoint
}

output "db_address" {
  description = "RDS 호스트 주소 (포트 제외)."
  value       = aws_db_instance.this.address
}

output "db_port" {
  description = "RDS 포트."
  value       = aws_db_instance.this.port
}

output "db_name" {
  description = "초기 생성된 데이터베이스 이름."
  value       = aws_db_instance.this.db_name
}

output "db_instance_id" {
  description = "RDS 인스턴스 식별자."
  value       = aws_db_instance.this.id
}

output "db_instance_arn" {
  description = "RDS 인스턴스 ARN."
  value       = aws_db_instance.this.arn
}

output "db_security_group_id" {
  description = "RDS security group ID."
  value       = aws_security_group.rds.id
}

output "db_secret_arn" {
  description = "RDS 인증 정보가 저장된 Secrets Manager secret ARN (Pod IRSA 정책에 사용)."
  value       = var.db_secret_arn
}

output "master_username" {
  description = "RDS 마스터 사용자 이름."
  value       = var.master_username
  sensitive   = true
}
