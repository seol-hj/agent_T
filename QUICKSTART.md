# 빠른 시작 - 로컬 테스트

Docker Compose로 Agent T를 로컬에서 5분 안에 실행하는 가이드

---

## ✅ 사전 준비

필수 도구:
- **Docker Desktop** (또는 Docker Engine + Docker Compose)
- **Git**
- **curl** (테스트용)

---

## 🚀 1단계: 레포지토리 클론

```bash
git clone https://github.com/<your-org>/agent-t.git
cd agent-t
```

---

## 🐳 2단계: Docker Compose 실행

```bash
docker compose up --build
```

**첫 실행 시 5-10분 소요** (이미지 빌드):
- Python 의존성 설치
- Next.js 프론트엔드 빌드
- PostgreSQL 초기화

**실행 완료 로그**:
```
pipeline-1            | INFO:     Uvicorn running on http://0.0.0.0:8000
agent-service-1       | INFO:     Uvicorn running on http://0.0.0.0:8001
simulation-service-1  | INFO:     Uvicorn running on http://0.0.0.0:8005
analysis-service-1    | INFO:     Uvicorn running on http://0.0.0.0:8006
report-service-1      | INFO:     Uvicorn running on http://0.0.0.0:8007
frontend-1            | ✓ Ready in 2.3s
postgres-1            | database system is ready to accept connections
```

---

## 🌐 3단계: 프론트엔드 접속

브라우저에서 접속:
```
http://localhost:3000
```

**화면 구성**:
- 홈: "New Experiment" 버튼
- 실험 생성 페이지: 자연어 입력 + 예제
- 실행 모니터링 페이지: 실시간 진행률 (2초마다 업데이트)
- 결과 페이지: KPI 및 리포트

**테스트 시나리오**:
1. "New Experiment" 버튼 클릭
2. 예제 중 하나 선택 또는 직접 입력:
   - "서울 강남역 일대 교통 시뮬레이션"
   - "강남역 일대 교통량 20% 증가 시 영향 분석"
3. "Start Simulation" 버튼 클릭
4. 자동으로 실행 모니터링 페이지로 이동
5. 6개 단계가 순차적으로 진행되는 것을 확인:
   - ✓ Scenario Building
   - ✓ Network Building
   - ✓ Demand Building
   - ✓ Simulation Running
   - ✓ Analysis
   - ✓ Report Generation

---

## 🧪 4단계: CLI 테스트 (선택 사항)

별도 터미널에서 테스트 스크립트 실행:

```bash
./scripts/test-services-local.sh
```

**테스트 항목**:
```
1. Health Check 테스트
✓ Agent Service (/health)
✓ Simulation Service (/health)
✓ Analysis Service (/health)
✓ Report Service (/health)
✓ Pipeline Service (/health)

2. Ready Check 테스트
✓ Agent Service (/ready)
✓ Simulation Service (/ready)
...

3. 서비스 정보 조회
✓ Agent Service (/)
✓ Simulation Service (/)
...

4. 시나리오 빌드 테스트
✓ POST /scenario/build (200 OK)

5. 네트워크 빌드 테스트
✓ POST /network/build (200 OK)
   ℹ️  Placeholder mode (SUMO not installed)

6. E2E 파이프라인 테스트
✓ Pipeline started (execution_id: exec-20260510-...)
✓ Progress API working

========================================
총 테스트: 15
성공: 15
실패: 0
✓ 모든 테스트 통과!
```

---

## 📊 5단계: 로그 확인

전체 로그 보기:
```bash
docker compose logs -f
```

특정 서비스 로그만 보기:
```bash
docker compose logs -f pipeline
docker compose logs -f agent-service
docker compose logs -f simulation-service
```

---

## 🛑 서비스 종료

```bash
# Ctrl+C로 중지 후
docker compose down

# 볼륨까지 삭제 (DB 초기화)
docker compose down -v
```

---

## 🔍 로컬 환경 상세

### 실행 중인 서비스

| 서비스 | 포트 | 설명 |
|--------|------|------|
| **frontend** | 3000 | Next.js 14 웹 UI |
| **pipeline** | 8000 | E2E 파이프라인 오케스트레이터 |
| **agent-service** | 8001 | AI 에이전트 (MockLLM) |
| **simulation-service** | 8005 | SUMO 시뮬레이션 (Placeholder) |
| **analysis-service** | 8006 | KPI 분석 |
| **report-service** | 8007 | 리포트 생성 (MockLLM) |
| **postgres** | 5432 | PostgreSQL 15 (실행 상태 추적) |

### 환경 설정

**LLM Provider**: MockLLMProvider
- 하드코딩된 응답 반환
- 실제 AI 호출 없음 (비용 없음)
- `libs/common/gateways/llm.py` 참고

**Storage Provider**: LocalStorageGateway
- 파일을 `/data` 볼륨에 저장
- Docker 볼륨: `storage-data`
- 컨테이너 내부 경로: `/data`

**Database**: PostgreSQL 15
- Docker 볼륨: `postgres-data`
- 데이터베이스: `agent_t_db`
- 사용자: `agent_t` / 비밀번호: `dev_password`
- 테이블: `pipeline_executions` (실행 이력 및 상태)

**SUMO 시뮬레이션**: Placeholder 모드
- SUMO가 설치되지 않음 (Docker 이미지 경량화)
- Placeholder 네트워크/수요/결과 생성
- 실제 시뮬레이션 대신 더미 데이터 반환

---

## 🐛 문제 해결

### 포트 충돌

**증상**: "bind: address already in use"

**해결**:
```bash
# 사용 중인 포트 확인
lsof -i :3000
lsof -i :8000

# 해당 프로세스 종료 또는 다른 포트 사용
# docker-compose.yaml 수정:
# ports:
#   - "3001:3000"  # 호스트 포트 변경
```

### Docker 메모리 부족

**증상**: 서비스가 재시작을 반복하거나 OOM 에러

**해결**:
```bash
# Docker Desktop 설정 → Resources → Memory를 8GB 이상으로 증가
```

### 프론트엔드 빌드 실패

**증상**: `frontend-1 exited with code 1`

**해결**:
```bash
# 캐시 없이 재빌드
docker compose build --no-cache frontend
docker compose up frontend
```

### PostgreSQL 연결 실패

**증상**: `pipeline-1 | ERROR: could not connect to server`

**해결**:
```bash
# PostgreSQL이 완전히 시작될 때까지 대기 (30초 정도)
# 또는 재시작
docker compose restart postgres
docker compose restart pipeline
```

### 진행률 조회 실패

**증상**: 프론트엔드에서 "진행률 조회 실패" 메시지

**확인**:
1. Pipeline 로그 확인: `docker compose logs pipeline | grep execution`
2. 브라우저 콘솔(F12) 확인: Network 탭에서 API 호출 상태
3. PostgreSQL 연결 확인: `docker compose logs postgres`

**해결**:
```bash
# 전체 재시작
docker compose down
docker compose up --build
```

---

## ⏭️ 다음 단계

로컬 테스트가 완료되었다면:

### AWS 배포로 이동
📖 **[DEPLOYMENT.md](./DEPLOYMENT.md)** - AWS EKS + RDS + S3 + Bedrock

**차이점**:
- MockLLM → Amazon Bedrock (실제 AI)
- LocalStorage → S3 (영구 저장)
- Placeholder SUMO → 실제 SUMO 설치 (선택)
- Docker Compose → Kubernetes (EKS)

### 개발 참여
📖 **[docs/contributing.md](./docs/contributing.md)** - 개발 기여 가이드

---

## 📚 참고 문서

- **[README.md](./README.md)** - 프로젝트 개요
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - AWS 배포
- **[docs/architecture.md](./docs/architecture.md)** - 아키텍처 상세
- **[docs/troubleshooting.md](./docs/troubleshooting.md)** - 문제 해결

---

**작성일**: 2026-05-10  
**버전**: 0.4.0
