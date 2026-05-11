output "bedrock_invoke_policy_arn" {
  description = "Bedrock 모델 호출 IAM Policy ARN"
  value       = aws_iam_policy.bedrock_invoke.arn
}
