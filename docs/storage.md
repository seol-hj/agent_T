# Storage 및 데이터 계층

Agent T 프로젝트의 **S3, RDS PostgreSQL, Redis** 구성을 설명한다.

---

## 개요

| 종류 | 기술 | 용도 | 모듈 위치 |
|---|---|---|---|
| **Object Storage** | S3 | SUMO 산출물, RAG 문서, 리포트, 학습 데이터셋 | `infra/terraform/modules/s3/` |
| **관계형 DB** | RDS PostgreSQL | 실험 메타, 사용자 데이터, 트랜잭션 데이터 | `infra/terraform/modules/rds/` |
| **캐시/세션** | ElastiCache Redis | 세션 저장, KPI 캐시, Rate limiting | `infra/terraform/modules/redis/` |

---

# S3 버킷

S3 버킷 4 종의 목적, 경로 규칙, 보안/생명주기 정책. 변경 시 `infra/terraform/modules/s3/` 와 함께 수정.

## 버킷 목록

| 키 (Terraform 내부) | 실제 버킷 이름 | 용도 | 주 생산자 | 주 소비자 |
|---|---|---|---|---|
| `artifact`    | `<project>-<env>-artifact`    | SUMO 입출력 + 분석 KPI                  | simulation-service / analysis-service | analysis-service / report-service |
| `rag_source`  | `<project>-<env>-rag-source`  | RAG 문서 원본 (PDF/MD/사용자 업로드)    | api-service (업로드) / 운영자          | agent-service (검색·임베딩) |
| `reports`     | `<project>-<env>-reports`     | 정책 리포트 (MD / PDF / HTML + 차트)    | report-service                         | api-service / 사용자 (signed URL) |
| `model_data`  | `<project>-<env>-model-data`  | Fine-tuning / evaluation 데이터셋        | 운영자 / 별도 ETL 파이프라인           | 학습/평가 잡 |

> Terraform 내부 키는 underscore (`rag_source`, `model_data`), 실제 버킷 이름은 hyphen.
> 모듈이 `replace(key, "_", "-")` 로 변환한다.

## 표준 보안 정책 (모든 버킷 공통)

| 정책 | 설정 |
|---|---|
| **Public Access Block** | `block_public_acls / block_public_policy / ignore_public_acls / restrict_public_buckets` 모두 `true` |
| **Object Ownership**    | `BucketOwnerEnforced` (ACL 비활성, IAM 정책으로만 권한 제어) |
| **Versioning**          | `Enabled` (모든 버킷) |
| **Server-Side Encryption** | 기본 SSE-S3 (`AES256`). `kms_key_arn` 변수로 SSE-KMS 전환 가능 |
| **TLS-only**            | `aws:SecureTransport=false` 거부 정책. `enforce_tls=false` 로 옵트아웃 가능 (권장 X) |

## 경로 규칙

### `artifact` — SUMO 입출력 + KPI

```
s3://<project>-<env>-artifact/
  experiments/{experiment_id}/
    spec.json                              # ScenarioSpec 원본 (Scenario Builder 출력)
    scenarios/{scenario_id}/
      network/
        network.net.xml                    # Network Builder 출력
        osm.pbf                            # 원본 OSM 추출본 (재현용)
      demand/
        demand.rou.xml                     # Demand Builder 출력
        od_matrix.parquet                  # OD 행렬 원본
      simulation/
        sumo.cfg                           # SUMO 실행 설정
        run.log                            # 실행 로그
      raw/
        tripinfo.xml                       # SUMO trip 정보
        edge-stats.xml                     # SUMO edge 통계
        emissions.xml                      # 배출 정보 (옵션)
      kpi/
        kpi.parquet                        # Analyzer 산출 KPI 데이터셋
        kpi-summary.json                   # 요약 통계
      metadata.json                        # 모듈 간 인덱스 (artifact 위치, 타임스탬프)
```

### `rag_source` — RAG 문서 원본

```
s3://<project>-<env>-rag-source/
  curated/                                 # 관리자가 큐레이션한 신뢰 도큐먼트
    traffic-policy/{doc_id}.pdf
    sumo-docs/{doc_id}.md
    icd/{doc_id}.json                      # 도시별 도로 등급 정의 등
  uploads/{user_id}/                       # 사용자 업로드
    {upload_id}.{ext}
  ingest-meta/                             # 임베딩 인덱싱 진행 메타 (재실행 idempotent 키)
    {doc_id}.json
```

벡터 임베딩 자체는 별도 vector DB (pgvector / OpenSearch — 18단계에서 결정)에 저장. 본 버킷에는 **원본만**.

### `reports` — 정책 리포트

```
s3://<project>-<env>-reports/
  reports/{report_id}/
    {report_id}.md                         # Markdown 본문
    {report_id}.pdf                        # PDF 렌더 결과
    {report_id}.html                       # HTML 렌더 결과 (선택)
    assets/
      chart-{n}.png                        # 인라인 차트
      table-{n}.csv                        # 보조 테이블
  index/
    {experiment_id}.json                   # experiment → report 들의 인덱스
```

사용자 다운로드는 **사인된 URL** 발급 (default 1 시간). 리포트 자체에는 PII 가 들어갈 수 있어 공용 URL 절대 금지 (Public Access Block 으로 강제).

### `model_data` — Fine-tuning / Evaluation 데이터셋

```
s3://<project>-<env>-model-data/
  fine-tuning/
    datasets/{dataset_id}/
      train.jsonl
      val.jsonl
      meta.json
    runs/{run_id}/
      output/                              # 학습 산출물 (체크포인트 등)
      eval-metrics.json
  evaluation/
    benchmarks/{benchmark_id}/
      cases.jsonl                          # 평가 케이스
      ground-truth.json
    runs/{run_id}/
      predictions.jsonl
      score.json
```

본 단계 시점에는 fine-tuning 파이프라인이 없다. 18단계(RAG/모델 확장) 진입 전까지는 비어 있어도 정상.

## 명명 규약

- 버킷 이름: `<project>-<env>-<purpose>` (purpose 는 hyphen)
  - 예: `agent-t-dev-artifact`, `agent-t-prod-rag-source`
- S3 객체 키:
  - 소문자 + hyphen 권장 (대문자/언더스코어 가급적 회피)
  - ID 는 ULID 권장 (시간순 정렬 + 충돌 방지)
  - 디렉토리 prefix 끝에 `/` 명시

## 생명주기 정책 (env 별)

`var.s3_lifecycle_rules` (env tfvars) 로 버킷별 정책 제어. 키는 버킷 키와 동일 (underscore).

### dev 기본값 (`tfvars.example`)

```hcl
s3_lifecycle_rules = {
  artifact = {
    enabled                            = true
    expiration_days                    = 30   # 현재 객체 30일 후 삭제
    noncurrent_version_expiration_days = 30   # 과거 버전도 30일 후 삭제
  }
}
```

→ dev 의 SUMO 산출물은 30일 후 자동 정리. 그 외 버킷은 보존.

### prod 기본값 (`tfvars.example`)

```hcl
s3_lifecycle_rules = {
  artifact = {
    enabled                            = true
    noncurrent_version_expiration_days = 90    # 현재 객체는 보존, 과거 버전만 정리
  }
  reports = {
    enabled                            = true
    noncurrent_version_expiration_days = 365   # 리포트 과거 버전 1 년 보존
  }
}
```

→ 사용자 데이터 손실 위험 차단을 위해 **현재 객체는 자동 만료시키지 않는다**. 과거 버전만 비용 통제.

## IAM 권한 매핑 (5단계 IRSA 에서 활용)

| 서비스 | 버킷 | 필요 권한 |
|---|---|---|
| simulation-service  | `artifact`            | `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` |
| analysis-service    | `artifact`            | `s3:GetObject`, `s3:PutObject` (KPI 쓰기), `s3:ListBucket` |
| report-service      | `reports` (write), `artifact` (read), `model_data` (read 평가용) | 각 버킷별 부분 권한 |
| agent-service       | `rag_source` (read), `artifact` (read) | 임베딩 ingest / 검색 |
| api-service         | `rag_source` (write — 업로드), `reports` (read — signed URL 발급) | |

5단계의 `iam-irsa` 모듈에서 위 매트릭스를 IAM Policy Document 로 구체화한다.

## 운영 노트

- **버킷 이름 글로벌 충돌**: S3 이름은 전역 유니크. `agent-t-...` prefix 가 누군가 선점되어 있으면 apply 실패. 그 경우 `project_name` 을 변경하거나 향후 모듈 입력으로 suffix 추가.
- **삭제 보호**: prod 의 stateful 리소스 삭제 보호는 EKS/RDS 위주. S3 는 default 가 빈 버킷일 때만 삭제 허용 — 본 모듈은 `lifecycle { prevent_destroy }` 미설정. 필요 시 prod 만 추후 추가 ADR.
- **CORS / Notification / Replication**: 본 단계 미설정. 사용 사례 발생 시 별도 인풋으로 노출.

---

# RDS PostgreSQL

## 개요

**PostgreSQL 16.4** 기반 관계형 DB. 실험 메타데이터, 사용자 정보, 트랜잭션 데이터를 저장한다.

## 아키텍처

- **배치 위치**: VPC private-db subnet (intra subnet — NAT 미경유)
- **접근 제어**: EKS private-app subnet 또는 EKS 노드 security group에서만 접근 가능
- **암호화**: 저장 데이터 암호화 (storage_encrypted=true), 전송 중 암호화 (TLS)
- **백업**: 자동 백업 활성화 (dev: 7일, prod: 30일 보존)
- **Multi-AZ**: prod는 Multi-AZ on (HA), dev는 Single-AZ (비용 절감)

## 인스턴스 크기 (env별)

| 환경 | 인스턴스 타입 | 스토리지 | Multi-AZ | 백업 보존 | 삭제 보호 |
|---|---|---|---|---|---|
| **dev** | `db.t4g.micro` | 20GB (최대 100GB auto-scale) | off | 7일 | off |
| **prod** | `db.r7g.large` | 100GB (최대 500GB auto-scale) | on | 30일 | on |

## 비밀번호 관리

1. **자동 생성**: Terraform `random_password` 리소스로 32자 랜덤 생성
2. **자동 저장**: RDS 모듈이 Secrets Manager에 인증 정보 저장
   ```json
   {
     "username": "agent_t_admin",
     "password": "<random-32-chars>",
     "engine": "postgres",
     "host": "<rds-endpoint>",
     "port": 5432,
     "dbname": "agent_t"
   }
   ```
3. **애플리케이션 접근**: EKS Pod는 IRSA 권한으로 Secrets Manager에서 읽기

자세한 내용은 [`docs/secrets.md`](./secrets.md) 참조.

## 데이터베이스 스키마 (예상)

| 테이블 | 용도 |
|---|---|
| `users` | 사용자 계정 정보 |
| `experiments` | 실험 메타데이터 (ID, 생성 시각, 소유자, 상태) |
| `scenarios` | 시나리오 정보 (experiment_id, spec, 실행 결과 참조) |
| `kpi_summaries` | KPI 요약 통계 (빠른 조회용 — 상세 데이터는 S3) |
| `reports` | 리포트 메타데이터 (report_id, S3 경로, 생성 시각) |

실제 스키마는 서비스 구현 단계(8~17단계)에서 정의된다.

## 성능 튜닝

RDS 모듈은 기본 parameter group을 생성하며, 다음 파라미터를 설정한다:

- `shared_preload_libraries = pg_stat_statements` — 쿼리 성능 모니터링
- `log_statement = all` (dev) / `ddl` or `mod` (prod 권장)
- `log_min_duration_statement = 1000` — 1초 이상 쿼리 로깅

추가 튜닝이 필요하면 `infra/terraform/modules/rds/main.tf`의 parameter group을 수정한다.

## 모니터링

- **CloudWatch Logs**: PostgreSQL 로그, 업그레이드 로그 자동 전송
- **Performance Insights**: 활성화 (7일 보존)
- **Enhanced Monitoring**: 필요 시 활성화 (추후 변수 추가)

## 접근 방법

### Bastion 호스트 (미구현)

현재는 bastion 호스트가 없다. RDS는 private subnet에만 있으므로 직접 접근 불가.

접근 방법:
1. **EKS Pod에서 psql 실행**:
   ```bash
   kubectl run -it --rm psql-client --image=postgres:16 --restart=Never -- bash
   # Pod 내부에서
   psql -h <rds-endpoint> -U agent_t_admin -d agent_t
   ```

2. **SSM Session Manager + Port Forwarding** (추후 구현):
   EKS 노드에 SSM Agent 설치 후 포트 포워딩.

3. **VPN / Direct Connect** (prod 권장):
   회사 VPN 통해 private subnet 접근.

---

# Redis (ElastiCache)

## 개요

**Redis 7.1** 기반 인메모리 캐시. 세션 저장, KPI 캐시, Rate limiting, 분산 락 등에 사용한다.

## 아키텍처

- **배치 위치**: VPC private-db subnet (intra subnet — NAT 미경유)
- **접근 제어**: EKS private-app subnet 또는 EKS 노드 security group에서만 접근 가능
- **암호화**: 저장 데이터 암호화 (at-rest), 전송 중 암호화 (TLS)
- **AUTH Token**: 활성화 (Secrets Manager에 저장)
- **Replication**: prod는 replica + automatic failover, dev는 single node

## 클러스터 크기 (env별)

| 환경 | 노드 타입 | 노드 수 | Multi-AZ | Failover | 스냅샷 보존 |
|---|---|---|---|---|---|
| **dev** | `cache.t4g.micro` | 1 (single) | off | off | 5일 |
| **prod** | `cache.r7g.large` | 2 (primary + replica) | on | on | 30일 |

## AUTH Token 관리

1. **자동 생성**: Terraform `random_password` 리소스로 64자 랜덤 생성 (영숫자만)
2. **자동 저장**: Redis 모듈이 Secrets Manager에 AUTH token 저장
   ```json
   {
     "auth_token": "<random-64-chars>",
     "host": "<redis-endpoint>",
     "port": 6379
   }
   ```
3. **애플리케이션 접근**: EKS Pod는 IRSA 권한으로 Secrets Manager에서 읽기

자세한 내용은 [`docs/secrets.md`](./secrets.md) 참조.

## 사용 사례

| 서비스 | 용도 | 키 패턴 |
|---|---|---|
| api-service | 사용자 세션 저장 | `session:<session_id>` |
| agent-service | LLM 응답 캐시 | `llm_cache:<prompt_hash>` |
| analysis-service | KPI 계산 결과 캐시 | `kpi:<experiment_id>:<scenario_id>` |
| 전체 | Rate limiting | `rate_limit:<user_id>:<endpoint>` |
| simulation-service | 분산 락 (동일 실험 중복 실행 방지) | `lock:experiment:<experiment_id>` |

## 접속 예시 (Python)

```python
import boto3
import json
import redis

# Secrets Manager에서 AUTH token 가져오기
client = boto3.client('secretsmanager', region_name='ap-northeast-2')
response = client.get_secret_value(SecretId='agent-t-dev-redis-auth')
secret = json.loads(response['SecretString'])

# Redis 연결 (TLS + AUTH)
r = redis.StrictRedis(
    host=secret['host'],
    port=secret['port'],
    password=secret['auth_token'],
    ssl=True,
    ssl_cert_reqs='required',
    decode_responses=True
)

# 테스트
r.set('hello', 'world')
print(r.get('hello'))  # 'world'
```

## 모니터링

- **CloudWatch Logs**: slow-log, engine-log 자동 전송 (7일 보존)
- **CloudWatch Metrics**: 
  - `CPUUtilization`
  - `DatabaseMemoryUsagePercentage`
  - `CurrConnections`
  - `Evictions` (메모리 부족 시 키 삭제 발생)
- **Parameter Group**: `maxmemory-policy = allkeys-lru` (LRU 캐시 정책)

## 고가용성 (prod)

- **Multi-AZ**: primary와 replica를 다른 AZ에 배치
- **Automatic Failover**: primary 장애 시 자동으로 replica 승격
- **Read Replica**: 읽기 부하 분산 (reader endpoint 사용)

dev 환경은 single node로 HA 없음 (비용 절감).

---

# 데이터 흐름 예시

```
사용자 요청 (자연어 시뮬레이션 요구)
        │
        ▼
  ┌─────────────┐
  │ api-service │ ── (세션 저장) ──▶ Redis
  └─────┬───────┘
        │
        ▼
  ┌─────────────┐
  │agent-service│ ── (실험 메타 저장) ──▶ RDS
  └─────┬───────┘    ── (RAG 문서 읽기) ──▶ S3 (rag_source)
        │
        ▼
  ┌────────────────────┐
  │simulation-service  │ ── (SUMO 산출물 저장) ──▶ S3 (artifact)
  └────────┬───────────┘
           │
           ▼
  ┌────────────────┐
  │analysis-service│ ── (KPI 읽기) ──▶ S3 (artifact)
  └────────┬───────┘    ── (KPI 요약 저장) ──▶ RDS
           │            ── (KPI 캐시) ──▶ Redis
           ▼
  ┌────────────┐
  │report-service│ ── (리포트 저장) ──▶ S3 (reports)
  └─────┬──────┘    ── (리포트 메타 저장) ──▶ RDS
        │
        ▼
  사용자에게 리포트 signed URL 반환
```

---

# 비용 추정 (ap-northeast-2 기준)

| 리소스 | dev (월) | prod (월) |
|---|---|---|
| **S3** | ~$5 (100GB) | ~$50 (1TB) |
| **RDS** | ~$15 (db.t4g.micro) | ~$300 (db.r7g.large Multi-AZ) |
| **Redis** | ~$12 (cache.t4g.micro) | ~$200 (cache.r7g.large × 2) |
| **합계** | **~$32** | **~$550** |

※ 실제 비용은 데이터 전송량, 백업 스토리지, IOPS 등에 따라 변동.

---

# 참고 문서

- [S3 버킷 상세](./storage.md) (본 문서 상단)
- [Secrets 관리](./secrets.md)
- [VPC 및 Subnet 설계](./networking.md)
- [VPC Endpoints](./vpc-endpoints.md)
