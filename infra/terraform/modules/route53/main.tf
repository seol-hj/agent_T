# ============================================================================
# module: route53
# 책임: Route 53 Hosted Zone 및 DNS 레코드 관리
# ============================================================================

locals {
  base_tags = var.tags
}

# ==== Hosted Zone ===========================================================
# 도메인이 다른 계정/등록업체에 있으면 수동으로 NS 레코드 설정 필요
resource "aws_route53_zone" "main" {
  name          = var.domain_name
  force_destroy = false  # 실수로 삭제 방지

  tags = merge(local.base_tags, {
    Name = "${var.project_name}-${var.env}-zone"
  })
}

# ==== ALB DNS 레코드 ========================================================
# ALB 생성 후 연결 (선택적)
resource "aws_route53_record" "alb" {
  for_each = var.alb_subdomains

  zone_id = aws_route53_zone.main.zone_id
  name    = each.value.subdomain  # api, argocd, www 등
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# ==== ACM 검증 레코드 =======================================================
# ACM 모듈에서 생성한 검증 레코드를 여기서 등록
# (ACM 모듈이 이 zone_id를 받아서 직접 생성하는 방식도 가능)
