# ============================================================================
# module: alb-controller
# 책임: AWS Load Balancer Controller IAM Policy 생성
# 활성화 단계: 5
# ============================================================================

locals {
  name_prefix = "${var.project_name}-${var.env}"
  base_tags   = var.tags
}

# ==== ALB Controller IAM Policy =============================================
# 공식 정책: https://github.com/kubernetes-sigs/aws-load-balancer-controller/blob/main/docs/install/iam_policy.json
data "http" "alb_controller_policy" {
  url = "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.1/docs/install/iam_policy.json"
}

resource "aws_iam_policy" "alb_controller" {
  name        = "${local.name_prefix}-alb-controller-policy"
  description = "IAM policy for AWS Load Balancer Controller"
  policy      = data.http.alb_controller_policy.response_body

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-alb-controller-policy"
  })
}
