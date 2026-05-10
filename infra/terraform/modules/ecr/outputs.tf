output "repository_urls" {
  description = "repo key → repository URL map (CI push, Helm values 의 image.repository 에 사용)."
  value       = { for k, v in aws_ecr_repository.this : k => v.repository_url }
}

output "repository_arns" {
  description = "repo key → ARN map (IRSA 정책의 Resource 에 사용)."
  value       = { for k, v in aws_ecr_repository.this : k => v.arn }
}

output "repository_names" {
  description = "repo key → 전체 레포 이름 map (예: 'agent-t-dev/api-service')."
  value       = { for k, v in aws_ecr_repository.this : k => v.name }
}

output "registry_id" {
  description = "ECR registry ID (= AWS account ID). docker login URL 구성에 사용."
  value       = length(aws_ecr_repository.this) > 0 ? values(aws_ecr_repository.this)[0].registry_id : ""
}
