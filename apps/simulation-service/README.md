# simulation-service

**Network Builder + Demand Builder + Simulator Runner**가 동작하는 시뮬레이션 실행 서비스.

## 책임

- OSM → SUMO 도로망(`.net.xml`) 생성
- 통행 수요/패턴(`.rou.xml`) 생성
- SUMO 시뮬레이션 실행 및 산출물 수집
- 산출물(raw 데이터)을 S3에 업로드 (Storage Provider 경유)

## 책임 외

- 시나리오 명세 결정 (Agent로 위임됨 — 입력으로 받음)
- KPI 추출/분석 (`analysis-service`로)

## 의존

- SUMO 바이너리 (컨테이너 이미지에 포함)
- OSM 데이터 소스 (Overpass API 또는 사전 다운로드 PBF)
- Storage Provider (S3)
- Common Schema

## 운영 특성

- **CPU/메모리 집약적** — 별도 노드그룹/HPA 정책 필요할 수 있음
- 장시간 실행되는 작업 → Job/Argo Workflows 패턴 검토
- 산출물 크기 큼 → 임시 EBS + S3 업로드

## 미결 사항

- 실행 모델: Pod 내 직접 실행 vs Kubernetes Job 위임
- SUMO 버전 핀

## 배포

- Helm chart: `infra/helm/simulation-service/`
