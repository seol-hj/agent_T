# Secrets 관리

이 문서는 Agent T 프로젝트의 비밀 정보(credentials, API keys, tokens) 관리 방법을 설명한다.

---

## 원칙

1. **Git에 비밀 정보를 커밋하지 않는다.**
   - `.env`, `terraform.tfvars`, 하드코딩된 비밀번호 등 모두 금지.
   - `.gitignore`에 반드시 포함.

2. **AWS Secrets Manager를 사용한다.**
   - 모든 런타임 비밀 정보는 Secrets Manager에 저장.
   - EKS Pod는 IRSA (IAM Role for Service Account)로 비밀 정보 읽기 권한 부여.

3. **Terraform은 비밀 "값"을 관리하지 않는다.**
   - Terraform은 Secret 메타데이터(이름, KMS 키, 정책)만 생성.
   - 실제 값은 RDS/Redis 모듈이 자동 생성하거나, 운영자가 수동으로 주입.
   - `terraform state`에 비밀 정보 노출 방지.

4. **환경별 분리.**
   - dev / prod 환경은 별도의 Secrets Manager secret 사용.
   - Secret 이름: `<project>-<env>-<purpose>` (예: `agent-t-dev-db-credentials`).

---

## Secrets Manager Secret 목록

| Secret 이름 | 용도 | 값 주입 방법 | 접근 주체 |
|---|---|---|---|
| `agent-t-<env>-db-credentials` | RDS PostgreSQL master credentials | RDS 모듈 (random_password) | 모든 서비스 Pod (read-only) |
| `agent-t-<env>-redis-auth` | Redis AUTH token | Redis 모듈 (random_password) | 모든 서비스 Pod (read-only) |
| `agent-t-<env>-app-secrets` | 애플리케이션 API 키, 토큰 | 운영자 수동 주입 | 특정 서비스 Pod |
| `agent-t-<env>-bedrock-config` | Bedrock 모델 설정, 엔드포인트 | 운영자 수동 주입 | LLM Gateway Pod |

---

## RDS 비밀번호 관리

### 1. Terraform 실행 시 자동 생성

RDS 모듈(`infra/terraform/modules/rds`)은 `random_password` 리소스로 master password를 생성한다.

```hcl
resource "random_password" "master" {
  length  = 32
  special = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}
```

### 2. Secrets Manager에 자동 저장

RDS 인스턴스 생성 후, `aws_secretsmanager_secret_version` 리소스로 인증 정보를 Secrets Manager에 주입한다.

```hcl
resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = var.db_secret_arn

  secret_string = jsonencode({
    username = var.master_username
    password = random_password.master.result
    engine   = "postgres"
    host     = aws_db_instance.this.address
    port     = aws_db_instance.this.port
    dbname   = var.db_name
  })
}
```

### 3. 애플리케이션에서 읽기

EKS Pod는 IRSA 권한으로 Secrets Manager에서 값을 읽는다.

```python
import boto3
import json

client = boto3.client('secretsmanager', region_name='ap-northeast-2')
response = client.get_secret_value(SecretId='agent-t-dev-db-credentials')
secret = json.loads(response['SecretString'])

# DB 연결
host = secret['host']
port = secret['port']
user = secret['username']
password = secret['password']
dbname = secret['dbname']
```

또는 환경 변수로 주입 (Helm values):

```yaml
env:
  - name: DB_SECRET_ARN
    value: "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:agent-t-dev-db-credentials"
```

---

## Redis AUTH Token 관리

### 1. Terraform 실행 시 자동 생성

Redis 모듈(`infra/terraform/modules/redis`)은 `random_password` 리소스로 AUTH token을 생성한다.

```hcl
resource "random_password" "auth_token" {
  count = var.auth_token_enabled ? 1 : 0

  length  = 64
  special = false # Redis AUTH token은 영숫자만 허용
}
```

### 2. Secrets Manager에 자동 저장

Redis replication group 생성 후, AUTH token을 Secrets Manager에 주입한다.

```hcl
resource "aws_secretsmanager_secret_version" "redis_auth" {
  count = var.auth_token_enabled && var.auth_token_secret_arn != "" ? 1 : 0

  secret_id = var.auth_token_secret_arn

  secret_string = jsonencode({
    auth_token = random_password.auth_token[0].result
    host       = aws_elasticache_replication_group.this.configuration_endpoint_address
    port       = aws_elasticache_replication_group.this.port
  })
}
```

### 3. 애플리케이션에서 읽기

```python
import boto3
import json
import redis

client = boto3.client('secretsmanager', region_name='ap-northeast-2')
response = client.get_secret_value(SecretId='agent-t-dev-redis-auth')
secret = json.loads(response['SecretString'])

# Redis 연결 (TLS + AUTH)
r = redis.StrictRedis(
    host=secret['host'],
    port=secret['port'],
    password=secret['auth_token'],
    ssl=True,
    decode_responses=True
)
```

---

## 애플리케이션 비밀 정보 (app-secrets)

외부 API 키, OAuth 토큰 등 애플리케이션이 사용하는 비밀 정보는 **운영자가 수동으로 주입**한다.

### 1. Secret 구조 (예시)

```json
{
  "openai_api_key": "sk-...",
  "slack_webhook_url": "https://hooks.slack.com/...",
  "github_token": "ghp_..."
}
```

### 2. 주입 방법

#### AWS CLI

```bash
aws secretsmanager put-secret-value \
  --secret-id agent-t-dev-app-secrets \
  --secret-string '{
    "openai_api_key": "sk-...",
    "slack_webhook_url": "https://hooks.slack.com/...",
    "github_token": "ghp_..."
  }'
```

#### AWS Console

1. AWS Console → Secrets Manager
2. `agent-t-dev-app-secrets` 선택
3. "Retrieve secret value" → "Edit"
4. JSON 형식으로 값 입력
5. "Save"

### 3. 애플리케이션에서 읽기

```python
import boto3
import json

client = boto3.client('secretsmanager', region_name='ap-northeast-2')
response = client.get_secret_value(SecretId='agent-t-dev-app-secrets')
secrets = json.loads(response['SecretString'])

openai_api_key = secrets['openai_api_key']
slack_webhook_url = secrets['slack_webhook_url']
```

---

## Bedrock 설정 (bedrock-config)

LLM Gateway가 Bedrock 모델을 호출하기 위한 설정 정보를 저장한다.

### 1. Secret 구조 (예시)

```json
{
  "region": "us-east-1",
  "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
  "max_tokens": 4096,
  "temperature": 0.7
}
```

### 2. 주입 방법

```bash
aws secretsmanager put-secret-value \
  --secret-id agent-t-dev-bedrock-config \
  --secret-string '{
    "region": "us-east-1",
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "max_tokens": 4096,
    "temperature": 0.7
  }'
```

### 3. LLM Gateway에서 읽기

```python
import boto3
import json

client = boto3.client('secretsmanager', region_name='ap-northeast-2')
response = client.get_secret_value(SecretId='agent-t-dev-bedrock-config')
config = json.loads(response['SecretString'])

bedrock_region = config['region']
model_id = config['model_id']
```

---

## IRSA 권한 부여

EKS Pod가 Secrets Manager에 접근하려면 **IRSA (IAM Role for Service Account)** 권한이 필요하다.

### 1. IAM Policy (예시)

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
      "Resource": [
        "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:agent-t-dev-db-credentials-*",
        "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:agent-t-dev-redis-auth-*",
        "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:agent-t-dev-app-secrets-*"
      ]
    }
  ]
}
```

### 2. ServiceAccount 생성 (Terraform)

`iam-irsa` 모듈에서 생성:

```hcl
module "irsa_api_service" {
  source = "../../modules/iam-irsa"

  project_name       = var.project_name
  env                = var.env
  service_name       = "api-service"
  cluster_oidc_issuer = module.eks.cluster_oidc_issuer
  policy_arns        = [
    aws_iam_policy.secrets_read.arn
  ]
}
```

### 3. Pod에서 ServiceAccount 사용 (Helm)

```yaml
serviceAccount:
  create: false
  name: api-service
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/agent-t-dev-api-service
```

---

## 로컬 개발 환경

로컬 개발 시 AWS 인증 정보가 있으면 Secrets Manager에서 직접 읽을 수 있다.

### 1. AWS CLI 인증 설정

```bash
aws configure --profile agent-t-dev
```

### 2. 환경 변수 설정

```bash
export AWS_PROFILE=agent-t-dev
export AWS_REGION=ap-northeast-2
export DB_SECRET_ARN=agent-t-dev-db-credentials
```

### 3. 애플리케이션 실행

Python 애플리케이션은 boto3가 자동으로 AWS 인증 정보를 찾아 Secrets Manager에 접근한다.

---

## 보안 체크리스트

- [ ] `.gitignore`에 `.env`, `*.tfvars` 추가 확인
- [ ] Terraform state를 S3 backend + 암호화로 관리 (state에 비밀번호 포함될 수 있음)
- [ ] Secrets Manager의 KMS 키는 환경별로 분리
- [ ] IRSA 정책은 최소 권한 원칙 (Least Privilege) 적용
- [ ] 로그에 비밀 정보 출력 금지 (masking 필요)
- [ ] Secret rotation 정책 고려 (RDS는 Lambda로 자동 rotation 가능)

---

## 참고

- [AWS Secrets Manager 문서](https://docs.aws.amazon.com/secretsmanager/)
- [EKS IRSA 문서](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [RDS Password Rotation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets-rds.html)
