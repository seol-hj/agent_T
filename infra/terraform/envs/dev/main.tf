# ============================================================================
# agent-t / envs/dev — 모듈 wiring 진입점
#
# 모든 모듈은 이번 단계(2)에서 skeleton 으로 추가된다.
# 모듈 내부 리소스 정의와 모듈 간 인풋 연결(vpc_id, oidc_provider_arn, ...) 은
# 후속 단계(3·4·5)에서 점진 활성화된다.
#
# 각 모듈 호출 위에 활성화 시점(단계 번호) 을 명시한다.
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

  project_name           = var.project_name
  env                    = var.env
  vpc_id                 = module.vpc.vpc_id
  private_db_subnet_ids  = module.vpc.private_db_subnet_ids
  instance_class         = var.rds_instance_class
  db_secret_arn          = module.secrets_manager.db_credentials_secret_arn
  tags                   = local.common_tags
}

module "redis" {
  source = "../../modules/redis"

  project_name           = var.project_name
  env                    = var.env
  vpc_id                 = module.vpc.vpc_id
  private_db_subnet_ids  = module.vpc.private_db_subnet_ids
  node_type              = var.redis_node_type
  tags                   = local.common_tags
}

module "bedrock" {
  source = "../../modules/bedrock"

  project_name = var.project_name
  env          = var.env
  region       = var.region
  tags         = local.common_tags
}

# === 5단계: EKS / 클러스터 부가 컴포넌트 =====================================
module "eks" {
  source = "../../modules/eks"

  project_name            = var.project_name
  env                     = var.env
  vpc_id                  = module.vpc.vpc_id
  private_app_subnet_ids  = module.vpc.private_app_subnet_ids
  kubernetes_version      = var.eks_cluster_version
  node_groups             = var.eks_node_groups
  tags                    = local.common_tags
}

module "iam_irsa" {
  source = "../../modules/iam-irsa"

  project_name      = var.project_name
  env               = var.env
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = replace(module.eks.cluster_oidc_issuer_url, "https://", "")
  service_accounts  = local.service_accounts_with_policies
  tags              = local.common_tags

  depends_on = [module.alb_controller, module.bedrock]
}

module "alb_controller" {
  source = "../../modules/alb-controller"

  project_name = var.project_name
  env          = var.env
  region       = var.region
  tags         = local.common_tags
}

module "argocd" {
  source = "../../modules/argocd"

  project_name = var.project_name
  env          = var.env
  tags         = local.common_tags
}

# === 6단계: DNS / SSL (선택) ================================================
module "route53" {
  count  = var.enable_route53 ? 1 : 0
  source = "../../modules/route53"

  project_name = var.project_name
  env          = var.env
  domain_name  = var.domain_name
  tags         = local.common_tags

  # ALB 연결은 Ingress 생성 후 수동으로 추가하거나,
  # data source로 Ingress에서 ALB 정보 가져와서 연결
  alb_dns_name    = ""  # 수동 설정 또는 후속 apply에서 추가
  alb_zone_id     = ""
  alb_subdomains  = {}
}

module "acm" {
  count  = var.enable_acm ? 1 : 0
  source = "../../modules/acm"

  project_name              = var.project_name
  env                       = var.env
  domain_name               = var.domain_name
  subject_alternative_names = var.acm_subject_alternative_names
  route53_zone_id           = var.enable_route53 ? module.route53[0].zone_id : ""
  enable_dns_validation     = var.enable_route53
  tags                      = local.common_tags

  depends_on = [module.route53]
}

# ==== Data Sources ==========================================================
data "aws_caller_identity" "current" {}
