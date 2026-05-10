# Terraform Module: RDS PostgreSQL

RDS PostgreSQL 인스턴스 + DB Subnet Group + Parameter Group + Security Group 생성.

---

## 책임

- RDS PostgreSQL 16.4 인스턴스 생성
- private-db subnet에 배치 (NAT 미경유)
- EKS에서만 접근 가능한 security group 생성
- master password 자동 생성 및 Secrets Manager 저장
- CloudWatch Logs 전송 (PostgreSQL, upgrade)
- Performance Insights 활성화

---

## 입력 변수

| 변수 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `project_name` | string | ✅ | - | 프로젝트 식별자 |
| `env` | string | ✅ | - | 환경 (dev / prod) |
| `vpc_id` | string | ✅ | - | VPC ID |
| `private_db_subnet_ids` | list(string) | ✅ | - | private DB subnet IDs (최소 2개) |
| `allowed_security_group_ids` | list(string) | | `[]` | 접근 허용할 SG IDs (EKS 노드 SG) |
| `allowed_cidr_blocks` | list(string) | | `[]` | 접근 허용할 CIDR 블록 |
| `instance_class` | string | ✅ | - | 인스턴스 타입 (예: `db.t4g.micro`) |
| `allocated_storage` | number | | `20` | 초기 스토리지 크기 (GB) |
| `max_allocated_storage` | number | | `100` | Auto-scaling 최대 크기 (GB) |
| `db_name` | string | | `agent_t` | 초기 DB 이름 |
| `master_username` | string | | `agent_t_admin` | 마스터 사용자 이름 |
| `multi_az` | bool | | `false` | Multi-AZ 배포 |
| `backup_retention_days` | number | | `7` | 백업 보존 기간 (일) |
| `deletion_protection` | bool | | `false` | 삭제 보호 |
| `skip_final_snapshot` | bool | | `true` | 삭제 시 최종 스냅샷 건너뛰기 |
| `db_secret_arn` | string | ✅ | - | Secrets Manager secret ARN (secrets-manager 모듈 출력) |
| `tags` | map(string) | | `{}` | 공통 태그 |

---

## 출력

| 출력 | 설명 |
|---|---|
| `db_endpoint` | RDS 엔드포인트 (host:port) |
| `db_address` | RDS 호스트 주소 |
| `db_port` | RDS 포트 (5432) |
| `db_name` | 데이터베이스 이름 |
| `db_instance_id` | RDS 인스턴스 ID |
| `db_instance_arn` | RDS 인스턴스 ARN |
| `db_security_group_id` | RDS security group ID |
| `db_secret_arn` | 인증 정보 저장된 secret ARN |
| `master_username` | 마스터 사용자 이름 (sensitive) |

---

## 사용 예시

```hcl
module "rds" {
  source = "../../modules/rds"

  project_name           = var.project_name
  env                    = var.env
  vpc_id                 = module.vpc.vpc_id
  private_db_subnet_ids  = module.vpc.private_db_subnet_ids
  
  allowed_security_group_ids = [module.eks.node_security_group_id]
  allowed_cidr_blocks        = ["10.10.1.0/24", "10.10.2.0/24"]

  instance_class        = var.rds_instance_class
  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  
  multi_az              = var.rds_multi_az
  backup_retention_days = var.rds_backup_retention_days
  deletion_protection   = var.rds_deletion_protection
  skip_final_snapshot   = var.rds_skip_final_snapshot

  db_secret_arn = module.secrets.db_credentials_secret_arn

  tags = local.common_tags
}
```

---

## 비밀번호 관리

1. **자동 생성**: `random_password` 리소스로 32자 생성
2. **자동 저장**: `aws_secretsmanager_secret_version` 리소스로 Secrets Manager에 주입
3. **애플리케이션 접근**: EKS Pod는 IRSA 권한으로 읽기

자세한 내용은 [`docs/secrets.md`](../../../../docs/secrets.md) 참조.

---

## 참고

- PostgreSQL 버전: 16.4
- Storage: gp3 (기본)
- Encryption: 저장 데이터 암호화 활성화
- Performance Insights: 7일 보존
