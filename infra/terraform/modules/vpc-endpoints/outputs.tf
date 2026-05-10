output "security_group_id" {
  description = "Interface endpoint 의 ENI 가 사용하는 SG ID."
  value       = aws_security_group.endpoints.id
}

# ==== S3 Gateway =============================================================
output "s3_endpoint_id" {
  description = "S3 Gateway endpoint ID."
  value       = aws_vpc_endpoint.s3.id
}

output "s3_endpoint_prefix_list_id" {
  description = "S3 Gateway endpoint 의 prefix list ID (SG egress 제한 시 destination 으로 사용 가능)."
  value       = aws_vpc_endpoint.s3.prefix_list_id
}

# ==== Interface Endpoints ====================================================
output "interface_endpoint_ids" {
  description = "활성화된 Interface endpoint ID 목록 (key = 서비스 라벨)."
  value       = { for k, v in aws_vpc_endpoint.interface : k => v.id }
}

output "interface_endpoint_dns_entries" {
  description = "활성화된 Interface endpoint 별 DNS 엔트리 (디버깅/연결 검증용)."
  value       = { for k, v in aws_vpc_endpoint.interface : k => v.dns_entry }
}

output "enabled_endpoints" {
  description = "이번 plan 에서 실제로 생성된 endpoint 라벨 목록."
  value       = concat(["s3"], keys(aws_vpc_endpoint.interface))
}
