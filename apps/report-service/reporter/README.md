# Reporter

정책적 리포트 생성 서비스. `AnalysisResult`를 정책적 의미로 해석하고 Markdown 리포트를 생성한다.

## 개요

- **입력**: `ReportRequest` (JSON) + `AnalysisResult`
- **출력**: `ReportArtifact` (JSON) + Markdown 리포트
- **지원 Reporter**:
  - `template`: 템플릿 기반 (빠름, LLM 불필요)
  - `llm`: LLM 기반 정책적 해석 (느림, LLM 필요)

## 디렉토리 구조

```
reporter/
├── main.py                     # FastAPI 앱
├── reporters/                  # Reporter 구현
│   ├── reporter.py             # Reporter 인터페이스
│   ├── template_reporter.py    # 템플릿 기반 Reporter
│   ├── llm_reporter.py         # LLM 기반 Reporter
│   └── pdf_generator.py        # PDF 생성기 (placeholder)
├── services/
│   └── report_service.py       # 메인 리포트 서비스
├── tests/
│   ├── test_template_reporter.py
│   ├── test_llm_reporter.py
│   └── test_api.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## 주요 컴포넌트

### 1. Reporter (인터페이스)

모든 Reporter가 구현해야 할 추상 클래스.

```python
class Reporter(ABC):
    @abstractmethod
    async def generate_report(
        self,
        analysis_result: dict,
        user_request: Optional[str] = None,
        experiment_context: Optional[dict] = None,
        rag_contexts: Optional[list] = None,
    ) -> ReportContent:
        pass
```

**ReportContent**:
```python
@dataclass
class ReportContent:
    markdown: str
    pdf: Optional[bytes] = None
```

### 2. TemplateReporter

템플릿 기반 리포터. 사전 정의된 구조로 리포트 생성.

**특징**:
- LLM 불필요
- 빠른 생성 속도
- 일관된 형식
- 정책적 해석 없음 (고정 메시지)

**리포트 구성**:
1. 요약
2. 사용자 요청 (선택)
3. 실험 조건 (선택)
4. 기준 시나리오 결과 (KPI 테이블)
5. 대안 시나리오 결과 (KPI 테이블)
6. 개선율 (개선율 테이블 + 평가)
7. 정책적 해석 (고정 메시지)
8. 제한사항
9. 후속 검토 사항

### 3. LLMReporter

LLM 기반 리포터. LLMGateway를 사용하여 정책적 해석 생성.

**특징**:
- LLM 필요 (LLMGateway)
- 느린 생성 속도
- 정책적 관점의 심층 분석
- RAG 컨텍스트 지원

**LLM 프롬프트**:
```
당신은 교통 정책 전문가입니다.
교통 시뮬레이션 분석 결과를 바탕으로 정책적 관점에서 해석하고 권고사항을 제시합니다.

다음 관점에서 분석하세요:
1. 교통 효율성 (통행 시간, 속도, 대기 시간)
2. 환경 영향 (배출량, 연료 소비)
3. 교통 안전 및 편의성
4. 실행 가능성 및 비용 효과
```

**LLM 응답 구조**:
- 정책적 해석 (2-3 문단)
- 권고사항 (3-5개 bullet points)
- 주의사항 (2-3개 bullet points)

### 4. PDFGenerator (Placeholder)

Markdown → PDF 변환 (향후 구현).

**계획**:
- Markdown → HTML → PDF 파이프라인
- 템플릿 커스터마이징
- 차트 및 그래프 삽입
- 페이지 번호, 헤더, 푸터

### 5. ReportService

전체 리포트 생성 흐름 관리:

1. `ReportRequest` 파싱
2. Reporter 선택 (Template / LLM)
3. 리포트 생성 (Markdown)
4. PDF 생성 (향후)
5. StorageGateway로 업로드
6. `ReportArtifact` 반환

## API 엔드포인트

### POST /report/generate

리포트 생성.

**요청**:
```json
{
  "report_request": {
    "schema_version": "1.0",
    "request_id": "req-rep-001",
    "experiment_id": "exp-001",
    "analysis_result": {
      "schema_version": "1.0",
      "analysis_id": "ana-001",
      "experiment_id": "exp-001",
      "kpi_comparison": {
        "baseline_kpis": {
          "average_travel_time": 125.0,
          "average_waiting_time": 12.0,
          "average_speed": 4.16,
          "total_co2": 16590.0
        },
        "alternative_kpis": {
          "average_travel_time": 110.0,
          "average_waiting_time": 9.6,
          "average_speed": 4.58,
          "total_co2": 14931.0
        },
        "improvements": {
          "average_travel_time": 12.0,
          "average_waiting_time": 20.0,
          "average_speed": 10.1,
          "total_co2": 10.0
        }
      },
      "overall_score": 13.5,
      "summary": "Alternative 시나리오가 전반적으로 우수합니다."
    },
    "user_request": "교통 수요를 20% 증가시켰을 때의 영향을 분석해주세요.",
    "experiment_context": {
      "request_type": "demand_increase",
      "demand_multiplier": 1.2
    },
    "rag_contexts": [
      {"content": "참고: 유사 지역 사례..."}
    ]
  },
  "reporter_type": "llm"
}
```

**응답** (`ReportArtifact`):
```json
{
  "schema_version": "1.0",
  "artifact_id": "rep-001",
  "request_id": "req-rep-001",
  "experiment_id": "exp-001",
  "report_uri": "s3://bucket/exp-001/report.md",
  "report_format": "markdown",
  "pdf_uri": null,
  "sections": [
    "요약",
    "사용자 요청",
    "실험 조건",
    "기준 시나리오 결과",
    "대안 시나리오 결과",
    "개선율",
    "정책적 해석",
    "제한사항",
    "후속 검토 사항"
  ],
  "created_at": "2026-05-07T12:00:00",
  "generated_by": "reporter-llmreporter-v0.1.0",
  "processing_time_ms": 3500.5
}
```

### GET /health

헬스 체크.

### GET /ready

준비 상태 체크 (LLM 사용 가능 여부 포함).

### GET /

서비스 정보 및 지원 Reporter 타입 목록.

## 로컬 실행

### Template Reporter (LLM 불필요)

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export STORAGE_PROVIDER=local
export STORAGE_BASE_PATH=/tmp/reports
export PORT=8006

# 서비스 시작
python -m uvicorn reporter.main:app --host 0.0.0.0 --port 8006 --reload
```

### LLM Reporter (LLM 필요)

```bash
# 환경 변수 설정
export STORAGE_PROVIDER=local
export STORAGE_BASE_PATH=/tmp/reports
export LLM_PROVIDER=bedrock
export AWS_REGION=ap-northeast-2
export PORT=8006

# 서비스 시작
python -m uvicorn reporter.main:app --host 0.0.0.0 --port 8006 --reload
```

## Docker 실행

```bash
# 이미지 빌드
docker build -t reporter:latest -f apps/reporter/Dockerfile .

# Template Reporter만 사용
docker run -d \
  --name reporter \
  -p 8006:8006 \
  -e STORAGE_PROVIDER=local \
  -e STORAGE_BASE_PATH=/app/data/reports \
  reporter:latest

# LLM Reporter 사용
docker run -d \
  --name reporter \
  -p 8006:8006 \
  -e STORAGE_PROVIDER=s3 \
  -e STORAGE_BASE_PATH=agent-t-reports \
  -e LLM_PROVIDER=bedrock \
  -e AWS_REGION=ap-northeast-2 \
  -e AWS_ACCESS_KEY_ID=<key> \
  -e AWS_SECRET_ACCESS_KEY=<secret> \
  reporter:latest
```

## 테스트

```bash
# 모든 테스트 실행
pytest apps/reporter/tests/ -v

# 특정 테스트 실행
pytest apps/reporter/tests/test_template_reporter.py -v
pytest apps/reporter/tests/test_llm_reporter.py -v
pytest apps/reporter/tests/test_api.py -v

# 커버리지
pytest apps/reporter/tests/ --cov=apps.reporter --cov-report=html
```

## 설정

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `STORAGE_PROVIDER` | `local` | 스토리지 제공자 (`local` / `s3`) |
| `STORAGE_BASE_PATH` | `/app/data/reports` | 로컬 저장 경로 또는 S3 버킷 |
| `LLM_PROVIDER` | `bedrock` | LLM 제공자 (LLM Reporter용) |
| `AWS_REGION` | - | AWS 리전 (Bedrock 사용 시) |
| `PORT` | `8006` | 서비스 포트 |

## 리포트 예시

### Markdown 리포트 구조

```markdown
# 교통 시뮬레이션 분석 리포트

**실험 ID**: exp-001
**생성 일시**: 2026-05-07 12:00:00 UTC

---

## 1. 요약

Alternative 시나리오가 전반적으로 우수합니다. 평균 통행 시간 12.0% 개선, 평균 대기 시간 20.0% 개선.

**종합 평가 점수**: 13.50점

## 2. 사용자 요청

```
교통 수요를 20% 증가시켰을 때의 영향을 분석해주세요.
```

## 3. 실험 조건

- **request_type**: demand_increase
- **demand_multiplier**: 1.2

## 4. 기준 시나리오 (Baseline) 결과

| KPI | 값 | 단위 |
|-----|------|------|
| 평균 통행 시간 | 125.00 | 초 |
| 평균 대기 시간 | 12.00 | 초 |
| 평균 속도 | 4.16 | m/s |
| 총 CO2 배출 | 16590.00 | mg |

## 5. 대안 시나리오 (Alternative) 결과

| KPI | 값 | 단위 |
|-----|------|------|
| 평균 통행 시간 | 110.00 | 초 |
| 평균 대기 시간 | 9.60 | 초 |
| 평균 속도 | 4.58 | m/s |
| 총 CO2 배출 | 14931.00 | mg |

## 6. 개선율

| KPI | 개선율 | 평가 |
|-----|--------|------|
| 평균 통행 시간 | +12.00% | ✅ 우수 |
| 평균 대기 시간 | +20.00% | ✅ 우수 |
| 평균 속도 | +10.10% | ✅ 우수 |
| 총 CO2 배출 | +10.00% | ✅ 우수 |

## 7. 정책적 해석

### 정책적 의미

Alternative 시나리오는 교통 효율성과 환경 영향 모두에서 유의미한 개선을 보여줍니다...

### 권고사항

- 단계적 시범 적용 권장
- 실시간 모니터링 체계 구축 필요
- 주민 의견 수렴 및 공청회 실시

### 주의사항

- 시뮬레이션과 실제 상황의 차이 고려 필요
- 비용-편익 분석 추가 검토 요망

## 8. 제한사항

- 본 분석은 시뮬레이션 결과를 기반으로 하며...
- 장기적인 효과나 간접 영향은 고려되지 않았습니다...

## 9. 후속 검토 사항

- 다양한 교통 수요 시나리오에서의 추가 검증
- 실제 현장 데이터와의 비교 분석
- 비용-편익 분석 및 예산 검토

---

*본 리포트는 AI Agent T 플랫폼에서 자동 생성되었습니다.*
```

## Reporter 비교

| 항목 | Template Reporter | LLM Reporter |
|------|-------------------|--------------|
| **속도** | 빠름 (< 100ms) | 느림 (1-5초) |
| **LLM 필요** | 불필요 | 필요 |
| **정책적 해석** | 고정 메시지 | LLM 생성 |
| **RAG 지원** | 미지원 | 지원 |
| **비용** | 무료 | LLM 비용 발생 |
| **일관성** | 높음 | 중간 |
| **심층 분석** | 없음 | 있음 |

## 확장 가능성

### 새 Reporter 추가

1. `Reporter` 인터페이스 구현
2. `main.py`에 등록
3. 테스트 작성

**예시**:
```python
class CustomReporter(Reporter):
    async def generate_report(self, analysis_result, ...) -> ReportContent:
        # Custom 로직
        pass
```

### PDF 생성 구현

1. `PDFGenerator` 구현
2. Markdown → HTML 변환 (markdown 라이브러리)
3. HTML → PDF 변환 (weasyprint 또는 pdfkit)
4. `ReportService`에 통합

### 차트 추가

1. KPI 차트 생성 (matplotlib, plotly)
2. Markdown에 이미지 삽입
3. PDF에 차트 포함

## 제약 사항

- **초기 구현**: Markdown만 지원, PDF는 placeholder
- **LLM Reporter**: LLMGateway 초기화 실패 시 사용 불가
- **템플릿**: 고정된 구조, 커스터마이징 제한적
- **언어**: 한국어만 지원

## 다음 단계

1. **PDF 생성 구현**: Markdown → PDF 파이프라인
2. **차트 생성**: KPI 시각화
3. **템플릿 커스터마이징**: 사용자 정의 템플릿
4. **다국어 지원**: 영어, 일본어 등
5. **이메일 전송**: 리포트 자동 배포
6. **버전 관리**: 리포트 히스토리 추적

## 참고

- [Markdown Specification](https://spec.commonmark.org/)
- [WeasyPrint Documentation](https://weasyprint.readthedocs.io/)
- [Python Markdown](https://python-markdown.github.io/)
