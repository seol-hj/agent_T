# Documentation

Agent T 프로젝트 문서 모음입니다.

**최종 업데이트**: 2026-05-11  
**전체 문서 수**: 30개

---

## 🚀 빠른 시작

| 문서 | 설명 | 소요 시간 |
|------|------|-----------|
| **[../QUICKSTART.md](../QUICKSTART.md)** | 로컬 Docker Compose 테스트 | 5분 |
| **[../DEPLOYMENT.md](../DEPLOYMENT.md)** | AWS 배포 전체 가이드 | 30분 |
| **[bootstrap-checklist.md](./bootstrap-checklist.md)** | Bootstrap 스크립트 실행 가이드 | 30분 |

---

## 📊 프로젝트 현황

| 문서 | 설명 |
|------|------|
| **[CURRENT-STATUS.md](./CURRENT-STATUS.md)** ⭐ | 현재 완성도, 실행 대기 중인 작업, 다음 단계 |
| **[PROJECT-EVALUATION.md](./PROJECT-EVALUATION.md)** ⭐ | CLAUDE.md/README.md 대비 평가, 완성도 분석 |
| **[implementation-status.md](./implementation-status.md)** | 구현 완료/미완료 항목 상세 |

---

## 🏗️ 아키텍처 & 설계

### 시스템 구조
| 문서 | 설명 |
|------|------|
| **[architecture.md](./architecture.md)** | 전체 시스템 아키텍처 (7개 모듈) |
| **[services.md](./services.md)** | 각 서비스 API 명세 및 역할 |
| **[schemas-reference.md](./schemas-reference.md)** | Pydantic 스키마 레퍼런스 |

### 인프라 설계
| 문서 | 설명 |
|------|------|
| **[infrastructure.md](./infrastructure.md)** | AWS 인프라 구성 개요 |
| **[networking.md](./networking.md)** | VPC, Subnets, NAT Gateway |
| **[vpc-endpoints.md](./vpc-endpoints.md)** | VPC Endpoints 상세 (S3, ECR, Secrets Manager) |
| **[eks.md](./eks.md)** | EKS 클러스터 설정 |

---

## 🔧 구현 가이드

### 핵심 컴포넌트
| 문서 | 설명 |
|------|------|
| **[gateway-implementation.md](./gateway-implementation.md)** | LLM/Storage Gateway 추상화 |
| **[bedrock-implementation.md](./bedrock-implementation.md)** | Amazon Bedrock 연동 |
| **[orchestrator-implementation.md](./orchestrator-implementation.md)** | Pipeline 오케스트레이터 |

### 서비스별 구현
| 문서 | 설명 |
|------|------|
| **[frontend-implementation-guide.md](./frontend-implementation-guide.md)** | Next.js 14 Frontend |
| **[sumo-integration.md](./sumo-integration.md)** | SUMO 시뮬레이터 연동 |

---

## 🚢 배포 & 운영

### 배포
| 문서 | 설명 |
|------|------|
| **[deployment.md](./deployment.md)** | AWS 배포 전체 가이드 |
| **[bootstrap-checklist.md](./bootstrap-checklist.md)** | Bootstrap 자동화 체크리스트 |
| **[cicd.md](./cicd.md)** | GitHub Actions + Argo CD |
| **[gitops.md](./gitops.md)** | GitOps 전략 (Argo CD) |
| **[ssl-setup.md](./ssl-setup.md)** | HTTPS/SSL 인증서 설정 |

### 인프라 리소스
| 문서 | 설명 |
|------|------|
| **[ecr.md](./ecr.md)** | ECR 레지스트리 관리 |
| **[storage.md](./storage.md)** | S3 버킷 구성 |
| **[secrets.md](./secrets.md)** | Secrets Manager 사용법 |
| **[platform-components.md](./platform-components.md)** | ALB Controller, Argo CD |

### 모니터링 & 운영
| 문서 | 설명 |
|------|------|
| **[observability.md](./observability.md)** | Prometheus, Grafana, CloudWatch |
| **[testing.md](./testing.md)** | 테스트 전략 (Unit, Integration, E2E) |
| **[troubleshooting.md](./troubleshooting.md)** | 문제 해결 가이드 |

---

## 📖 참고 자료

### 프로젝트 규칙
| 문서 | 설명 |
|------|------|
| **[../CLAUDE.md](../CLAUDE.md)** | Claude Code를 위한 프로젝트 가이드라인 |
| **[contributing.md](./contributing.md)** | 개발 기여 가이드 |

---

## 🗂️ 문서 분류

### ⭐ 필수 읽기 (시작 전)
1. [../README.md](../README.md) - 프로젝트 개요
2. [CURRENT-STATUS.md](./CURRENT-STATUS.md) - 현재 상태
3. [bootstrap-checklist.md](./bootstrap-checklist.md) - 배포 가이드

### 📚 인프라 엔지니어용
- [infrastructure.md](./infrastructure.md)
- [networking.md](./networking.md)
- [eks.md](./eks.md)
- [cicd.md](./cicd.md)
- [troubleshooting.md](./troubleshooting.md)

### 👨‍💻 백엔드 개발자용
- [architecture.md](./architecture.md)
- [services.md](./services.md)
- [gateway-implementation.md](./gateway-implementation.md)
- [bedrock-implementation.md](./bedrock-implementation.md)
- [schemas-reference.md](./schemas-reference.md)

### 🎨 프론트엔드 개발자용
- [frontend-implementation-guide.md](./frontend-implementation-guide.md)
- [services.md](./services.md) (API 명세)
- [testing.md](./testing.md)

### 🔬 시뮬레이션 엔지니어용
- [sumo-integration.md](./sumo-integration.md)
- [orchestrator-implementation.md](./orchestrator-implementation.md)

---

## 📝 문서 작성 규칙

### 문서 구조
```markdown
# 제목

**최종 업데이트**: YYYY-MM-DD  
**대상 독자**: [인프라/백엔드/프론트엔드/전체]

---

## 개요
(1-2 문장 요약)

## 목차
...

## 상세 내용
...

## 참고 문서
- [관련 문서](./related.md)
```

### 파일명 규칙
- 소문자 + 하이픈 (kebab-case)
- 명확한 목적: `bootstrap-checklist.md` (O), `doc1.md` (X)
- 최대 30자 이내

### 업데이트 주기
- **CURRENT-STATUS.md**: 주요 변경 시마다
- **PROJECT-EVALUATION.md**: 월 1회
- 나머지: 관련 코드 변경 시

---

## 🗑️ Archive

더 이상 사용하지 않는 문서는 `../.archive/docs/`로 이동:
- deployment-architecture.md (CURRENT-STATUS.md와 중복)
- infra-vs-cicd-separation.md (cicd.md와 중복)
- external-access-setup.md (bootstrap-checklist.md에 통합)

**Archive 사유**: `../.archive/README.md` 참조

---

## 🔗 외부 링크

- **SUMO 공식 문서**: https://sumo.dlr.de/docs/
- **Amazon Bedrock**: https://docs.aws.amazon.com/bedrock/
- **Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/
- **Argo CD**: https://argo-cd.readthedocs.io/

---

**문서 관리자**: DevOps Team  
**문서 피드백**: GitHub Issues
