# ============================================================================
# Outputs
# dev 와 동일한 출력 키 셋을 유지한다 (외부 도구가 환경별로 다른 키를 알 필요 없게).
# ============================================================================

output "project_name" {
  description = "프로젝트 식별자."
  value       = var.project_name
}

output "env" {
  description = "환경 식별자."
  value       = var.env
}

output "region" {
  description = "AWS 리전."
  value       = var.region
}

# === 3단계 (VPC) ============================================================
output "vpc_id" {
  description = "VPC ID."
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block."
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs."
  value       = module.vpc.public_subnet_ids
}

output "private_app_subnet_ids" {
  description = "Private-app subnet IDs."
  value       = module.vpc.private_app_subnet_ids
}

output "private_db_subnet_ids" {
  description = "Private-db subnet IDs."
  value       = module.vpc.private_db_subnet_ids
}

output "private_route_table_ids" {
  description = "VPC Endpoint(Gateway) 용 private route table 전체 (app + db)."
  value       = module.vpc.private_route_table_ids
}

# === 3단계 (VPC Endpoints) =================================================
output "vpc_endpoint_security_group_id" {
  description = "Interface endpoint ENI 의 SG ID."
  value       = module.vpc_endpoints.security_group_id
}

output "vpc_endpoint_s3_id" {
  description = "S3 Gateway endpoint ID."
  value       = module.vpc_endpoints.s3_endpoint_id
}

output "vpc_endpoint_s3_prefix_list_id" {
  description = "S3 Gateway endpoint prefix list ID."
  value       = module.vpc_endpoints.s3_endpoint_prefix_list_id
}

output "vpc_interface_endpoint_ids" {
  description = "Interface endpoint id map (라벨 → id)."
  value       = module.vpc_endpoints.interface_endpoint_ids
}

output "vpc_enabled_endpoints" {
  description = "이번 plan 에서 실제로 생성된 endpoint 라벨 목록."
  value       = module.vpc_endpoints.enabled_endpoints
}

# === 4단계 (S3) ============================================================
output "s3_artifact_bucket" {
  description = "SUMO 산출물 버킷 이름."
  value       = module.s3.artifact_bucket_name
}

output "s3_rag_source_bucket" {
  description = "RAG 문서 원본 버킷 이름."
  value       = module.s3.rag_source_bucket_name
}

output "s3_reports_bucket" {
  description = "리포트 버킷 이름."
  value       = module.s3.reports_bucket_name
}

output "s3_model_data_bucket" {
  description = "모델 학습/평가 데이터 버킷 이름."
  value       = module.s3.model_data_bucket_name
}

output "s3_bucket_names" {
  description = "S3 버킷 키 → 이름 map."
  value       = module.s3.bucket_names
}

# === 4단계 (ECR) ===========================================================
output "ecr_repository_urls" {
  description = "service → ECR repository URL map."
  value       = module.ecr.repository_urls
}

output "ecr_repository_arns" {
  description = "service → ECR repository ARN map."
  value       = module.ecr.repository_arns
}

output "ecr_registry_id" {
  description = "ECR registry ID (= AWS account ID)."
  value       = module.ecr.registry_id
}

# === 4단계 이후 ============================================================
# output "rds_endpoint"        { value = module.rds.endpoint sensitive = true }
# output "redis_endpoint"      { value = module.redis.primary_endpoint }
#
# === 5단계 이후 ============================================================
# output "eks_cluster_name"     { value = module.eks.cluster_name }
# output "eks_cluster_endpoint" { value = module.eks.cluster_endpoint }
# output "eks_oidc_provider_arn"{ value = module.eks.oidc_provider_arn }
