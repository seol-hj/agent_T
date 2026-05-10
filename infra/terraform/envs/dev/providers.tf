provider "aws" {
  region = var.region

  default_tags {
    tags = local.common_tags
  }
}

# ============================================================================
# kubernetes / helm provider 는 EKS 가 생성된 이후에 활성화한다 (5단계).
# 활성화 시 module "eks" 의 outputs (cluster_endpoint / oidc / CA) 를 사용.
# ============================================================================
#
# data "aws_eks_cluster"      "this" { name = module.eks.cluster_name }
# data "aws_eks_cluster_auth" "this" { name = module.eks.cluster_name }
#
# provider "kubernetes" {
#   host                   = data.aws_eks_cluster.this.endpoint
#   cluster_ca_certificate = base64decode(data.aws_eks_cluster.this.certificate_authority[0].data)
#   token                  = data.aws_eks_cluster_auth.this.token
# }
#
# provider "helm" {
#   kubernetes {
#     host                   = data.aws_eks_cluster.this.endpoint
#     cluster_ca_certificate = base64decode(data.aws_eks_cluster.this.certificate_authority[0].data)
#     token                  = data.aws_eks_cluster_auth.this.token
#   }
# }
