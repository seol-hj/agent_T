# ============================================================================
# Outputs
# 모듈이 구체화될 때마다 단계별로 노출. 외부(GitHub Actions, kubeconfig 등)가
# 의존하는 안정적인 키만 둔다.
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
  description = "S3 버킷 키 → 이름 map (IRSA / 앱 환경변수 일괄 주입용)."
  value       = module.s3.bucket_names
}

# === 4단계 (ECR) ===========================================================
output "ecr_repository_urls" {
  description = "service → ECR repository URL map. CI 의 image push 와 Helm image.repository 에 사용."
  value       = module.ecr.repository_urls
}

output "ecr_repository_arns" {
  description = "service → ECR repository ARN map (IRSA 정책 Resource 매칭용)."
  value       = module.ecr.repository_arns
}

output "ecr_registry_id" {
  description = "ECR registry ID (= AWS account ID). docker login URL 구성에 사용."
  value       = module.ecr.registry_id
}

# === 4단계 이후 ============================================================
output "rds_endpoint" {
  description = "RDS 엔드포인트"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis 엔드포인트"
  value       = module.redis.redis_endpoint
}
#
# === 5단계 이후 ============================================================
output "cluster_name" {
  description = "EKS 클러스터 이름"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS 클러스터 엔드포인트"
  value       = module.eks.cluster_endpoint
}

output "cluster_oidc_provider_arn" {
  description = "EKS OIDC provider ARN"
  value       = module.eks.oidc_provider_arn
}

output "alb_controller_role_arn" {
  description = "AWS Load Balancer Controller IRSA Role ARN"
  value       = module.iam_irsa.role_arns["aws-load-balancer-controller"]
}

# === 6단계: DNS / SSL =======================================================
output "route53_zone_id" {
  description = "Route 53 Hosted Zone ID"
  value       = var.enable_route53 ? module.route53[0].zone_id : ""
}

output "route53_name_servers" {
  description = "Route 53 Name Servers - 다른 계정의 도메인 NS 레코드를 이 값으로 설정하세요"
  value       = var.enable_route53 ? module.route53[0].name_servers : []
}

output "acm_certificate_arn" {
  description = "ACM 인증서 ARN - Ingress annotation에 사용"
  value       = var.enable_acm ? module.acm[0].certificate_arn : ""
}

output "acm_certificate_status" {
  description = "ACM 인증서 상태 (ISSUED면 사용 가능)"
  value       = var.enable_acm ? module.acm[0].certificate_status : ""
}
