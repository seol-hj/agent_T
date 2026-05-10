# Terraform Module: Redis (ElastiCache)

ElastiCache Redis Replication Group + Subnet Group + Parameter Group + Security Group 생성.

---

## 책임

- Redis 7.1 replication group 생성
- private-db subnet에 배치 (NAT 미경유)
- EKS에서만 접근 가능한 security group 생성
- AUTH token 자동 생성 및 Secrets Manager 저장
- 전송 중 + 저장 데이터 암호화 활성화
- CloudWatch Logs 전송 (slow-log, engine-log)

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
| `node_type` | string | ✅ | - | 노드 타입 (예: `cache.t4g.micro`) |
| `num_cache_clusters` | number | | `1` | 캐시 클러스터 수 (1=single, 2+=replica) |
| `multi_az_enabled` | bool | | `false` | Multi-AZ 배포 |
| `automatic_failover_enabled` | bool | | `false` | 자동 failover (num_cache_clusters>=2 필요) |
| `at_rest_encryption_enabled` | bool | | `true` | 저장 데이터 암호화 |
| `transit_encryption_enabled` | bool | | `true` | 전송 중 암호화 (TLS) |
| `auth_token_enabled` | bool | | `true` | AUTH token 활성화 |
| `auth_token_secret_arn` | string | | `""` | AUTH token 저장할 secret ARN |
| `snapshot_retention_limit` | number | | `5` | 스냅샷 보존 기간 (일) |
| `snapshot_window` | string | | `"03:00-05:00"` | 스냅샷 시간대 (UTC) |
| `maintenance_window` | string | | `"mon:05:00-mon:07:00"` | 유지보수 시간대 (UTC) |
| `tags` | map(string) | | `{}` | 공통 태그 |

---

## 출력

| 출력 | 설명 |
|---|---|
| `redis_endpoint` | Redis configuration/primary endpoint |
| `redis_primary_endpoint` | Primary endpoint address |
| `redis_reader_endpoint` | Reader endpoint address (replica 있을 때) |
| `redis_port` | Redis 포트 (6379) |
| `redis_security_group_id` | Redis security group ID |
| `redis_auth_secret_arn` | AUTH token 저장된 secret ARN |
| `replication_group_id` | Replication group ID |
| `replication_group_arn` | Replication group ARN |

---

## 사용 예시

```hcl
module "redis" {
  source = "../../modules/redis"

  project_name           = var.project_name
  env                    = var.env
  vpc_id                 = module.vpc.vpc_id
  private_db_subnet_ids  = module.vpc.private_db_subnet_ids
  
  allowed_security_group_ids = [module.eks.node_security_group_id]
  allowed_cidr_blocks        = ["10.10.1.0/24", "10.10.2.0/24"]

  node_type              = var.redis_node_type
  num_cache_clusters     = var.redis_num_cache_clusters
  multi_az_enabled       = var.redis_multi_az_enabled
  automatic_failover_enabled = var.redis_automatic_failover_enabled
  
  snapshot_retention_limit = var.redis_snapshot_retention_limit

  auth_token_enabled     = true
  auth_token_secret_arn  = module.secrets.redis_auth_secret_arn

  tags = local.common_tags
}
```

---

## AUTH Token 관리

1. **자동 생성**: `random_password` 리소스로 64자 생성 (영숫자만)
2. **자동 저장**: `aws_secretsmanager_secret_version` 리소스로 Secrets Manager에 주입
3. **애플리케이션 접근**: EKS Pod는 IRSA 권한으로 읽기

자세한 내용은 [`docs/secrets.md`](../../../../docs/secrets.md) 참조.

---

## 고가용성 (prod)

- `num_cache_clusters = 2` (primary + replica)
- `multi_az_enabled = true` (다른 AZ에 배치)
- `automatic_failover_enabled = true` (primary 장애 시 자동 승격)

---

## 참고

- Redis 버전: 7.1
- Parameter Group: `maxmemory-policy = allkeys-lru`
- CloudWatch Logs: slow-log, engine-log (7일 보존)
