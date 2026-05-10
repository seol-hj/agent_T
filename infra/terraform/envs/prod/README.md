# envs/prod

운영 환경 진입점. 2단계에서 구체화.

## 의도된 구성 (예정)

- VPC: 단일 리전, 3 AZ
- EKS: 워크로드별 노드그룹 분리 (general / sumo-compute)
- RDS: db.r7g 계열, Multi-AZ on, 자동 백업 30일
- Redis: replication group, Multi-AZ on
- 삭제 보호: 모든 stateful 리소스 on
- 모니터링/알람: CloudWatch + (선택) Managed Prometheus

## 변수 파일

- `terraform.tfvars` (커밋 금지)
- `terraform.tfvars.example` (커밋)
