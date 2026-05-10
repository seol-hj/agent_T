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
  # 부트스트랩 절차는 docs/infrastructure.md 참조.
  # prod 는 dev 와 같은 backend 버킷을 공유하되 key 만 분리한다.
  # ===========================================================================
  #
  # backend "s3" {
  #   bucket         = "agent-t-tfstate-<aws-account-id>"
  #   key            = "envs/prod/terraform.tfstate"
  #   region         = "ap-northeast-2"
  #   dynamodb_table = "agent-t-tflock"
  #   encrypt        = true
  # }
}
