# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**AI Agent T** — AI 에이전트 기반 교통 시뮬레이션 지능화 플랫폼.

- 사용자의 자연어 교통 시뮬레이션 요구사항을 AI Agent가 해석
- 실험 명세 생성 → OpenStreetMap 도로망 + SUMO 시뮬레이터로 자동 실행
- 결과 KPI 분석 후 정책 리포트 생성

현재 저장소는 비어 있으며, 단계별로 코드/IaC/문서를 구축해 나간다.

## 핵심 모듈 (7개)

각 모듈은 **명확한 입출력 스키마**를 가지고 독립적으로 동작한다.

1. **Orchestrator** — 전체 흐름 제어, Agent 호출, 모듈 간 라우팅
2. **Scenario Builder** — 자연어 요구사항 → 실험 명세(JSON/YAML)
3. **Network Builder** — OSM → SUMO 도로망(`.net.xml`)
4. **Demand Builder** — 교통 수요/통행 패턴(`.rou.xml`) 생성
5. **Simulator Runner** — SUMO 실행 및 산출물 수집
6. **Analyzer** — KPI 추출 및 통계 분석
7. **Reporter** — 정책적 리포트 생성

## 책임 분리 (반드시 지킬 것)

- **LLM**: 판단(judgment), 계획(planning), 자연어 ↔ 명세 변환
- **코드**: 검증(validation), 변환(transformation), 파일 생성, 실행, 저장
- **SUMO**: 교통 시뮬레이션 계산

LLM에게 결정론적 계산(수치 분석, XML 생성, 파일 IO)을 시키지 말 것. 코드에게 정책적 판단(어떤 시나리오가 합리적인가)을 시키지 말 것.

## 인프라 결정 사항 (논의 끝났음 — 재논의 금지)

| 영역 | 선택 | 비고 |
|---|---|---|
| IaC | **Terraform** | AWS 리소스 전부 |
| 오케스트레이션 | **EKS** | |
| Ingress | **AWS Load Balancer Controller + ALB** | NGINX Ingress 사용 금지 |
| 네트워크 | **VPC Endpoint 적극 활용** | S3/ECR/Secrets Manager 등 PrivateLink |
| CI | **GitHub Actions** | |
| CD/GitOps | **Argo CD** | |
| 스토리지/DB | **S3, RDS PostgreSQL, Redis(ElastiCache)** | |
| 컨테이너 레지스트리 | **ECR** | |
| 비밀 관리 | **AWS Secrets Manager** | Git 커밋 금지 |
| LLM | **Amazon Bedrock** | 직접 호출 금지 — **LLM Gateway 경유 필수** |

### 추상화 원칙

향후 교체를 전제로 **Provider/Gateway** 계층을 둔다:

- LLM Gateway → Bedrock / Local LLM / fine-tuned model 교체 가능
- Vector DB Provider → 다른 vector DB로 교체 가능
- Storage Provider → 다른 storage로 교체 가능

비즈니스 로직은 AWS SDK를 직접 import하지 않는다. 항상 Gateway/Provider 인터페이스를 거친다.

## 운영 규칙

- **`latest` 태그 사용 금지** — 이미지/차트 모두 명시적 버전 핀
- **Secret은 Git에 저장 금지** — `.env.example`, Secrets Manager 참조만
- **재현성**: 다른 머신에서 `git clone` + `terraform apply` + bootstrap 스크립트로 환경 재구축이 가능해야 함
- **모든 주요 구성은 문서화** — 결정 사항은 `docs/` 또는 모듈별 README에

## 작업 진행 방식 (단계별)

사용자는 단계별로 코드를 추가한다. 각 단계마다 다음 형식을 따른다:

1. **현재 구조 분석** — 무엇이 존재하고 무엇이 빠져 있는지
2. **파일 생성/수정** — 변경 사항을 명시
3. **실행 방법** — 어떻게 실행/배포하는지
4. **테스트 방법** — 어떻게 검증하는지
5. **다음 단계로의 인계** — 이어가기 좋은 상태로 정리

## 명령어 / 빌드 / 테스트

> 아직 구현되지 않았다. 단계가 진행되면서 이 섹션을 갱신한다.
> 새 도구나 명령이 추가될 때마다 이 영역에 반영할 것.

## 참고

- 사용자는 한국어로 소통한다 — 응답/문서/주석 모두 한국어 우선
- 시니어 아키텍트 시점에서 트레이드오프를 명시하고, 결정 근거를 남긴다
