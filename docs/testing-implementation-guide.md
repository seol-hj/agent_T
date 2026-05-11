# 테스트 구현 가이드

**최종 업데이트**: 2026-05-11  
**상태**: 테스트 코드 미구현, CI에서 스킵 중

---

## 현재 상태

### CI/CD에서 테스트 스킵 중
```yaml
# .github/workflows/ci-frontend.yml
test-command: |
  npm install
  npm run build
skip-tests: true  # TODO: 테스트 코드 구현 후 false로 변경

# .github/workflows/ci-*-service.yml
test-command: |
  pip install -r requirements.txt
  echo "Tests skipped - TODO: implement tests"
skip-tests: true  # TODO: 테스트 코드 구현 후 false로 변경
```

**이유**:
- Frontend: `package.json`에 `test` 스크립트 없음
- Backend: `pytest` 설치 안 됨, 테스트 파일 없음

---

## 테스트 구현 로드맵

### Phase 1: 기본 테스트 환경 구성 (1-2일)

#### Frontend (Next.js)
```bash
cd apps/frontend

# 1. 테스트 라이브러리 설치
npm install --save-dev @testing-library/react @testing-library/jest-dom jest jest-environment-jsdom

# 2. jest.config.js 생성
cat > jest.config.js << 'EOF'
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  testMatch: ['**/__tests__/**/*.test.ts', '**/__tests__/**/*.test.tsx'],
}

module.exports = createJestConfig(customJestConfig)
EOF

# 3. jest.setup.js 생성
cat > jest.setup.js << 'EOF'
import '@testing-library/jest-dom'
EOF

# 4. package.json에 test 스크립트 추가
npm pkg set scripts.test="jest"
npm pkg set scripts.test:watch="jest --watch"
```

#### Backend (FastAPI)
```bash
cd apps/agent-service  # 또는 다른 서비스

# 1. requirements.txt에 pytest 추가
cat >> requirements.txt << 'EOF'

# Testing
pytest==8.0.0
pytest-asyncio==0.23.0
pytest-cov==4.1.0
httpx==0.26.0
EOF

# 2. pytest 설치
pip install -r requirements.txt

# 3. pytest.ini 생성
cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=app --cov-report=term-missing
EOF
```

---

### Phase 2: 기본 테스트 작성 (3-5일)

#### Frontend 테스트 예시

**파일**: `apps/frontend/src/__tests__/pages/index.test.tsx`
```typescript
import { render, screen } from '@testing-library/react'
import Home from '@/pages/index'

describe('Home Page', () => {
  it('renders without crashing', () => {
    render(<Home />)
    expect(screen.getByRole('main')).toBeInTheDocument()
  })

  it('displays the welcome message', () => {
    render(<Home />)
    expect(screen.getByText(/AI Agent T/i)).toBeInTheDocument()
  })
})
```

**파일**: `apps/frontend/src/__tests__/components/Header.test.tsx`
```typescript
import { render, screen } from '@testing-library/react'
import Header from '@/components/Header'

describe('Header Component', () => {
  it('renders logo', () => {
    render(<Header />)
    expect(screen.getByAltText(/logo/i)).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(<Header />)
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument()
    expect(screen.getByText(/Simulations/i)).toBeInTheDocument()
  })
})
```

---

#### Backend 테스트 예시

**파일**: `apps/agent-service/tests/conftest.py`
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway for testing"""
    from unittest.mock import Mock
    gateway = Mock()
    gateway.generate.return_value = {
        "content": "Test scenario",
        "usage": {"input_tokens": 10, "output_tokens": 20}
    }
    return gateway
```

**파일**: `apps/agent-service/tests/test_health.py`
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_ready_endpoint(client: AsyncClient):
    response = await client.get("/ready")
    assert response.status_code == 200
    assert "version" in response.json()
```

**파일**: `apps/agent-service/tests/test_scenario_builder.py`
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_build_scenario(client: AsyncClient, mock_llm_gateway):
    # Given
    request_data = {
        "user_input": "강남역 일대 교통량 20% 증가 시뮬레이션",
        "language": "ko"
    }
    
    # When
    response = await client.post("/scenario/build", json=request_data)
    
    # Then
    assert response.status_code == 200
    data = response.json()
    assert "scenario_id" in data
    assert "location" in data
    assert data["location"]["name"] == "강남역"
```

---

### Phase 3: CI/CD 통합 (1일)

#### 1. Frontend 테스트 활성화
```yaml
# .github/workflows/ci-frontend.yml
test-command: |
  npm ci
  npm run test
  npm run lint
skip-tests: false  # ✅ 활성화
```

#### 2. Backend 테스트 활성화
```yaml
# .github/workflows/ci-agent-service.yml
test-command: |
  pip install -r requirements.txt
  pytest tests/ --cov=app --cov-report=xml
skip-tests: false  # ✅ 활성화
```

#### 3. Coverage 리포트 추가
```yaml
# .github/workflows/build-and-push.yml
- name: Upload coverage to Codecov
  if: ${{ !inputs.skip-tests }}
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
    flags: ${{ inputs.service-name }}
```

---

## 테스트 전략

### 테스트 피라미드

```
       /\
      /E2E\      10% - End-to-End (느림, 비용 높음)
     /------\
    /Integr.\   20% - Integration (중간)
   /----------\
  /   Unit     \ 70% - Unit Tests (빠름, 저비용)
 /--------------\
```

### 우선순위

#### P0 - 필수 (즉시 구현)
- [x] Health check endpoints
- [ ] API 기본 응답 (200, 404, 500)
- [ ] 주요 비즈니스 로직 (Scenario Builder, Analyzer)

#### P1 - 중요 (1주 이내)
- [ ] Gateway 추상화 계층 (LLM, Storage)
- [ ] Database 연동 (Repository 계층)
- [ ] 입력 검증 (Pydantic)

#### P2 - 보조 (1개월 이내)
- [ ] Edge cases
- [ ] Performance tests
- [ ] E2E tests

---

## 서비스별 테스트 체크리스트

### Frontend
- [ ] Component rendering tests
- [ ] User interaction tests (click, input)
- [ ] API mocking tests
- [ ] Routing tests
- [ ] Error boundary tests

### Agent Service (Scenario Builder)
- [ ] `/scenario/build` API
- [ ] LLM Gateway mocking
- [ ] 자연어 → 명세 변환 검증
- [ ] Error handling (invalid input)

### Simulation Service
- [ ] Network Builder (OSM → SUMO)
- [ ] Demand Builder
- [ ] Simulator Runner
- [ ] File I/O (XML 생성/읽기)

### Analysis Service
- [ ] KPI 계산 로직
- [ ] 통계 분석
- [ ] 데이터 파싱 (tripinfo.xml)

### Report Service
- [ ] LLM Report 생성
- [ ] Template rendering
- [ ] PDF 생성 (선택)

### Pipeline (Orchestrator)
- [ ] E2E 파이프라인 흐름
- [ ] 모듈 간 연동
- [ ] DB 상태 관리
- [ ] 에러 전파 및 복구

---

## Mock 데이터

### LLM Gateway Mock
```python
# libs/common/gateways/llm.py
class MockLLMProvider(LLMGateway):
    """테스트용 Mock LLM"""
    def __init__(self, model_id: str = "mock-model-v1"):
        self.model_id = model_id
    
    def generate(self, messages: List[dict], **kwargs) -> LLMResponse:
        # 하드코딩된 응답 반환
        return LLMResponse(
            content="Mock scenario output",
            usage=LLMUsageMetadata(
                input_tokens=10,
                output_tokens=20,
                total_tokens=30
            )
        )
```

### Storage Gateway Mock
```python
# libs/common/gateways/storage.py
class MockStorageProvider(StorageGateway):
    """테스트용 Mock Storage"""
    def __init__(self):
        self.storage = {}
    
    def save(self, key: str, data: bytes):
        self.storage[key] = data
    
    def load(self, key: str) -> bytes:
        return self.storage.get(key, b"")
```

---

## 실행 방법

### 로컬 테스트
```bash
# Frontend
cd apps/frontend
npm test
npm test -- --coverage

# Backend (예: agent-service)
cd apps/agent-service
pytest
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### CI에서 테스트
```bash
# GitHub Actions 트리거
git add .
git commit -m "test: add unit tests"
git push origin main

# Actions 탭에서 확인
```

---

## 테스트 커버리지 목표

| 서비스 | 목표 커버리지 | 현재 |
|--------|---------------|------|
| Frontend | 70% | 0% |
| Agent Service | 80% | 0% |
| Simulation Service | 60% | 0% |
| Analysis Service | 80% | 0% |
| Report Service | 70% | 0% |
| Pipeline | 70% | 0% |

---

## 참고 자료

- [Testing Library (React)](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest (Frontend)](https://jestjs.io/)
- [Pytest (Backend)](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Next.js Testing](https://nextjs.org/docs/testing)

---

## 다음 단계

### 즉시 실행 (1-2시간)
1. Frontend에 기본 테스트 1개 추가
2. Backend에 Health check 테스트 추가
3. CI에서 테스트 활성화 확인

### 단기 목표 (1주)
1. 각 서비스당 10개 이상 Unit Test
2. 주요 API Endpoint 테스트 커버리지 50%
3. CI/CD 파이프라인에 테스트 통합

### 장기 목표 (1개월)
1. 전체 커버리지 70% 달성
2. Integration Tests 추가
3. E2E Tests (Playwright/Cypress)

---

**작성자**: DevOps Team  
**검토**: 필요 시 업데이트
