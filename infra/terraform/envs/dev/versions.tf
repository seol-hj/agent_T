terraform {
  required_version = ">= 1.6.0, < 2.0.0"

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
  # State 파일을 S3에 저장하고 DynamoDB로 lock 관리
  # ===========================================================================

  backend "s3" {
    bucket         = "agent-t-terraform-state-dev"
    key            = "dev/terraform.tfstate"
    region         = "ap-northeast-2"
    dynamodb_table = "agent-t-terraform-locks"
    encrypt        = true
  }
}
