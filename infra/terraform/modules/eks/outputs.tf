output "cluster_name" {
  description = "EKS 클러스터 이름."
  value       = aws_eks_cluster.this.name
}

output "cluster_id" {
  description = "EKS 클러스터 ID."
  value       = aws_eks_cluster.this.id
}

output "cluster_arn" {
  description = "EKS 클러스터 ARN."
  value       = aws_eks_cluster.this.arn
}

output "cluster_endpoint" {
  description = "EKS 클러스터 API 엔드포인트 (kubectl 접근)."
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  description = "EKS 클러스터 CA 인증서 (base64 인코딩)."
  value       = aws_eks_cluster.this.certificate_authority[0].data
  sensitive   = true
}

output "cluster_version" {
  description = "EKS Kubernetes 버전."
  value       = aws_eks_cluster.this.version
}

output "cluster_security_group_id" {
  description = "EKS 클러스터 security group ID."
  value       = aws_security_group.cluster.id
}

output "node_security_group_id" {
  description = "EKS 노드 security group ID (RDS/Redis 접근 허용에 사용)."
  value       = aws_security_group.node.id
}

output "cluster_oidc_issuer_url" {
  description = "EKS 클러스터 OIDC provider URL (IRSA 설정에 사용)."
  value       = var.enable_irsa ? aws_eks_cluster.this.identity[0].oidc[0].issuer : ""
}

output "oidc_provider_arn" {
  description = "IAM OIDC provider ARN (IRSA Trust Policy에 사용)."
  value       = var.enable_irsa ? aws_iam_openid_connect_provider.cluster[0].arn : ""
}

output "node_group_names" {
  description = "Managed node group 이름 목록."
  value       = [for ng in aws_eks_node_group.this : ng.node_group_name]
}

output "node_group_arns" {
  description = "Managed node group ARN 목록."
  value       = [for ng in aws_eks_node_group.this : ng.arn]
}

output "node_role_arn" {
  description = "EKS 노드 IAM Role ARN."
  value       = aws_iam_role.node.arn
}
