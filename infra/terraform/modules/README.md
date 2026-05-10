# modules

재사용 가능한 Terraform 모듈. 본 단계(2)에서 skeleton 으로 12개 모듈이 자리잡았으며,
실제 리소스 정의는 후속 단계에서 채워진다.

## 모듈 목록

| 모듈 | 책임 | 활성화 단계 |
|---|---|---|
| `vpc`              | VPC, public/private/intra subnet, NAT, route table | 3 |
| `vpc-endpoints`    | S3, ECR(api/dkr), STS, Secrets Manager, Logs, Bedrock 등 PrivateLink | 3 |
| `ecr`              | 서비스별 ECR 리포지토리 (image scan, immutable tag) | 4 |
| `s3`               | 표준 정책(SSE, public block, versioning) 적용된 버킷 | 4 |
| `rds`              | RDS PostgreSQL + 서브넷그룹 + 파라미터그룹 + SG | 4 |
| `redis`            | ElastiCache Redis (replication group) + SG | 4 |
| `secrets-manager`  | Secrets Manager 컨테이너 (값은 외부에서 주입) | 4 |
| `bedrock`          | Bedrock InvokeModel IAM 정책 / Logging | 4 |
| `eks`              | EKS 클러스터 + Managed Node Group + OIDC provider | 5 |
| `iam-irsa`         | 서비스별 IRSA(IAM Role for Service Account) 일괄 생성 | 5 |
| `alb-controller`   | AWS Load Balancer Controller 설치 + IRSA + IAM Policy | 5 |
| `argocd`           | Argo CD Helm release + 초기 AppProject | 5 |

## 작성 원칙

- **입력 변수는 명시 타입과 description 필수**
- 출력은 다른 모듈/루트에서 참조 가능한 안정적 키만 노출
- 모듈은 자체 `main.tf` + `variables.tf` + `outputs.tf` 분리
- **모듈에서 직접 provider 선언 금지** — 루트(envs/<env>/providers.tf)에서 주입
- **모듈은 자체적으로 default_tags 를 만들지 않음** — 루트 provider 에 위임

## 모듈 간 의존 관계

```
vpc ─┬─▶ vpc-endpoints
     ├─▶ eks ─┬─▶ iam-irsa
     │       ├─▶ alb-controller
     │       └─▶ argocd
     ├─▶ rds
     └─▶ redis

(독립) ecr / s3 / secrets-manager / bedrock
```

루트의 `main.tf` 에서 cross-module 인풋(vpc_id, oidc_provider_arn 등)이 채워지는 시점은
각 모듈의 본 구현 단계와 동일하다 (3·4·5).
