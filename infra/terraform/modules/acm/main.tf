# ============================================================================
# module: acm
# 책임: ACM SSL/TLS 인증서 발급 및 DNS 검증
# ============================================================================

locals {
  base_tags = var.tags
}

# ==== ACM 인증서 발급 =======================================================
resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = var.subject_alternative_names
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.base_tags, {
    Name = "${var.project_name}-${var.env}-cert"
  })
}

# ==== DNS 검증 레코드 =======================================================
# Route 53 Hosted Zone에 검증 레코드 자동 생성
resource "aws_route53_record" "cert_validation" {
  for_each = var.enable_dns_validation ? {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.route53_zone_id
}

# ==== 검증 완료 대기 ========================================================
resource "aws_acm_certificate_validation" "main" {
  count = var.enable_dns_validation ? 1 : 0

  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]

  timeouts {
    create = "30m"
  }
}
