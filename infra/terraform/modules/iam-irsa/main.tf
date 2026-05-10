# ============================================================================
# module: iam-irsa
# 책임: 서비스별 IRSA (IAM Role for Service Account) 일괄 생성.
# 활성화 단계: 5
#
# 설계:
#   - 입력으로 ServiceAccount 명세를 받아 namespace + sa name 별 IAM Role 생성
#   - OIDC provider를 Trust Policy에 추가 (EKS Pod가 해당 Role을 AssumeRole 가능)
#   - 정책은 모듈 외부에서 IAM Policy ARN 또는 inline policy로 주입
#
# 예시:
#   agent-service → bedrock:InvokeModel, secretsmanager:GetSecretValue
#   simulation-service → s3:PutObject (artifact 버킷)
#   report-service → s3:PutObject (reports 버킷)
#   external-secrets → secretsmanager:GetSecretValue
#   aws-load-balancer-controller → ALB 제어 권한
# ============================================================================

locals {
  base_tags = var.tags

  # OIDC provider URL에서 https:// 제거 (Trust Policy 조건에 사용)
  oidc_provider_url_stripped = replace(var.oidc_provider_url, "https://", "")
}

# ==== IAM Role per Service Account ==========================================
resource "aws_iam_role" "this" {
  for_each = var.service_accounts

  name = "${var.project_name}-${var.env}-${each.key}-irsa"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${local.oidc_provider_url_stripped}:sub" = "system:serviceaccount:${each.value.namespace}:${each.value.service_account}"
            "${local.oidc_provider_url_stripped}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.base_tags, {
    Name              = "${var.project_name}-${var.env}-${each.key}-irsa"
    ServiceAccount    = each.value.service_account
    Namespace         = each.value.namespace
    "irsa/managed-by" = "terraform"
  })
}

# ==== Attach Managed Policies ===============================================
# service_accounts[].policy_arns에 지정된 IAM Policy ARN 연결.
resource "aws_iam_role_policy_attachment" "managed" {
  for_each = {
    for pair in flatten([
      for sa_key, sa_value in var.service_accounts : [
        for policy_arn in sa_value.policy_arns : {
          key        = "${sa_key}--${basename(policy_arn)}"
          role_name  = aws_iam_role.this[sa_key].name
          policy_arn = policy_arn
        }
      ]
    ]) : pair.key => pair
  }

  role       = each.value.role_name
  policy_arn = each.value.policy_arn
}

# ==== Inline Policies =======================================================
# service_accounts[].inline_policies에 지정된 인라인 정책 추가.
resource "aws_iam_role_policy" "inline" {
  for_each = {
    for pair in flatten([
      for sa_key, sa_value in var.service_accounts : [
        for policy_name, policy_doc in sa_value.inline_policies : {
          key         = "${sa_key}--${policy_name}"
          role_name   = aws_iam_role.this[sa_key].name
          policy_name = policy_name
          policy_doc  = policy_doc
        }
      ]
    ]) : pair.key => pair
  }

  name   = each.value.policy_name
  role   = each.value.role_name
  policy = each.value.policy_doc
}
