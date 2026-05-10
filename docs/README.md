# 문서 디렉토리

Agent T 프로젝트의 상세 문서

---

## 📚 문서 목록

### 시스템 설계
- **[architecture.md](./architecture.md)** - 전체 시스템 아키텍처, 데이터 흐름
- **[services.md](./services.md)** - 각 마이크로서비스 상세 설명 및 API 명세

### 인프라 & 배포
- **[infrastructure.md](./infrastructure.md)** - AWS 인프라 구성 (VPC, EKS, RDS, S3)
- **[cicd.md](./cicd.md)** - CI/CD 파이프라인 (GitHub Actions + Argo CD)
- **[networking.md](./networking.md)** - 네트워크 구성 및 VPC Endpoints
- **[observability.md](./observability.md)** - 모니터링 및 로깅 (CloudWatch, Prometheus)

### 구현 가이드
- **[gateway-implementation.md](./gateway-implementation.md)** - LLM/Storage Gateway 추상화 계층
- **[sumo-integration.md](./sumo-integration.md)** - SUMO 시뮬레이터 통합 방법
- **[frontend-implementation-guide.md](./frontend-implementation-guide.md)** - Next.js 프론트엔드 구현

### 운영
- **[troubleshooting.md](./troubleshooting.md)** - 문제 해결 가이드
- **[secrets.md](./secrets.md)** - 비밀 관리 (AWS Secrets Manager)
- **[contributing.md](./contributing.md)** - 개발 기여 가이드

---

## 🚀 빠른 링크

### 처음 시작하는 경우
1. [프로젝트 개요](../README.md)
2. [로컬 테스트](../QUICKSTART.md)
3. [AWS 배포](../DEPLOYMENT.md)

### 개발에 참여하는 경우
1. [아키텍처 이해](./architecture.md)
2. [서비스 API 명세](./services.md)
3. [기여 가이드](./contributing.md)
4. [GitHub 전략](../GITHUB_STRATEGY.md)

### 문제가 발생한 경우
1. [문제 해결 가이드](./troubleshooting.md)
2. [GitHub Issues](https://github.com/<your-org>/agent-t/issues)

---

## 📝 문서 작성 가이드

새 문서를 추가할 때:

1. **위치**: 적절한 카테고리 선택 (시스템 설계/인프라/구현/운영)
2. **형식**: Markdown 사용, 명확한 제목 구조
3. **내용**: 
   - 목적과 범위 명시
   - 코드 예제 포함
   - 다이어그램 활용 (Mermaid 또는 이미지)
4. **업데이트**: 이 README.md에 링크 추가

---

**최종 업데이트**: 2026-05-11
