# VPC Endpoints

VPC 내부 서비스가 AWS 서비스 API 를 **인터넷/NAT 우회 없이** 호출하기 위한 PrivateLink 구성.
변경 시 `infra/terraform/modules/vpc-endpoints/` 와 함께 수정.

## 왜 VPC Endpoint 인가

1. **보안**: 트래픽이 VPC 를 떠나지 않는다. 외부 IGW/NAT 우회 경로가 없으므로 데이터 유출 면 면적이 줄어듦.
2. **비용**: dev 에서 NAT off 가능. NAT 1 대 ≈ $32/월 + 트래픽 vs Interface endpoint ≈ $7.5/월/AZ. Endpoint 호출량이 NAT 트래픽보다 많지 않은 한 Endpoint 가 유리.
3. **신뢰성**: NAT 한 대 다운 시 모든 외부 호출이 중단되는 것 vs Interface endpoint 는 AZ 별 ENI 로 분산.

## 구성 요약

| # | 서비스 | Endpoint 타입 | 활성화 토글 | Default |
|---|---|---|---|---|
| 1 | S3                          | **Gateway**   | (항상)                         | on |
| 2 | ECR API                     | Interface     | (항상)                         | on |
| 3 | ECR DKR                     | Interface     | (항상)                         | on |
| 4 | CloudWatch Logs             | Interface     | `enable_cloudwatch_endpoint`   | on |
| 5 | Secrets Manager             | Interface     | (항상)                         | on |
| 6 | STS                         | Interface     | (항상)                         | on |
| 7 | KMS                         | Interface     | `enable_kms_endpoint`          | on |
| 8 | Bedrock Runtime (`bedrock-runtime`) | Interface | `enable_bedrock_endpoint`     | on |
| 9 | Bedrock (control)           | Interface     | `enable_bedrock_endpoint`      | on |

**왜 "always-on"이 있나**: ECR/STS/SecretsManager 가 끊기면 EKS 가 사실상 동작 못 한다 (이미지 풀, IRSA, DB 자격증명). 토글 노출은 사고 방지를 위해 의도적으로 제한.

## 각 Endpoint 의 용도

### S3 (Gateway)

- **용도**: SUMO 시뮬레이션 산출물(.net.xml, raw output, KPI, 리포트) 저장/조회. ECR 이미지 layer storage 도 내부적으로 S3 에 가므로 ECR endpoint 와 짝꿍.
- **위치**: VPC 내 모든 private route table (app + db) 에 prefix list 라우트 자동 추가.
- **비용**: Gateway endpoint 는 시간당 요금 0, 트래픽 0. 사실상 공짜.

### ECR API / ECR DKR (Interface ×2)

- **ECR API**: `ecr:GetAuthorizationToken`, `DescribeRepositories` 등 **메타데이터** 호출.
- **ECR DKR**: 실제 **이미지 layer pull** 트래픽. 컨테이너 이미지 다운로드는 여기로 흐른다.
- 둘 다 있어야 EKS 노드가 NAT off 에서 이미지 풀 가능. **함께 활성화**.

### CloudWatch Logs (Interface)

- 컨테이너 stdout/stderr 가 CloudWatch Logs 로 가는 경우 필요. 미사용(Loki 등 다른 로깅) 환경이면 off 가능 → `enable_cloudwatch_endpoint = false`.

### Secrets Manager (Interface)

- 앱이 DB 비밀번호, 외부 API 키를 Secrets Manager 에서 끌어올 때 사용. **항상 켠다**.

### STS (Interface)

- IRSA(IAM Role for Service Account) 가 `AssumeRoleWithWebIdentity` 를 호출하는 endpoint. **EKS Pod 가 IAM 자격을 받는 경로**. 끊기면 모든 IRSA 동작 중단.

### KMS (Interface)

- Secrets Manager 의 시크릿 암복호화, RDS storage 암호화, S3 SSE-KMS 호출 시 사용. KMS CMK 를 적극 활용한다면 켠다.
- 비활성화하려면 `enable_kms_endpoint = false`.

### Bedrock Runtime (Interface)

- `InvokeModel`, `InvokeModelWithResponseStream` 호출 경로. **LLM Gateway 의 핵심 의존**.
- 리전이 Bedrock 미지원이면 `enable_bedrock_endpoint = false` 로 끄고, 다른 리전 endpoint 를 통해 호출 (cross-region) 또는 Local LLM 어댑터로 대체.

### Bedrock control (Interface)

- 모델 목록 조회(`ListFoundationModels`), Knowledge Base, Agent 관리 호출. 호출량은 적지만 동일 토글로 묶어 운영 단순화.

## Security Group 정책

```
ingress: 443/tcp from VPC CIDR
egress : all
```

- **VPC CIDR 기반**으로 `vpc_cidr_block` 변수에서 받음.
- 추후 EKS 노드 SG 만 허용하도록 좁히려면 5단계에서 `ingress` 를 `security_groups = [<eks_node_sg>]` 로 교체.
- egress 는 endpoint ENI 가 클라이언트에게 응답해야 하므로 모든 방향 허용 (실제 외부 인터넷으로 나가지 않음 — 라우팅이 차단).

## Endpoint Policy

본 단계에서는 default policy(IAM 정책에 위임). 향후 강화 시:

- 본 계정/조직 외 호출 차단 (`aws:PrincipalOrgID` 조건)
- 특정 S3 bucket 만 허용
- 특정 Bedrock 모델 ID 만 허용

이는 보안 강화 단계(별도 ADR)에서 다룬다.

## 비용 추정

| 항목 | 단가 (서울 리전 기준 근사) | dev 2 AZ | prod 3 AZ |
|---|---|---|---|
| Interface endpoint ENI | $0.014/시간/AZ ≈ $10/월/AZ | 7 endpoint × 2 AZ = 14 ENI ≈ $140/월 | 7 × 3 = 21 ENI ≈ $210/월 |
| Interface 트래픽       | $0.01/GB |  사용량 비례 | 사용량 비례 |
| Gateway (S3)           | 무료 | $0 | $0 |
| **NAT 절감 효과**       | NAT $32/월/AZ + $0.045/GB | dev 에서 NAT 0 → -$32 ~ -$96 | prod 는 NAT 도 유지 |

dev 에서 모든 endpoint on + NAT off 가 비용 면에서 nominally 비슷하지만, **외부 인터넷이 필요 없다면 endpoint 만으로 충분**. 외부 의존이 있으면 NAT 도 켜야 한다.

## DNS 동작 (`private_dns_enabled = true`)

Interface endpoint 가 활성화되면 AWS 가 VPC 에 **사설 호스팅 영역(R53)** 을 자동 생성해, public DNS 이름(예: `sts.ap-northeast-2.amazonaws.com`)이 endpoint ENI 의 사설 IP 로 resolve 된다. → 앱은 일반 SDK 호출 코드 그대로 두고, 트래픽만 endpoint 로 흘러간다.

전제: VPC 의 `enable_dns_support = true`, `enable_dns_hostnames = true`. 본 프로젝트 vpc 모듈에서 이미 설정.

## 향후 추가가 필요할 endpoint

5단계(EKS) 진입 시 NAT off 모드를 유지하려면 다음을 추가 검토:

| 서비스 | 사유 |
|---|---|
| `ec2`                   | EKS 노드의 IMDS 외 메타데이터, 태깅, ENI 관리 |
| `autoscaling`           | Cluster Autoscaler / ASG 호출 |
| `elasticloadbalancing`  | AWS Load Balancer Controller 가 ALB 생성 시 호출 |
| `eks`                   | aws-auth, EKS API 콜 |
| `ssm`                   | Session Manager / Parameter Store |

추가 시 본 모듈의 `interface_endpoints_all` map 에 항목만 추가하면 된다.

## 모듈 출력

| Output | 용도 |
|---|---|
| `security_group_id`             | 이 SG 를 다른 모듈(EKS, RDS 등)이 ingress 로 받을 수 있다 |
| `s3_endpoint_id`                | (관찰/디버깅용) |
| `s3_endpoint_prefix_list_id`    | SG egress 를 prefix list 로 좁힐 때 destination |
| `interface_endpoint_ids`        | 라벨 → endpoint id map |
| `interface_endpoint_dns_entries`| 연결 검증/디버깅 |
| `enabled_endpoints`             | plan 시 실제 생성된 라벨 목록 (드리프트 방지) |
