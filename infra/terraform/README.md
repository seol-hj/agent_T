# infra/terraform

AWS 리소스의 **유일한 정의 위치**. 콘솔/CLI로 만든 리소스는 곧 드리프트가 된다.

## 구조

```
terraform/
├── envs/
│   ├── dev/        # 개발 환경 (작은 인스턴스, 단일 AZ 옵션)
│   └── prod/       # 운영 환경 (다중 AZ, 백업 활성)
└── modules/        # 재사용 가능한 컴포지션 단위
```

- **`envs/<env>/`**: 환경별 진입점. `terraform init/plan/apply`를 여기서 실행.
- **`modules/`**: VPC, EKS, ALB Controller, RDS, Redis, S3 등 재사용 모듈.

## 원칙

- **State는 원격(S3 + DynamoDB lock)** — 로컬 state 금지. 부트스트랩 스크립트로 초기 backend 생성.
- **환경별 변수 파일**: `envs/<env>/terraform.tfvars` (시크릿은 절대 커밋 금지 — Secrets Manager 참조)
- **모듈은 안정 버전 핀** — community 모듈은 `~> x.y` 또는 정확한 태그
- **`.terraform.lock.hcl`은 커밋**

## 환경별 핵심 차이 (추후 명시)

| 항목 | dev | prod |
|---|---|---|
| AZ | 2개   | 3개  |
| 인스턴스 크기 | 작게 | 표준 |
| RDS Multi-AZ | off  | on   |
| 백업 보관기간 | 7일  | 30일 |
| 삭제 보호 | off  | on   |

## 실행 (placeholder, 2단계에서 구체화)

```bash
cd infra/terraform/envs/dev
terraform init
terraform plan -out=plan.out
terraform apply plan.out
```
