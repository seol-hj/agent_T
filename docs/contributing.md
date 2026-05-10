# 기여 가이드

AI Agent T 프로젝트에 기여해주셔서 감사합니다!

---

## 📋 목차

- [행동 강령](#행동-강령)
- [시작하기](#시작하기)
- [개발 프로세스](#개발-프로세스)
- [코딩 스타일](#코딩-스타일)
- [커밋 메시지](#커밋-메시지)
- [Pull Request](#pull-request)
- [문서 작성](#문서-작성)
- [테스트](#테스트)

---

## 행동 강령

### 우리의 약속

모든 기여자와 관리자는 다음을 준수합니다:
- 존중과 배려의 자세
- 건설적인 피드백
- 다양성과 포용성 존중
- 프로젝트 목표에 집중

---

## 시작하기

### 1. 저장소 Fork

```bash
# GitHub에서 Fork 버튼 클릭
# Fork한 저장소를 로컬에 클론
git clone https://github.com/YOUR_USERNAME/agent-t.git
cd agent-t

# Upstream 추가
git remote add upstream https://github.com/YOUR_ORG/agent-t.git
```

### 2. 개발 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 공통 라이브러리 설치
pip install -r libs/common/requirements.txt

# 개발 도구 설치
pip install black flake8 pytest pytest-cov

# Docker Compose로 서비스 실행
docker-compose up -d
```

### 3. 브랜치 생성

```bash
# 최신 코드 가져오기
git fetch upstream
git checkout main
git merge upstream/main

# Feature 브랜치 생성
git checkout -b feature/your-feature-name

# 또는 Bugfix 브랜치
git checkout -b bugfix/issue-123
```

---

## 개발 프로세스

### 1. Issue 확인

- 기존 Issue 확인: GitHub Issues에서 중복 확인
- 새 Issue 생성: 버그 리포트 또는 기능 요청

### 2. 코드 작성

```bash
# 변경사항 작성
vim apps/orchestrator/main.py

# 테스트 작성 (필수)
vim apps/orchestrator/tests/test_main.py

# 로컬 테스트
pytest apps/orchestrator/tests/ -v
```

### 3. 코드 스타일 검사

```bash
# Black 포맷터 (자동 수정)
black apps/orchestrator/

# Flake8 린터 (검사만)
flake8 apps/orchestrator/ --max-line-length=120

# Terraform 포맷
cd infra/terraform/envs/dev
terraform fmt
```

### 4. 테스트 실행

```bash
# 단위 테스트
pytest apps/orchestrator/tests/ -v

# 커버리지
pytest apps/orchestrator/tests/ --cov=apps.orchestrator --cov-report=html

# 통합 테스트 (Docker Compose)
docker-compose up -d
./scripts/test-services-local.sh
```

---

## 코딩 스타일

### Python (PEP 8)

```python
# Good
def process_user_request(user_request: str, experiment_id: str) -> dict:
    """
    사용자 요청 처리

    Args:
        user_request: 사용자 자연어 요청
        experiment_id: 실험 ID

    Returns:
        dict: 처리 결과
    """
    logger.info("Processing request", extra_fields={"experiment_id": experiment_id})
    result = orchestrator.parse(user_request)
    return result


# Bad
def processUserRequest(userRequest,experimentId):
    result=orchestrator.parse(userRequest)
    return result
```

### 주석 규칙

```python
# 한국어 우선 (국제화 시 영어 병기)
# Good
def calculate_kpi(data: list) -> dict:
    """KPI 계산 / Calculate KPI"""
    pass


# 복잡한 로직에만 주석 (명확한 코드는 주석 불필요)
# Good
# Bedrock API는 비동기 미지원 → ThreadPoolExecutor 사용
result = await loop.run_in_executor(None, bedrock_client.converse, ...)

# Bad
# 변수 선언 (불필요한 주석)
experiment_id = request.experiment_id
```

### Terraform

```hcl
# 리소스명: <project>-<env>-<resource>-<suffix>
resource "aws_s3_bucket" "scenarios" {
  bucket = "agent-t-dev-scenarios"
  
  tags = merge(local.base_tags, {
    Name = "agent-t-dev-scenarios"
    Type = "Scenarios"
  })
}

# 들여쓰기: 2 spaces
# 줄 길이: 120자
```

### YAML

```yaml
# 들여쓰기: 2 spaces
apiVersion: v1
kind: Service
metadata:
  name: orchestrator
  namespace: agent-t
  labels:
    app: orchestrator
    version: v1
spec:
  selector:
    app: orchestrator
  ports:
    - name: http
      port: 8001
      targetPort: 8001
```

---

## 커밋 메시지

### 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 스타일 (포맷팅, 세미콜론 등)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드, 설정 파일 수정
- `perf`: 성능 개선
- `ci`: CI 설정 수정

### Scope

- `orchestrator`, `scenario-builder`, `network-builder` 등 (서비스명)
- `terraform`, `helm`, `argocd` 등 (인프라)
- `gateway`, `db`, `observability` 등 (공통 라이브러리)

### 예시

```bash
# 좋은 예시
feat(orchestrator): LLM Gateway 통합 추가

- BedrockProvider를 통한 Claude 호출
- 프롬프트 버전 관리 기능
- LLM 메트릭 수집 (latency, token, cost)

Closes #42

# 나쁜 예시
update orchestrator
```

---

## Pull Request

### 1. Push

```bash
# 변경사항 커밋
git add .
git commit -m "feat(orchestrator): LLM Gateway 통합 추가"

# Fork한 저장소에 Push
git push origin feature/your-feature-name
```

### 2. PR 생성

GitHub에서 "New Pull Request" 클릭

**PR 템플릿**:

```markdown
## 변경 사항

- [ ] 새 기능 추가
- [ ] 버그 수정
- [ ] 리팩토링
- [ ] 문서 업데이트

## 설명

이 PR은 Orchestrator에 LLM Gateway를 통합합니다.

- BedrockProvider를 통한 Claude 호출
- 프롬프트 버전 관리
- LLM 메트릭 수집

## 관련 Issue

Closes #42

## 테스트

- [x] 단위 테스트 추가
- [x] 통합 테스트 확인
- [x] 로컬 환경에서 동작 확인

## 체크리스트

- [x] 코드 스타일 검사 (Black, Flake8)
- [x] 테스트 작성 및 통과
- [x] 문서 업데이트
- [x] 커밋 메시지 규칙 준수
```

### 3. 코드 리뷰

- 리뷰어 의견에 대응
- 필요 시 추가 커밋
- CI 통과 확인

### 4. Merge

- Squash and Merge (권장) - 커밋 히스토리 정리
- Rebase and Merge - 선형 히스토리 유지
- Merge Commit - 브랜치 히스토리 보존

---

## 문서 작성

### 문서 위치

- **루트**: README.md, QUICKSTART.md, CLAUDE.md
- **docs/**: 상세 가이드 (22개 파일)
- **서비스별**: apps/<service>/README.md

### 문서 구조

```markdown
# 제목

간단한 설명 (1-2문장)

---

## 개요

상세 설명

## 주요 내용

### 섹션 1

내용

### 섹션 2

내용

## 예시

\```bash
# 예시 코드
\```

## 참고

- [관련 문서](./link.md)
```

### 문서 업데이트

```bash
# 문서 수정
vim docs/architecture.md

# docs/README.md 인덱스 업데이트 (새 문서 추가 시)
vim docs/README.md

# 커밋
git add docs/
git commit -m "docs: architecture.md 업데이트"
```

---

## 테스트

### 단위 테스트

```python
# apps/orchestrator/tests/test_orchestrator.py
import pytest
from ..services.orchestrator_service import OrchestratorService


@pytest.fixture
def orchestrator_service():
    return OrchestratorService()


def test_parse_user_request(orchestrator_service):
    """사용자 요청 파싱 테스트"""
    request = "강남역 일대 교통량 20% 증가 시뮬레이션"
    result = orchestrator_service.parse(request)
    
    assert result is not None
    assert "location" in result
    assert result["location"] == "강남역"


def test_parse_empty_request(orchestrator_service):
    """빈 요청 처리 테스트"""
    with pytest.raises(ValueError):
        orchestrator_service.parse("")
```

### 통합 테스트

```python
# apps/orchestrator/tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from ..main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_orchestrator_endpoint(client):
    """Orchestrator API 엔드포인트 테스트"""
    response = client.post("/orchestrator/parse", json={
        "user_request": "강남역 일대 교통량 20% 증가 시뮬레이션"
    })
    
    assert response.status_code == 200
    assert "specification" in response.json()
```

### E2E 테스트

```bash
# scripts/test-e2e.sh
#!/bin/bash

# 서비스 시작
docker-compose up -d

# E2E 테스트
curl -X POST http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"user_request": "테스트", "experiment_id": "e2e_test", "dry_run": true}'

# 정리
docker-compose down
```

---

## 문제 해결

### CI 실패

```bash
# GitHub Actions 로그 확인
# → Repository → Actions → Failed Run

# 로컬에서 재현
docker-compose build
docker-compose up -d
pytest
```

### 코드 스타일 실패

```bash
# Black으로 자동 수정
black .

# Flake8 검사
flake8 . --max-line-length=120

# 재커밋
git add .
git commit --amend --no-edit
git push --force-with-lease
```

### Merge Conflict

```bash
# Upstream 최신 코드 가져오기
git fetch upstream
git rebase upstream/main

# 충돌 해결
vim <conflicted-file>
git add <conflicted-file>
git rebase --continue

# Force Push (주의: 자신의 브랜치만)
git push --force-with-lease origin feature/your-feature-name
```

---

## 질문 & 지원

### 커뮤니케이션

- **GitHub Issues**: 버그 리포트, 기능 요청
- **GitHub Discussions**: 질문, 아이디어 공유
- **Pull Request**: 코드 리뷰, 피드백

### 리소스

- [README.md](../README.md) - 프로젝트 개요
- [QUICKSTART.md](../QUICKSTART.md) - 빠른 시작
- [docs/README.md](./README.md) - 문서 인덱스
- [CLAUDE.md](../CLAUDE.md) - 프로젝트 컨텍스트

---

## 감사합니다!

여러분의 기여가 AI Agent T를 더 나은 프로젝트로 만듭니다.

**Happy Coding! 🚀**
