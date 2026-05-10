# Terraform Module: Secrets Manager

AWS Secrets Manager 시크릿 메타데이터(컨테이너) 생성. 실제 비밀 값은 Terraform으로 관리하지 않는다.

---

## 책임

- Secrets Manager secret 메타데이터만 생성 (이름, KMS 키, 복구 기간)
- 실제 비밀 값은:
  - RDS/Redis 모듈이 `aws_secretsmanager_secret_version`으로 주입
  - 또는 운영자가 AWS CLI/Console로 수동 주입
- `terraform state`에 비밀 정보 노출 방지

---

## 생성되는 Secret 목록

| Secret 이름 | 용도 | 값 주입 방법 |
|---|---|---|
| `<project>-<env>-db-credentials` | RDS master credentials | RDS 모듈 (자동) |
| `<project>-<env>-redis-auth` | Redis AUTH token | Redis 모듈 (자동) |
| `<project>-<env>-app-secrets` | 애플리케이션 API 키, 토큰 | 운영자 (수동) |
| `<project>-<env>-bedrock-config` | Bedrock 모델 설정 | 운영자 (수동) |

---

## 입력 변수

| 변수 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `project_name` | string | ✅ | - | 프로젝트 식별자 |
| `env` | string | ✅ | - | 환경 (dev / prod) |
| `kms_key_arn` | string | | `""` | KMS Key ARN (빈 문자열이면 AWS 관리형 키) |
| `recovery_window_in_days` | number | | `30` | 삭제 후 복구 가능 기간 (7~30일) |
| `create_redis_auth_secret` | bool | | `true` | Redis AUTH secret 생성 여부 |
| `tags` | map(string) | | `{}` | 공통 태그 |

---

## 출력

| 출력 | 설명 |
|---|---|
| `db_credentials_secret_arn` | RDS 인증 정보 secret ARN |
| `db_credentials_secret_name` | RDS 인증 정보 secret 이름 |
| `app_secrets_secret_arn` | 애플리케이션 secret ARN |
| `app_secrets_secret_name` | 애플리케이션 secret 이름 |
| `bedrock_config_secret_arn` | Bedrock 설정 secret ARN |
| `bedrock_config_secret_name` | Bedrock 설정 secret 이름 |
| `redis_auth_secret_arn` | Redis AUTH secret ARN |
| `redis_auth_secret_name` | Redis AUTH secret 이름 |

---

## 사용 예시

```hcl
module "secrets" {
  source = "../../modules/secrets-manager"

  project_name = var.project_name
  env          = var.env

  kms_key_arn              = module.kms.key_arn  # 선택사항
  recovery_window_in_days  = 30
  create_redis_auth_secret = true

  tags = local.common_tags
}

# RDS 모듈에 secret ARN 전달
module "rds" {
  source = "../../modules/rds"
  # ...
  db_secret_arn = module.secrets.db_credentials_secret_arn
}

# Redis 모듈에 secret ARN 전달
module "redis" {
  source = "../../modules/redis"
  # ...
  auth_token_secret_arn = module.secrets.redis_auth_secret_arn
}
```

---

## 비밀 값 수동 주입 (app-secrets, bedrock-config)

### AWS CLI

```bash
aws secretsmanager put-secret-value \
  --secret-id agent-t-dev-app-secrets \
  --secret-string '{
    "openai_api_key": "sk-...",
    "slack_webhook_url": "https://hooks.slack.com/..."
  }'
```

### Python (boto3)

```python
import boto3
import json

client = boto3.client('secretsmanager', region_name='ap-northeast-2')
client.put_secret_value(
    SecretId='agent-t-dev-bedrock-config',
    SecretString=json.dumps({
        'region': 'us-east-1',
        'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'max_tokens': 4096
    })
)
```

---

## 참고

- 자세한 비밀 관리 방법: [`docs/secrets.md`](../../../../docs/secrets.md)
- IRSA 권한 설정: [`docs/infrastructure.md`](../../../../docs/infrastructure.md)
- Secret rotation: 추후 Lambda 함수로 구현 가능 (RDS는 AWS 제공 rotation 지원)
