# analysis-service

**Analyzer** 모듈. 시뮬레이션 raw 산출물 → KPI 데이터셋.

## 책임

- SUMO 산출물(차량 trip, edge 통계, 신호 등) 파싱
- KPI 계산: 평균 통행시간, 지연, 정체구간, 배출, 연료소비 등
- 결과를 S3 + RDS에 저장 (Storage Provider 경유)

## 책임 외

- 시뮬레이션 실행 (`simulation-service`)
- 정책적 해석/리포트 작성 (`report-service`)

이 서비스는 **결정론적 계산만** 담당. LLM 호출 없음.

## 의존

- Storage Provider (S3 raw 입력 + S3/RDS KPI 출력)
- Common Schema

## 미결 사항

- 처리 엔진: pandas vs DuckDB vs Spark — 데이터 규모 기준으로 결정
- 시계열 저장: RDS vs Timestream

## 배포

- Helm chart: `infra/helm/analysis-service/`
