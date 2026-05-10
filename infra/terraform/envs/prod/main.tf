# ============================================================================
# agent-t / envs/prod — 모듈 wiring 진입점
#
# 구조는 dev 와 동일. 환경 차이는 terraform.tfvars 와 모듈 내부의 env 분기로
# 표현한다. 같은 모듈을 호출하므로 동작이 비대칭이 되는 일을 방지한다.
# ============================================================================

# === 3단계: 네트워크 (VPC / Endpoints) =======================================
module "vpc" {
  source = "../../modules/vpc"

  project_name       = var.project_name
  env                = var.env
  vpc_cidr           = var.vpc_cidr
  azs                = var.azs
  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = var.single_nat_gateway
  tags               = local.common_tags
}

module "vpc_endpoints" {
  source = "../../modules/vpc-endpoints"

  project_name = var.project_name
  env          = var.env
  region       = var.region

  vpc_id                  = module.vpc.vpc_id
  vpc_cidr_block          = module.vpc.vpc_cidr_block
  private_app_subnet_ids  = module.vpc.private_app_subnet_ids
  private_route_table_ids = module.vpc.private_route_table_ids

  enable_bedrock_endpoint    = var.enable_bedrock_endpoint
  enable_kms_endpoint        = var.enable_kms_endpoint
  enable_cloudwatch_endpoint = var.enable_cloudwatch_endpoint

  tags = local.common_tags
}

# === 4단계: 데이터 / 보안 ====================================================
module "ecr" {
  source = "../../modules/ecr"

  project_name         = var.project_name
  env                  = var.env
  image_tag_mutability = var.ecr_image_tag_mutability
  tags                 = local.common_tags
}

module "s3" {
  source = "../../modules/s3"

  project_name    = var.project_name
  env             = var.env
  lifecycle_rules = var.s3_lifecycle_rules
  tags            = local.common_tags
}

module "secrets_manager" {
  source = "../../modules/secrets-manager"

  project_name = var.project_name
  env          = var.env
  tags         = local.common_tags
}

module "rds" {
  source = "../../modules/rds"

  project_name = var.project_name
  env          = var.env
  tags         = local.common_tags
  # 4단계 추가 인풋: vpc_id, intra_subnet_ids
}

module "redis" {
  source = "../../modules/redis"

  project_name = var.project_name
  env          = var.env
  tags         = local.common_tags
  # 4단계 추가 인풋: vpc_id, intra_subnet_ids
}

module "bedrock" {
  source = "../../modules/bedrock"

  project_name = var.project_name
  env          = var.env
  tags         = local.common_tags
}

# === 5단계: EKS / 클러스터 부가 컴포넌트 =====================================
module "eks" {
  source = "../../modules/eks"

  project_name = var.project_name
  env          = var.env
  tags         = local.common_tags
  # 5단계 추가 인풋: vpc_id, private_subnet_ids
}

module "iam_irsa" {
  source = "../../modules/iam-irsa"

  project_name = var.project_name
  env          = var.env
  tags         = local.common_tags
  # 5단계 추가 인풋: oidc_provider_arn, oidc_provider_url
}

module "alb_controller" {
  source = "../../modules/alb-controller"

  project_name = var.project_name
  env          = var.env
  region       = var.region
  tags         = local.common_tags
  # 5단계 추가 인풋: cluster_name, oidc_provider_arn, oidc_provider_url
}

module "argocd" {
  source = "../../modules/argocd"

  project_name = var.project_name
  env          = var.env
  tags         = local.common_tags
  # 5단계 추가 인풋: cluster_name (helm/kubernetes provider 활성화 후)
}
