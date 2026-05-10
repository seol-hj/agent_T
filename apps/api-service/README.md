# api-service

외부 트래픽 진입점. ALB → 이 서비스 → 내부 마이크로서비스 라우팅.

## 책임

- 외부 REST/WebSocket API 노출
- 인증·인가 (토큰 검증)
- 요청 검증, 사용량 제한
- 작업 큐잉 (사용자 요청 → `agent-service` 호출)
- 진행 상황·결과 조회 엔드포인트

## 책임 외 (다른 서비스로 위임)

- AI 판단 → `agent-service`
- 시뮬레이션 → `simulation-service`
- 분석/리포트 → `analysis-service` / `report-service`

이 서비스는 **얇은 진입 계층**이다. 비즈니스 로직을 두지 않는다.

## 미결 사항

- 언어/프레임워크: FastAPI(Python) vs Echo/Gin(Go) — 추후 결정
- 인증 방식

## 배포

- Helm chart: `infra/helm/api-service/`
- ALB Ingress 대상은 이 서비스 하나 (다른 서비스는 ClusterIP)
