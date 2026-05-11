output "zone_id" {
  description = "Route 53 Hosted Zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "zone_arn" {
  description = "Route 53 Hosted Zone ARN"
  value       = aws_route53_zone.main.arn
}

output "name_servers" {
  description = "Name servers - 다른 계정/등록업체의 도메인 NS 레코드를 이 값으로 설정하세요"
  value       = aws_route53_zone.main.name_servers
}

output "domain_name" {
  description = "도메인 이름"
  value       = aws_route53_zone.main.name
}
