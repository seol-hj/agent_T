output "certificate_arn" {
  description = "ACM 인증서 ARN (ALB Ingress annotation에 사용)"
  value       = aws_acm_certificate.main.arn
}

output "certificate_id" {
  description = "ACM 인증서 ID"
  value       = aws_acm_certificate.main.id
}

output "certificate_status" {
  description = "인증서 상태 (ISSUED, PENDING_VALIDATION 등)"
  value       = aws_acm_certificate.main.status
}

output "domain_name" {
  description = "인증서 메인 도메인"
  value       = aws_acm_certificate.main.domain_name
}

output "domain_validation_options" {
  description = "DNS 검증 레코드 정보 (수동 검증 시 사용)"
  value       = aws_acm_certificate.main.domain_validation_options
  sensitive   = true
}
