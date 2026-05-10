# agent-service

**Orchestrator + Scenario Builder**가 동작하는 핵심 AI 서비스.

## 책임

- 사용자 요청 라우팅 / 작업 흐름 제어 (Orchestrator)
- 자연어 요구사항 → 실험 명세 변환 (Scenario Builder)
- 모듈 간 호출 조율 (Network/Demand/Sim/Analyzer/Report)
- LLM 호출은 **반드시 LLM Gateway 경유** (Bedrock SDK 직접 호출 금지)

## 책임 외

- 결정론적 계산 (XML 생성, 수치 분석) — `simulation-service` / `analysis-service`로
- 외부 API 노출 — `api-service`로

## 의존

- LLM Gateway (`packages/` 또는 별도 sidecar — 추후 결정)
- Common Schema (`packages/common-schema`)
- 다른 서비스 호출 (gRPC vs REST 추후 결정)

## 미결 사항

- Agent 프레임워크: 자체 구현 vs LangGraph vs Bedrock Agents — 추후 결정
- 컨텍스트 저장소: Redis(단기) + RDS(장기) 분담 방식

## 배포

- Helm chart: `infra/helm/agent-service/`
- Bedrock 호출을 위한 IRSA(IAM Role for Service Account) 필요
