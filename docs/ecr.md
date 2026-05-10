# ECR

컨테이너 이미지 레포지토리. 변경 시 `infra/terraform/modules/ecr/` 와 함께 수정.

## 레포지토리 목록

| 레포 키 | 전체 이름 | 용도 |
|---|---|---|
| `frontend`              | `<project>-<env>/frontend`              | 사용자 UI |
| `api-service`           | `<project>-<env>/api-service`           | 외부 진입 API |
| `agent-service`         | `<project>-<env>/agent-service`         | Orchestrator + Scenario Builder (LLM 호출) |
| `simulation-service`    | `<project>-<env>/simulation-service`    | Network/Demand Builder + SUMO Runner 컨트롤 |
| `analysis-service`      | `<project>-<env>/analysis-service`      | KPI 분석 |
| `report-service`        | `<project>-<env>/report-service`        | 정책 리포트 생성 |
| `simulation-runner`     | `<project>-<env>/simulation-runner`     | **SUMO 실행 컨테이너** — `simulation-service` 가 K8s Job 으로 띄우는 워커 이미지 |

> `simulation-runner` 는 `apps/*` 마이크로서비스가 아니라 **운영 실행 이미지**다.
> `simulation-service` 가 시뮬레이션 1 회당 Job/Pod 으로 띄우는 패턴을 가정한 분리 (비용 격리 + SUMO 버전 핀 + 노드그룹 분리 가능).

## 이미지 태그 전략 (강제 규칙)

| 태그 | 용도 | 생성 주체 | 예 |
|---|---|---|---|
| `sha-<git-short-sha>` | CI 가 메인 브랜치 빌드마다 자동 부여 | GitHub Actions (6단계) | `sha-abc1234` |
| `v<semver>`           | 릴리즈 시 명시적으로 부여        | 운영자 / 릴리즈 워크플로우 | `v1.4.0`, `v1.4.0-rc1` |

**금지**:
- `latest` — 어느 환경에서도 사용 금지. Helm values, Argo CD, 문서 어디에도 표기하지 않는다.
- `dev` / `prod` — 환경 식별은 레포 namespace 가 한다. 태그에 환경을 넣지 않는다.
- `master` / `main` — 브랜치명 태그 금지 (재현 불가).

### 태그 형식 정의

```
sha tag    : ^sha-[0-9a-f]{7,40}$
release tag: ^v\d+\.\d+\.\d+(-[a-z0-9.]+)?$
```

CI 는 git short SHA(7 자) + `sha-` prefix 로 통일. 예: `git rev-parse --short=7 HEAD` → `abc1234` → 태그 `sha-abc1234`.

## 라이프사이클 정책

모듈이 모든 레포에 동일한 2-rule 정책을 자동 적용한다.

| Rule | 대상 | 액션 | 기본값 |
|---|---|---|---|
| 1 | `untagged` 이미지            | `untagged_image_expiration_days` 후 expire | 14 일 |
| 2 | `tag_prefix_filters` 매칭 태그 | 최근 `tagged_image_retention_count` 개만 유지 | 30 개, prefix `["sha-"]` |

**의도**:
- 빌드 실패/중단으로 남은 untagged 레이어 정리 → 비용 절감
- `sha-*` 태그는 잦은 빌드로 누적되므로 최근 30 개만 유지 (롤백 윈도우 충분)
- `v*` 릴리즈 태그는 prefix 필터에서 빠져 **영구 보존**

### 변경 가이드

| 상황 | 변경 변수 |
|---|---|
| 더 빠른 untagged 정리 | `untagged_image_expiration_days = 7` |
| 더 긴 sha 보존        | `tagged_image_retention_count = 100` |
| sha 외에 `pr-` 같은 임시 태그도 정리 대상 | `tag_prefix_filters = ["sha-", "pr-"]` |
| sha 정리 끄기         | `tagged_image_retention_count = 0` (rule 2 자체 비활성) |

## Tag Mutability

| 환경 | `image_tag_mutability` | 의미 |
|---|---|---|
| dev (tfvars 기본 override) | `MUTABLE`   | 동일 `sha-*` 태그를 재푸시 가능 — CI 재시도/로컬 빌드 반복 편의 |
| prod                        | `IMMUTABLE` | 동일 태그 재푸시 차단 — 운영 이미지의 변형을 원천 봉쇄 |

`IMMUTABLE` 에서 같은 SHA 의 재빌드가 필요하면 새 태그(`sha-abc1234-r2`)를 부여하거나 commit 자체를 새로 한다.

## 보안

- `scan_on_push = true` (모든 환경) — 푸시 즉시 ECR Basic Scan. 결과는 콘솔/CLI로 확인.
- 더 강한 검사가 필요하면 **계정 레벨 Enhanced Scanning (Inspector)** 활성화 (Terraform 외부에서 1회 설정).
- 암호화: 기본 `AES256`. `kms_key_arn` 으로 SSE-KMS 전환 가능 (KMS 모듈 추가 시).
- VPC Endpoint: `ecr.api`, `ecr.dkr` 가 활성화되어 있어 EKS 가 NAT 없이 이미지 풀 가능 (3단계 결과).

## CI 파이프라인 (6단계 예고)

```
PR push
  ├─ docker build .
  ├─ docker tag <repo>:sha-${GIT_SHORT_SHA}
  └─ trivy/snyk scan (CI 단계)

main merge
  ├─ docker build .
  ├─ aws ecr get-login-password | docker login
  ├─ docker tag  <repo>:sha-${GIT_SHORT_SHA}
  ├─ docker push <repo>:sha-${GIT_SHORT_SHA}
  └─ helm values bump → infra/helm/<svc>/values-<env>.yaml: image.tag = sha-${GIT_SHORT_SHA}
                       (Argo CD 가 변경 감지 → 클러스터 동기화)

release
  ├─ git tag v1.4.0 && git push --tags
  ├─ docker pull <repo>:sha-<commit>
  ├─ docker tag  <repo>:sha-<commit> <repo>:v1.4.0
  └─ docker push <repo>:v1.4.0
```

자세한 워크플로우는 6단계에서 `.github/workflows/build-push.yml` 로 구체화.

## 인증

| 사용처 | 방식 |
|---|---|
| 개발자 로컬 docker      | `aws ecr get-login-password --region <r> \| docker login --username AWS --password-stdin <acct>.dkr.ecr.<r>.amazonaws.com` |
| GitHub Actions          | OIDC + IAM Role (6단계). access key 미사용 |
| EKS 노드 (이미지 pull)  | EKS 노드 IAM Role 의 `AmazonEC2ContainerRegistryReadOnly` 정책 (5단계 EKS 모듈에서 부여) |
| EKS Pod (in-cluster)    | 노드 인증을 그대로 사용 (별도 imagePullSecrets 불필요) |

## URL 형식

```
<account-id>.dkr.ecr.<region>.amazonaws.com/<project>-<env>/<repo>:<tag>

예) 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/api-service:sha-abc1234
```

Helm values 의 image 블록:

```yaml
image:
  repository: 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/api-service
  tag: sha-abc1234   # latest 절대 금지
  pullPolicy: IfNotPresent
```

`image.repository` 는 Terraform output `ecr_repository_urls[<svc>]` 와 정확히 일치해야 한다 — CI 가 매번 lookup 하면 좋다.
