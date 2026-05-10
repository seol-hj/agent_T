# report-service

**Reporter** 모듈. KPI 데이터셋 → 정책적 리포트(PDF/Markdown/HTML).

## 책임

- KPI 해석을 위한 LLM 호출 (LLM Gateway 경유)
- 차트/표 렌더링
- 다양한 포맷으로 리포트 생성 (PDF, MD, HTML)
- 결과를 S3에 업로드 + 사인된 URL 발급

## 책임 외

- KPI 계산 (`analysis-service`)
- 시뮬레이션 실행 (`simulation-service`)

## 의존

- LLM Gateway (정책적 해석 단계)
- Storage Provider
- 차트 렌더러 (matplotlib / plotly / vega-lite — 추후 결정)
- PDF 생성기 (weasyprint / chromium headless — 추후 결정)

## 미결 사항

- 템플릿 엔진
- 다국어 지원 범위

## 배포

- Helm chart: `infra/helm/report-service/`
