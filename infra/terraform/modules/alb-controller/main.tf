# ============================================================================
# module: alb-controller
# 책임: AWS Load Balancer Controller 설치 + IRSA + IAM Policy.
# 활성화 단계: 5
# 메모:
#   - NGINX Ingress 사용 금지 — 본 컨트롤러로 ALB/NLB 프로비저닝
#   - 공식 IAM 정책: https://github.com/kubernetes-sigs/aws-load-balancer-controller
#     → 모듈에 정책 JSON 또는 aws_iam_policy_document 로 동기화 (버전 핀)
#   - helm_release "aws-load-balancer-controller" (kube-system namespace)
#   - 활성화 전제: kubernetes / helm provider 활성화 + EKS OIDC provider 존재
# ============================================================================

# 구현은 5단계에서 추가된다.
