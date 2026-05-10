# Architecture

## 책임 분리 (가장 중요한 원칙)

| 영역 | 담당 | 예 |
|---|---|---|
| 판단 / 계획 / 자연어 ↔ 명세 | **LLM** | "출퇴근 시간 강남역 정체 완화" → ScenarioSpec |
| 검증 / 변환 / 파일 IO / 실행 | **코드** | OSM → `.net.xml`, KPI 계산, S3 업로드 |
| 교통 시뮬레이션 계산 | **SUMO** | 차량 미시 시뮬레이션 |

LLM에게 결정론적 계산을 시키지 않는다. 코드에게 정책적 판단을 시키지 않는다.

## 모듈 다이어그램

```
                       ┌────────────────────────┐
                       │       frontend         │
                       └───────────┬────────────┘
                                   │ HTTPS (ALB)
                                   ▼
                       ┌────────────────────────┐
                       │      api-service       │  ← 외부 진입점 (인증/검증/큐잉)
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │     agent-service      │  ← Orchestrator + Scenario Builder
                       │  (LLM Gateway 경유)     │
                       └─┬──────────┬──────────┬┘
                         │          │          │
              ┌──────────▼─┐  ┌─────▼───────┐  │
              │ simulation │  │  analysis   │  │
              │  -service  │  │  -service   │  │
              │ Net+Demand │  │   (KPI)     │  │
              │ +SUMO Run  │  └─────┬───────┘  │
              └─────┬──────┘        │          │
                    │ raw data      │ KPI      │
                    ▼               ▼          ▼
                  S3            S3 + RDS    report-service ── PDF/MD/HTML
                                                        ▲
                                                LLM Gateway 경유
```

## 모듈별 입출력 스키마 (개요)

| 모듈 | 입력 | 출력 |
|---|---|---|
| Orchestrator      | `UserRequest`            | `AgentTask`, `JobStatus` |
| Scenario Builder  | `UserRequest`            | `ScenarioSpec` |
| Network Builder   | `ScenarioSpec.area`      | `NetworkArtifact (.net.xml ref)` |
| Demand Builder    | `ScenarioSpec.demand`    | `DemandArtifact (.rou.xml ref)` |
| Simulator Runner  | `ScenarioSpec + Net + Demand` | `SimulationResult (raw refs)` |
| Analyzer          | `SimulationResult`       | `KPIDataset` |
| Reporter          | `KPIDataset + ScenarioSpec` | `ReportArtifact` |

상세 정의는 `packages/common-schema`에서 단일 소스로 관리한다 (10단계).

## 데이터 플로우

1. 사용자 요청 → `api-service` (인증/검증)
2. `api-service` → `agent-service` (작업 enqueue)
3. `agent-service` (Scenario Builder) → ScenarioSpec
4. `agent-service` → `simulation-service`로 Network/Demand/Run 트리거
5. `simulation-service` 산출물 → S3 + 메타데이터 RDS
6. `agent-service` → `analysis-service` 트리거
7. `analysis-service` 산출 KPI → S3 + RDS
8. `agent-service` → `report-service` 트리거
9. `report-service` 산출 리포트 → S3 (사인된 URL을 사용자에게 반환)

## 추상화 계층 (재교체 가능성을 위한)

```
   비즈니스 로직 (apps/*)
            │
            ▼
   ┌─────────────────────┐
   │  Gateway / Provider │   ← 모든 외부 의존은 여기서 추상화
   └─────────────────────┘
       │       │       │
   LLM GW   Storage  Vector DB
       │       │       │
   Bedrock   S3   pgvector / OpenSearch
   (교체:   (교체:    (교체:
   Local LLM,GCS,…  Pinecone,…)
   FT model)
```

비즈니스 로직은 AWS SDK를 **직접 import 하지 않는다**. 항상 인터페이스 경유.

## 개방된 결정 사항

- gRPC vs REST (서비스 간)
- 작업 큐: SQS vs Redis Streams vs DB-backed
- Workflow 엔진: 직접 구현 vs Argo Workflows vs Step Functions
- Agent 프레임워크 선택

각 항목은 해당 단계 진입 시 ADR(Architecture Decision Record)로 기록한다.
