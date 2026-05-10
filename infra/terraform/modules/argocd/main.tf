# ============================================================================
# module: argocd
# 책임: Argo CD Helm release 설치 + 초기 AppProject (root).
# 활성화 단계: 5
# 메모:
#   - helm_release "argo-cd" 로 설치 (community chart, 명시적 버전 핀)
#   - 활성화 전제: kubernetes / helm provider 가 envs/<env>/providers.tf 에서 활성화
#   - 초기 admin password 는 secret 으로 자동 생성 → 사용자가 즉시 회전
#   - 외부 노출은 ALB Ingress (alb-controller 모듈 동작 후 별도 manifest)
#   - GitHub repo 자격증명 / private repo 연결은 GitOps 매니페스트(infra/argocd/) 로
# ============================================================================

# 구현은 5단계에서 추가된다.
