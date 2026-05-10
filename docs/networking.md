# Networking

VPC 와 서브넷 설계 문서. 변경 시 `infra/terraform/modules/vpc/` 와 함께 수정.

## CIDR 설계

| 환경 | VPC CIDR | 비고 |
|---|---|---|
| dev  | `10.10.0.0/16` | 2 AZ |
| prod | `10.20.0.0/16` | 3 AZ |

### 서브넷 자동 도출 (newbits = 4 → 모든 서브넷 `/20`)

`vpc_cidr` 만 주면 모듈이 다음 규칙으로 서브넷 CIDR 을 도출한다:

```
public[i]      = cidrsubnet(vpc_cidr, 4, i)
private_app[i] = cidrsubnet(vpc_cidr, 4, i + 4)
private_db[i]  = cidrsubnet(vpc_cidr, 4, i + 8)
```

**예시: `10.10.0.0/16`, AZ 3개**

| Tier | AZ-a | AZ-b | AZ-c |
|---|---|---|---|
| public      | `10.10.0.0/20`   | `10.10.16.0/20`  | `10.10.32.0/20`  |
| private-app | `10.10.64.0/20`  | `10.10.80.0/20`  | `10.10.96.0/20`  |
| private-db  | `10.10.128.0/20` | `10.10.144.0/20` | `10.10.160.0/20` |

각 `/20` = 4096 IP. EKS Pod ENI 가 IP 를 많이 소모하므로 private-app 은 `/20` 권장.
override 하려면 `public_subnet_cidrs` / `private_app_subnet_cidrs` / `private_db_subnet_cidrs` 변수 사용.

## 서브넷 3-tier 책임

| Tier | 누가 산다 | 인터넷 라우트 | 들어오는 트래픽 | 나가는 트래픽 |
|---|---|---|---|---|
| **public**      | ALB, NAT Gateway        | IGW (`0.0.0.0/0`) | 외부 → ALB | ALB → 내부 |
| **private-app** | EKS 노드, K8s 서비스    | (옵션) NAT → IGW  | ALB / 내부 서비스 | NAT 또는 VPC Endpoint |
| **private-db**  | RDS, ElastiCache, VPC Endpoint | 없음 (intra-only) | 내부 서비스에서만 | 없음 (S3 Gateway endpoint 만 prefix-list 라우트로) |

### 왜 3-tier 인가

- **블래스트 라디우스**: DB 서브넷은 인터넷에 닿지 않는다. RDS 가 실수로 0.0.0.0/0 라우트가 있는 RT 에 attach 되는 사고를 막는다.
- **NAT 트래픽 격리**: private-app 만 NAT 를 사용 — DB 트래픽이 NAT 비용에 섞이지 않는다.
- **VPC Endpoint 정책의 일관성**: private-db RT 는 외부 라우트가 절대 없으므로 endpoint policy 가 단순해진다.

## 라우트 테이블

| RT | 개수 | 라우트 |
|---|---|---|
| `rt-public`              | 1 (공유) | `0.0.0.0/0 → IGW` |
| `rt-private-app-<az>`    | AZ 별 1 | `0.0.0.0/0 → NAT` (NAT 활성 시), 그 외 intra |
| `rt-private-db-<az>`     | AZ 별 1 | intra 만 (외부 라우트 없음) |

private 측을 AZ 별로 분리한 이유:
- AZ별 NAT (`single_nat_gateway = false`) 사용 시 RT 마다 다른 NAT 를 가리켜야 한다.
- AZ 격리 장애 (NAT 한 대 다운) 시 다른 AZ 영향이 없다.

## NAT Gateway 전략

| 환경 | `enable_nat_gateway` | `single_nat_gateway` | 비고 |
|---|---|---|---|
| **dev**  | `false` (기본) | `true` | NAT 없이 VPC Endpoint 만으로 동작 시도. 외부 인터넷 필요한 워크로드는 명시적으로 enable. |
| **prod** | `true`  | `false` | AZ별 NAT 1개씩. 비용 ↑, HA ↑. |

NAT 1개 ≈ 월 $32 + 트래픽($/GB). 3 AZ 면 NAT 만 월 ~$96. 따라서:
- dev 는 가능하면 NAT off → VPC Endpoint (S3, ECR, STS, Secrets Manager 등) 로 우회.
- 외부 GitHub / Docker Hub / pip 등이 필요하면 dev 에서도 NAT 켜는 편이 운영 단순.
- prod 는 무조건 AZ별 NAT.

dev 에서 NAT off 시 주의:
- 컨테이너가 외부 인터넷이 필요하다면 빌드 단계에서 사전 다운로드해 이미지에 포함해야 함.
- ECR Public Gallery 도 NAT 가 필요 — 사설 ECR 로만 운영 가능해야 한다.

## 서브넷 태그 (Kubernetes Load Balancer Controller 용)

AWS Load Balancer Controller (5단계에 설치) 가 자동 검색하는 태그:

| 서브넷 tier | 태그 | 의미 |
|---|---|---|
| public      | `kubernetes.io/role/elb = 1`          | internet-facing ALB / NLB 후보 |
| private-app | `kubernetes.io/role/internal-elb = 1` | internal ALB / NLB 후보 |
| private-db  | (없음)                                  | LB 가 위치하지 않음 |

EKS cluster discovery 태그(`kubernetes.io/cluster/<name>`) 는 본 모듈에서 추가하지 않는다 — Load Balancer Controller v2.6+ 는 cluster ID 매칭 없이 자동 동작. 필요 시 EKS 모듈에서 후처리로 추가.

## VPC Endpoints (예고)

본 VPC 모듈은 endpoint 를 만들지 않는다. 다음 모듈인 `vpc-endpoints` 가 처리:

- **Gateway**: S3, DynamoDB → `private_route_table_ids` 에 attach (모듈 출력 사용)
- **Interface**: ECR(api/dkr), STS, Secrets Manager, Logs, Bedrock(런타임), EC2, Autoscaling 등 → private-db 서브넷에 ENI

NAT off + endpoint 로 외부 의존을 끊는 것이 보안·비용 최적의 형태.

## 운영 노트 / 향후 작업

- **VPC Flow Logs**: 본 단계에서는 미설정. 운영 보안 강화 시 별도 모듈 / `aws_flow_log` 추가.
- **Egress 제어**: 현재는 SG 기본값. WAF / Network Firewall 도입은 별도 ADR.
- **IPv6**: 사용하지 않음. 향후 dual-stack 요구 시 모듈 확장.
- **PrefixList 기반 0.0.0.0/0 분리**: 트래픽 가시성 강화가 필요해지면 도입.

## 모듈 출력 → 다른 모듈 입력 연결

| `module.vpc` output | 사용처 (다음 단계들) |
|---|---|
| `vpc_id`                  | vpc-endpoints, eks, rds(SG), redis(SG), alb-controller |
| `public_subnet_ids`       | (참고용) ALB 자동 검색이 사용 |
| `private_app_subnet_ids`  | eks (노드 그룹 배치) |
| `private_db_subnet_ids`   | vpc-endpoints (interface), rds, redis |
| `database_subnet_ids`     | rds (`aws_db_subnet_group.subnet_ids` 직접 입력) |
| `private_route_table_ids` | vpc-endpoints (Gateway 타입 attach) |
