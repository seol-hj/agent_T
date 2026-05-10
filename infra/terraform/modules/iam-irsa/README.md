# Terraform Module: IAM IRSA

서비스별 IRSA (IAM Role for Service Account) 일괄 생성.

---

## 책임

- Kubernetes ServiceAccount별 IAM Role 생성
- OIDC provider를 Trust Policy에 추가 (EKS Pod가 AssumeRole 가능)
- 관리형 IAM Policy 또는 인라인 정책 연결
- ServiceAccount annotation 출력 (Helm values 사용)

---

## 입력 변수

| 변수 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `project_name` | string | ✅ | - | 프로젝트 식별자 |
| `env` | string | ✅ | - | 환경 (dev / prod) |
| `oidc_provider_arn` | string | ✅ | - | EKS OIDC provider ARN (EKS 모듈 출력) |
| `oidc_provider_url` | string | ✅ | - | EKS OIDC provider URL (EKS 모듈 출력) |
| `service_accounts` | map(object) | ✅ | - | 서비스별 IRSA 설정 |
| `tags` | map(string) | | `{}` | 공통 태그 |

---

## service_accounts 변수 구조

```hcl
service_accounts = {
  "<service-key>" = {
    namespace       = "<kubernetes-namespace>"
    service_account = "<service-account-name>"
    policy_arns     = ["<iam-policy-arn>", ...]  # 선택사항
    inline_policies = {                          # 선택사항
      "<policy-name>" = "<policy-json-string>"
    }
  }
}
```

---

## 출력

| 출력 | 설명 |
|---|---|
| `role_arns` | 서비스별 IAM Role ARN map |
| `role_names` | 서비스별 IAM Role 이름 map |
| `service_account_annotations` | ServiceAccount에 추가할 annotations |

---

## 사용 예시

### 1. 모듈 호출 (env/dev/main.tf)

```hcl
module "irsa" {
  source = "../../modules/iam-irsa"

  project_name       = var.project_name
  env                = var.env
  oidc_provider_arn  = module.eks.oidc_provider_arn
  oidc_provider_url  = module.eks.cluster_oidc_issuer_url

  service_accounts = {
    agent-service = {
      namespace       = "default"
      service_account = "agent-service"
      inline_policies = {
        bedrock = jsonencode({
          Version = "2012-10-17"
          Statement = [
            {
              Effect = "Allow"
              Action = [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
              ]
              Resource = "arn:aws:bedrock:us-east-1::foundation-model/*"
            }
          ]
        })
        s3_rag = jsonencode({
          Version = "2012-10-17"
          Statement = [
            {
              Effect = "Allow"
              Action = ["s3:GetObject", "s3:ListBucket"]
              Resource = [
                module.s3.bucket_arns["rag_source"],
                "${module.s3.bucket_arns["rag_source"]}/*"
              ]
            }
          ]
        })
        secrets = jsonencode({
          Version = "2012-10-17"
          Statement = [
            {
              Effect = "Allow"
              Action = [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
              ]
              Resource = [
                module.secrets.bedrock_config_secret_arn,
                module.secrets.app_secrets_secret_arn
              ]
            }
          ]
        })
      }
    }

    simulation-service = {
      namespace       = "default"
      service_account = "simulation-service"
      inline_policies = {
        s3_artifact = jsonencode({
          Version = "2012-10-17"
          Statement = [
            {
              Effect = "Allow"
              Action = [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
              ]
              Resource = [
                module.s3.bucket_arns["artifact"],
                "${module.s3.bucket_arns["artifact"]}/*"
              ]
            }
          ]
        })
      }
    }

    report-service = {
      namespace       = "default"
      service_account = "report-service"
      inline_policies = {
        s3_reports = jsonencode({
          Version = "2012-10-17"
          Statement = [
            {
              Effect   = "Allow"
              Action   = ["s3:PutObject", "s3:GetObject"]
              Resource = "${module.s3.bucket_arns["reports"]}/*"
            },
            {
              Effect   = "Allow"
              Action   = ["s3:GetObject", "s3:ListBucket"]
              Resource = [
                module.s3.bucket_arns["artifact"],
                "${module.s3.bucket_arns["artifact"]}/*"
              ]
            }
          ]
        })
      }
    }

    external-secrets = {
      namespace       = "external-secrets-system"
      service_account = "external-secrets"
      inline_policies = {
        secrets_read = jsonencode({
          Version = "2012-10-17"
          Statement = [
            {
              Effect = "Allow"
              Action = [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
              ]
              Resource = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}-${var.env}-*"
            }
          ]
        })
      }
    }

    aws-load-balancer-controller = {
      namespace       = "kube-system"
      service_account = "aws-load-balancer-controller"
      policy_arns     = [aws_iam_policy.alb_controller.arn]
    }
  }

  tags = local.common_tags
}
```

### 2. Helm values에서 사용

```yaml
# agent-service Helm values
serviceAccount:
  create: true
  name: agent-service
  annotations:
    eks.amazonaws.com/role-arn: ${module.irsa.role_arns["agent-service"]}

# 또는 Terraform output 활용
annotations: ${jsonencode(module.irsa.service_account_annotations["agent-service"])}
```

---

## 정책 예시

### Bedrock InvokeModel

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/*"
    }
  ]
}
```

### S3 읽기/쓰기

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::agent-t-dev-artifact/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::agent-t-dev-artifact"
    }
  ]
}
```

### Secrets Manager 읽기

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:agent-t-dev-*"
    }
  ]
}
```

---

## ALB Controller 정책

AWS Load Balancer Controller는 공식 IAM Policy 사용 권장:

1. 정책 다운로드:
   ```bash
   curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json
   ```

2. IAM Policy 생성:
   ```bash
   aws iam create-policy \
     --policy-name AWSLoadBalancerControllerIAMPolicy \
     --policy-document file://iam_policy.json
   ```

3. Terraform에서 참조:
   ```hcl
   data "aws_iam_policy" "alb_controller" {
     name = "AWSLoadBalancerControllerIAMPolicy"
   }

   service_accounts = {
     aws-load-balancer-controller = {
       namespace       = "kube-system"
       service_account = "aws-load-balancer-controller"
       policy_arns     = [data.aws_iam_policy.alb_controller.arn]
     }
   }
   ```

---

## 참고

- IRSA 문서: [`docs/eks.md`](../../../../docs/eks.md)
- Trust Policy는 모듈 내부에서 자동 생성
- `oidc_provider_url`은 `https://` 제거된 형태 (예: `oidc.eks.ap-northeast-2.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE`)
