# ============================================================================
# IRSA Inline Policy 예시 문서
# 실제 정책은 env 단계(dev/main.tf)에서 inline_policies로 주입하거나,
# 별도 aws_iam_policy 리소스를 생성 후 policy_arns로 참조한다.
# ============================================================================

# 이 파일은 정책 템플릿 참고용. 실제 사용은 env 단에서 구현.

# ==== Bedrock 정책 예시 =====================================================
# agent-service가 Bedrock 모델 호출에 필요한 권한.
#
# 사용 예시 (env/dev/main.tf):
#   inline_policies = {
#     bedrock = jsonencode({
#       Version = "2012-10-17"
#       Statement = [
#         {
#           Effect = "Allow"
#           Action = [
#             "bedrock:InvokeModel",
#             "bedrock:InvokeModelWithResponseStream"
#           ]
#           Resource = "arn:aws:bedrock:us-east-1::foundation-model/*"
#         }
#       ]
#     })
#   }

# ==== S3 정책 예시 ==========================================================
# simulation-service가 artifact 버킷에 SUMO 산출물 저장.
#
# 사용 예시:
#   inline_policies = {
#     s3_artifact = jsonencode({
#       Version = "2012-10-17"
#       Statement = [
#         {
#           Effect = "Allow"
#           Action = [
#             "s3:PutObject",
#             "s3:GetObject",
#             "s3:ListBucket"
#           ]
#           Resource = [
#             "arn:aws:s3:::${bucket_name}",
#             "arn:aws:s3:::${bucket_name}/*"
#           ]
#         }
#       ]
#     })
#   }

# ==== Secrets Manager 정책 예시 =============================================
# external-secrets operator가 Secrets Manager에서 비밀 정보 읽기.
#
# 사용 예시:
#   inline_policies = {
#     secrets_read = jsonencode({
#       Version = "2012-10-17"
#       Statement = [
#         {
#           Effect = "Allow"
#           Action = [
#             "secretsmanager:GetSecretValue",
#             "secretsmanager:DescribeSecret"
#           ]
#           Resource = [
#             "arn:aws:secretsmanager:${region}:${account_id}:secret:${project}-${env}-*"
#           ]
#         }
#       ]
#     })
#   }

# ==== ALB Controller 정책 ===================================================
# aws-load-balancer-controller가 ALB 생성/수정/삭제.
#
# 관리형 정책 사용 권장:
#   policy_arns = [
#     "arn:aws:iam::${account_id}:policy/AWSLoadBalancerControllerIAMPolicy"
#   ]
#
# 또는 공식 정책 JSON 다운로드:
# curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json
# aws iam create-policy --policy-name AWSLoadBalancerControllerIAMPolicy --policy-document file://iam_policy.json
