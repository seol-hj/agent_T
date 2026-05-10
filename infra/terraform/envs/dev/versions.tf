terraform {
  required_version = ">= 1.9.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.15"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.32"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # ===========================================================================
  # Remote backend (S3 + DynamoDB)
  # ---------------------------------------------------------------------------
  # 부트스트랩 절차는 docs/infrastructure.md → "Terraform 실행 순서" 참조.
  # backend 활성화 후, `terraform init -migrate-state` 로 로컬 state → 원격 이전.
  # ===========================================================================
  #
  # backend "s3" {
  #   bucket         = "agent-t-tfstate-<aws-account-id>"
  #   key            = "envs/dev/terraform.tfstate"
  #   region         = "ap-northeast-2"
  #   dynamodb_table = "agent-t-tflock"
  #   encrypt        = true
  # }
}
