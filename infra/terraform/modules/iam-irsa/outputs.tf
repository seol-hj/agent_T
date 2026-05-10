output "role_arns" {
  description = "서비스별 IAM Role ARN map (Helm values의 serviceAccount.annotations에 사용)."
  value       = { for k, v in aws_iam_role.this : k => v.arn }
}

output "role_names" {
  description = "서비스별 IAM Role 이름 map."
  value       = { for k, v in aws_iam_role.this : k => v.name }
}

output "service_account_annotations" {
  description = "Kubernetes ServiceAccount에 추가할 annotations (eks.amazonaws.com/role-arn)."
  value = {
    for k, v in aws_iam_role.this : k => {
      "eks.amazonaws.com/role-arn" = v.arn
    }
  }
}
