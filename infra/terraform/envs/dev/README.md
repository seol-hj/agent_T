# envs/dev

개발 환경 진입점. 2단계에서 구체화.

## 의도된 구성 (예정)

- VPC: 단일 리전, 2 AZ
- EKS: 작은 노드그룹 (예: t3.medium x 2)
- RDS: db.t4g.micro, Multi-AZ off
- Redis: cache.t4g.micro, single node
- ALB Controller, External DNS, Argo CD, Cluster Autoscaler 설치

## 변수 파일

- `terraform.tfvars` (커밋 금지)
- `terraform.tfvars.example` (커밋 — 템플릿 용도)
