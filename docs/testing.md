# 서비스 테스트 가이드

Docker Compose로 실행 중인 서비스들의 기능 테스트 방법

---

## 🚀 빠른 테스트 (자동화 스크립트)

```bash
# 모든 서비스 기능 테스트 실행
./scripts/test-services-local.sh
```

이 스크립트는 다음을 테스트합니다:
- ✅ Health Check (5개 서비스)
- ✅ Ready Check (4개 서비스)
- ✅ 서비스 정보 조회
- ✅ 시나리오 빌드 (Agent Service)
- ✅ 네트워크 빌드 (Simulation Service)
- ✅ E2E 파이프라인 (Pipeline Service)

---

## 🔍 수동 테스트 (상세)

### 1. 서비스 상태 확인

```bash
# 모든 컨테이너 상태
docker-compose ps

# 로그 실시간 확인
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f agent-service
```

**예상 출력**: 모든 서비스가 `Up` 상태

---

### 2. Health Check

각 서비스가 정상적으로 응답하는지 확인:

```bash
# Agent Service
curl http://localhost:8001/health

# Simulation Service
curl http://localhost:8005/health

# Analysis Service
curl http://localhost:8006/health

# Report Service
curl http://localhost:8007/health

# Pipeline Service
curl http://localhost:8000/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "service": "agent-service",
  "timestamp": "2026-05-08T...",
  "version": "0.4.0"
}
```

---

### 3. Ready Check (Gateway 확인)

서비스가 의존성(Storage, LLM)과 연결되었는지 확인:

```bash
# Agent Service (LLM + Storage)
curl http://localhost:8001/ready | jq

# Simulation Service (Storage)
curl http://localhost:8005/ready | jq

# Analysis Service (Storage)
curl http://localhost:8006/ready | jq

# Report Service (LLM + Storage)
curl http://localhost:8007/ready | jq
```

**예상 응답**:
```json
{
  "status": "ready",
  "service": "agent-service",
  "dependencies": {
    "storage_gateway": "local",
    "llm_gateway": "local"
  }
}
```

---

### 4. 시나리오 빌드 테스트 (Agent Service)

자연어 요청을 구조화된 시나리오로 변환:

```bash
curl -X POST http://localhost:8001/scenario/build \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "강남역 일대 교통량 20% 증가 시뮬레이션",
    "experiment_id": "test-001"
  }' | jq
```

**예상 응답**:
```json
{
  "success": true,
  "scenario_id": "scenario-20260508-...",
  "scenario": {
    "location": {...},
    "parameters": {...}
  },
  "scenario_file_uri": "file://..."
}
```

---

### 5. 네트워크 빌드 테스트 (Simulation Service)

OSM → SUMO 네트워크 변환 (Placeholder 모드):

```bash
curl -X POST http://localhost:8005/network/build \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "test-001",
    "scenario_id": "scenario-001",
    "location": {
      "bbox": [126.9, 37.5, 127.0, 37.6]
    }
  }' | jq
```

**예상 응답**:
```json
{
  "success": true,
  "network_id": "network-20260508-...",
  "network_file_uri": "file://...",
  "edge_count": 3,
  "junction_count": 4,
  "traffic_light_count": 0
}
```

**참고**: SUMO가 설치되지 않은 경우 Placeholder 네트워크가 생성됩니다.

---

### 6. 수요 빌드 테스트 (Simulation Service)

교통 수요 생성 (Placeholder 모드):

```bash
curl -X POST http://localhost:8005/demand/build \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "test-001",
    "scenario_id": "scenario-001",
    "network_file_uri": "file:///data/networks/test-001/network.net.xml",
    "vehicle_count": 100,
    "duration_hours": 1.0
  }' | jq
```

**예상 응답**:
```json
{
  "success": true,
  "demand_id": "demand-20260508-...",
  "demand_file_uri": "file://...",
  "vehicle_count": 3,
  "route_count": 2
}
```

---

### 7. 시뮬레이션 실행 테스트 (Simulation Service)

SUMO 시뮬레이션 실행 (Placeholder 모드):

```bash
curl -X POST http://localhost:8005/simulation/run \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "test-001",
    "scenario_id": "scenario-001",
    "network_file_uri": "file:///data/networks/test-001/network.net.xml",
    "demand_file_uri": "file:///data/demands/test-001/demand.rou.xml",
    "duration_seconds": 3600,
    "use_placeholder": true
  }' | jq
```

**예상 응답**:
```json
{
  "success": true,
  "simulation_id": "sim-20260508-...",
  "status": "completed",
  "output_files": {
    "tripinfo": "file://...",
    "summary": "file://..."
  },
  "tripinfo_stats": {
    "completed_trips": 2,
    "avg_duration": 300.0,
    ...
  }
}
```

---

### 8. KPI 분석 테스트 (Analysis Service)

시뮬레이션 결과에서 KPI 추출:

```bash
curl -X POST http://localhost:8006/analysis/run \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "test-001",
    "scenario_id": "scenario-001",
    "simulation_id": "sim-001",
    "tripinfo_uri": "file:///data/simulations/test-001/tripinfo.xml",
    "summary_uri": "file:///data/simulations/test-001/summary.xml"
  }' | jq
```

**예상 응답**:
```json
{
  "success": true,
  "analysis_id": "analysis-20260508-...",
  "status": "completed",
  "kpis": {
    "tripinfo": {
      "completed_trips": 2,
      "avg_travel_time": 300.0,
      ...
    },
    "summary": {...},
    "derived": {
      "completion_rate": 1.0,
      "congestion_index": 0.1,
      ...
    }
  }
}
```

---

### 9. 리포트 생성 테스트 (Report Service)

KPI를 정책 리포트로 변환:

```bash
curl -X POST http://localhost:8007/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "test-001",
    "scenario_id": "scenario-001",
    "analysis_id": "analysis-001",
    "kpis": {
      "tripinfo": {"completed_trips": 100},
      "summary": {},
      "derived": {"completion_rate": 0.95}
    }
  }' | jq
```

**예상 응답**:
```json
{
  "success": true,
  "report_id": "report-20260508-...",
  "report": "# 교통 시뮬레이션 리포트\n\n...",
  "report_file_uri": "file://..."
}
```

---

### 10. E2E 파이프라인 테스트 (Pipeline Service)

전체 파이프라인 한 번에 실행 (Dry Run):

```bash
curl -X POST http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-req-001",
    "user_request": "서울 강남역 일대 교통 시뮬레이션. 차량 500대, 1시간 동안 시뮬레이션",
    "dry_run": true
  }' | jq
```

**예상 응답** (30-60초 소요):
```json
{
  "schema_version": "1.0",
  "execution_id": "exec-001",
  "request_id": "test-req-001",
  "experiment_id": "exp-001",
  "status": "completed",
  "steps": [
    {
      "step_name": "orchestrator",
      "status": "completed",
      "started_at": "2026-05-08T12:00:00",
      "completed_at": "2026-05-08T12:00:02",
      "duration_ms": 2000.0
    }
  ],
  "report_uri": "file:///data/reports/...",
  "started_at": "2026-05-08T12:00:00",
  "completed_at": "2026-05-08T12:05:00",
  "total_duration_ms": 300000.0
}
```

---

## 🐛 문제 해결

### 서비스가 응답하지 않는 경우

```bash
# 1. 컨테이너 상태 확인
docker-compose ps

# 2. 로그 확인
docker-compose logs <service-name>

# 3. 재시작
docker-compose restart <service-name>

# 4. 완전 재시작
docker-compose down
docker-compose up --build
```

### "Connection refused" 오류

```bash
# 서비스가 아직 시작 중일 수 있음
docker-compose ps

# 30초 정도 대기 후 재시도
sleep 30
curl http://localhost:8001/health
```

### Import 오류

```bash
# 완전히 재빌드
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

---

## 📊 성공 기준

### ✅ 모든 테스트 통과
- [ ] 5개 서비스 모두 Health Check 200 OK
- [ ] 4개 서비스 모두 Ready Check 200 OK (dependencies 정상)
- [ ] 시나리오 빌드 성공 (scenario_id 반환)
- [ ] 네트워크 빌드 성공 (network_id 반환)
- [ ] 수요 빌드 성공 (demand_id 반환)
- [ ] 시뮬레이션 실행 성공 (simulation_id 반환)
- [ ] KPI 분석 성공 (21가지 KPI 추출)
- [ ] 리포트 생성 성공 (Markdown 리포트 반환)
- [ ] E2E 파이프라인 성공 (전체 단계 완료)

### ⚠️ 알려진 제한사항

1. **SUMO 미설치**: Placeholder 모드로 동작 (테스트용 더미 데이터 생성)
2. **LLM Mock 모드**: 고정된 응답 반환 (실제 AI 생성 없음)
   - `LLM_PROVIDER=mock` 사용
   - Agent Service, Report Service에서 가짜 AI 응답
3. **Storage Local 모드**: `/data` 볼륨에 파일 저장 (S3 대신)

---

## 📝 다음 단계

테스트 통과 후:

1. **SUMO 실제 통합 테스트**:
   - SUMO 설치된 환경에서 `use_placeholder: false`로 실행
   - 실제 OSM 다운로드 및 네트워크 변환 확인

2. **프로덕션 배포**:
   - AWS EKS에 배포
   - Bedrock LLM으로 전환
   - S3 Storage로 전환

3. **성능 테스트**:
   - 대규모 시뮬레이션 (10,000+ 차량)
   - 동시 요청 테스트
   - 응답 시간 측정

---

**작성일**: 2026-05-08  
**버전**: 0.4.0
