# Archive 색인

이 문서는 `.archive/` 디렉토리에 보관된 파일들의 목록과 보관 이유를 설명합니다.

---

## `.archive/docs-old-fixes/` - 과거 트러블슈팅 문서

**보관 이유**: 2026-05-11에 발생한 이슈들의 수정 과정을 기록한 문서들. 현재는 모두 해결되어 더이상 참조 불필요.

| 파일명 | 내용 | 보관일 |
|---|---|---|
| `FINAL-FIX-SUMMARY-2026-05-11.md` | 최종 수정 요약 | 2026-05-11 |
| `bootstrap-ingress-fix.md` | Ingress 설정 수정 | 2026-05-11 |
| `root-cause-libs-ci-fix.md` | libs/** CI path 누락 수정 | 2026-05-11 |
| `runtime-errors-fix-2026-05-11.md` | Runtime 오류 수정 | 2026-05-11 |
| `ci-fixes-2026-05-11-final.md` | CI 최종 수정 | 2026-05-11 |
| `ci-fixes-2026-05-11.md` | CI 중간 수정 | 2026-05-11 |
| `ci-fixes-final-2026-05-11.md` | CI 최종 수정 (중복) | 2026-05-11 |
| `CHANGES-2026-05-11-gitops.md` | GitOps 변경 사항 | 2026-05-11 |
| `CHANGES-2026-05-11.md` | 일반 변경 사항 | 2026-05-11 |
| `CURRENT-STATUS.md` | 임시 상태 문서 | 2026-05-11 |
| `implementation-status.md` | 임시 구현 상태 | 2026-05-11 |

**참조**: 이슈 해결 방법은 현재 `docs/troubleshooting.md`에 통합되어 있습니다.

---

## `.archive/k8s-old/` - 레거시 Kubernetes Manifests

**보관 이유**: 초기 개발 시 사용했던 raw Kubernetes manifests. 현재는 Helm Charts로 완전히 대체됨.

### `/apps/` - 레거시 애플리케이션 manifests

| 파일명 | 내용 | 대체 경로 |
|---|---|---|
| `analyzer.yaml` | Analysis Service | `infra/helm/services/analysis-service/` |
| `demand-builder.yaml` | Demand Builder (통합됨) | `infra/helm/services/simulation-service/` |
| `orchestrator.yaml` | Orchestrator (통합됨) | `infra/helm/services/agent-service/` |
| `pipeline.yaml` | Pipeline Service | `infra/helm/services/api-service/` |
| `reporter.yaml` | Report Service | `infra/helm/services/report-service/` |
| `scenario-builder.yaml` | Scenario Builder (통합됨) | `infra/helm/services/agent-service/` |
| `simulator-runner.yaml` | Simulator Runner (통합됨) | `infra/helm/services/simulation-service/` |

**주의**: 일부 파일에 `:latest` 태그가 사용되어 있으나, 현재 미사용이므로 문제없음.

### `/monitoring/` - 레거시 모니터링 manifests

| 파일명 | 내용 | 비고 |
|---|---|---|
| `prometheus-placeholder.yaml` | Prometheus placeholder | 미구현 상태로 보관 |

### `/rbac/` - 레거시 RBAC 설정

| 파일명 | 내용 | 대체 경로 |
|---|---|---|
| `sumo-runner.yaml` | SUMO Runner RBAC | Helm Chart에 통합됨 |

---

## `.archive/k8s-kustomize/` - Kustomize 실험

**보관 이유**: Kustomize 방식을 시도했으나 Helm으로 전환.

| 파일명 | 내용 | 보관일 |
|---|---|---|
| `frontend.yaml` | Frontend Kustomize 설정 | 알 수 없음 |

---

## `.archive/workflows/` - 레거시 CI Workflows

**보관 이유**: 초기 CI workflow 시도. 현재는 `.github/workflows/`의 재사용 가능한 워크플로우로 대체됨.

| 파일명 | 내용 | 대체 파일 |
|---|---|---|
| `ci-simulation-runner.yml` | Simulation Runner CI | `.github/workflows/ci-simulation-service.yml` |

---

## 복원 방법

만약 과거 파일이 필요하다면:

```bash
# 특정 파일 복원
cp .archive/docs-old-fixes/FINAL-FIX-SUMMARY-2026-05-11.md docs/

# 전체 디렉토리 복원
cp -r .archive/k8s-old/apps k8s/
```

---

## 보관 정책

1. **문서**: 3개월 후 완전 삭제 고려
2. **코드**: 6개월 후 Git history에서만 참조
3. **설정 파일**: 1년 보관 후 삭제

---

## 관련 문서

- `docs/ARCHITECTURE-COMPLIANCE.md` - 현재 아키텍처 준수 상태
- `docs/troubleshooting.md` - 통합된 트러블슈팅 가이드
- `infra/helm/` - 현재 사용 중인 Helm Charts

---

**마지막 업데이트**: 2026-05-11  
**관리자**: Claude Code
