# ============================================================================
# module: bedrock
# 책임: Bedrock 모델 호출 IAM Policy 생성
# 활성화 단계: 4
#
# 메모:
#   - Bedrock 모델 access 자체는 콘솔에서 enable (account 레벨, IaC 외부)
#   - IRSA에 attach할 IAM Policy만 본 모듈에서 생성:
#       - bedrock:InvokeModel, bedrock:InvokeModelWithResponseStream
#       - bedrock:ListFoundationModels (옵션)
#   - Guardrail / Knowledge Base는 본격 사용 시 추가 (아래 주석 참조)
#   - 비즈니스 로직은 직접 호출 금지 → LLM Gateway 경유 (CLAUDE.md 참조)
# ============================================================================

locals {
  name_prefix = "${var.project_name}-${var.env}"
  base_tags   = var.tags
}

# ==== Bedrock Invoke Policy =================================================
resource "aws_iam_policy" "bedrock_invoke" {
  name        = "${local.name_prefix}-bedrock-invoke"
  description = "Policy for invoking AWS Bedrock models"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockInvokeModel"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.region}::foundation-model/*"
        ]
      },
      {
        Sid    = "BedrockListModels"
        Effect = "Allow"
        Action = [
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-bedrock-invoke"
  })
}

# ==== Knowledge Base Policy (미래 사용, 현재 주석) ============================
# RAG 구현 시 활성화
# resource "aws_iam_policy" "bedrock_knowledge_base" {
#   name = "${local.name_prefix}-bedrock-kb"
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Sid    = "BedrockKnowledgeBase"
#         Effect = "Allow"
#         Action = [
#           "bedrock:Retrieve",
#           "bedrock:RetrieveAndGenerate"
#         ]
#         Resource = [
#           "arn:aws:bedrock:${var.region}:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
#         ]
#       }
#     ]
#   })
# }

# ==== Guardrail Policy (미래 사용, 현재 주석) =================================
# 콘텐츠 필터링 사용 시 활성화
# resource "aws_iam_policy" "bedrock_guardrail" {
#   name = "${local.name_prefix}-bedrock-guardrail"
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Sid    = "BedrockGuardrail"
#         Effect = "Allow"
#         Action = [
#           "bedrock:ApplyGuardrail"
#         ]
#         Resource = [
#           "arn:aws:bedrock:${var.region}:${data.aws_caller_identity.current.account_id}:guardrail/*"
#         ]
#       }
#     ]
#   })
# }
