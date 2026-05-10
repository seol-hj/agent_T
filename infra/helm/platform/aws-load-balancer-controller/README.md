# AWS Load Balancer Controller

EKS 클러스터에서 AWS ALB/NLB를 Ingress로 관리하는 컨트롤러.

---

## 개요

AWS Load Balancer Controller는 Kubernetes Ingress 리소스를 AWS Application Load Balancer (ALB)로 자동 프로비저닝한다.

- **Helm Chart**: https://github.com/aws/eks-charts/tree/master/stable/aws-load-balancer-controller
- **버전**: v2.7.1

---

## 설치

### 1. Terraform으로 IRSA 권한 생성

먼저 Terraform으로 IAM Role (IRSA)을 생성해야 한다.

```hcl
# infra/terraform/envs/dev/main.tf
module "irsa" {
  source = "../../modules/iam-irsa"

  # ...

  service_accounts = {
    aws-load-balancer-controller = {
      namespace       = "kube-system"
      service_account = "aws-load-balancer-controller"
      policy_arns     = [aws_iam_policy.alb_controller.arn]
    }
  }
}

# ALB Controller IAM Policy
resource "aws_iam_policy" "alb_controller" {
  name        = "${var.project_name}-${var.env}-alb-controller-policy"
  description = "IAM policy for AWS Load Balancer Controller"

  policy = file("${path.module}/policies/alb-controller-policy.json")
}
```

IAM Policy JSON은 공식 문서에서 다운로드:
```bash
curl -o alb-controller-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json
```

### 2. Bootstrap 스크립트로 설치

```bash
# dev 환경
./scripts/install-platform.sh dev alb

# prod 환경
./scripts/install-platform.sh prod alb
```

### 3. 수동 설치 (Helm)

```bash
# Helm Repo 추가
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# 설치
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --values values-dev.yaml \
  --wait
```

---

## Values 파일 커스터마이징

### values-dev.yaml

주요 설정:
- `clusterName`: EKS 클러스터 이름 (`agent-t-dev-eks`)
- `vpcId`: VPC ID (자동으로 설정됨)
- `serviceAccount.annotations.eks.amazonaws.com/role-arn`: IRSA Role ARN
- `replicaCount`: 1 (dev는 단일 replica)
- `logLevel`: debug

### values-prod.yaml

주요 설정:
- `replicaCount`: 2 (고가용성)
- `logLevel`: info
- `enableShield`: true (DDoS 보호)
- `enableWafv2`: true (WAF 연동)
- `affinity`: Pod Anti-Affinity (다른 노드에 배치)
- `priorityClassName`: system-cluster-critical

---

## IngressClass 설정

ALB Controller가 처리할 IngressClass 정의:

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: alb
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"
spec:
  controller: ingress.k8s.aws/alb
```

확인:
```bash
kubectl get ingressclass
```

---

## Ingress 예시

### 기본 Ingress (HTTP)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-service
  namespace: default
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
spec:
  ingressClassName: alb
  rules:
  - host: api.dev.agent-t.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
```

### HTTPS Ingress (ACM 인증서)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-service
  namespace: default
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:123456789012:certificate/abc123
spec:
  ingressClassName: alb
  rules:
  - host: api.dev.agent-t.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
```

---

## 주요 Annotations

| Annotation | 설명 | 예시 |
|---|---|---|
| `alb.ingress.kubernetes.io/scheme` | ALB 타입 (internet-facing / internal) | `internet-facing` |
| `alb.ingress.kubernetes.io/target-type` | 타겟 타입 (ip / instance) | `ip` |
| `alb.ingress.kubernetes.io/listen-ports` | 리스너 포트 | `[{"HTTP": 80}, {"HTTPS": 443}]` |
| `alb.ingress.kubernetes.io/certificate-arn` | ACM 인증서 ARN | `arn:aws:acm:...` |
| `alb.ingress.kubernetes.io/ssl-redirect` | HTTP → HTTPS 리다이렉트 | `'443'` |
| `alb.ingress.kubernetes.io/healthcheck-path` | Health check 경로 | `/health` |
| `alb.ingress.kubernetes.io/backend-protocol` | 백엔드 프로토콜 | `HTTP` |
| `alb.ingress.kubernetes.io/subnets` | ALB 서브넷 (public subnet) | `subnet-xxx, subnet-yyy` |
| `alb.ingress.kubernetes.io/tags` | ALB 태그 | `Environment=dev,Team=platform` |
| `alb.ingress.kubernetes.io/wafv2-acl-arn` | WAF ACL ARN | `arn:aws:wafv2:...` |

전체 목록: https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/

---

## 확인

### 1. Controller Pod 확인
```bash
kubectl get deployment aws-load-balancer-controller -n kube-system
kubectl logs -f deployment/aws-load-balancer-controller -n kube-system
```

### 2. IngressClass 확인
```bash
kubectl get ingressclass
```

### 3. Ingress 확인
```bash
kubectl get ingress -A
kubectl describe ingress <ingress-name> -n <namespace>
```

### 4. ALB 확인 (AWS Console)
```bash
aws elbv2 describe-load-balancers --query "LoadBalancers[?contains(LoadBalancerName, 'k8s')]"
```

---

## 문제 해결

### Controller Pod가 시작 안 됨

**확인**:
```bash
kubectl describe pod -l app.kubernetes.io/name=aws-load-balancer-controller -n kube-system
kubectl logs -l app.kubernetes.io/name=aws-load-balancer-controller -n kube-system
```

**원인 1**: IRSA 권한 부족
- ServiceAccount annotation 확인: `kubectl get sa aws-load-balancer-controller -n kube-system -o yaml`
- IAM Policy 확인

**원인 2**: VPC ID 미설정
- `values.yaml`에서 `vpcId` 확인

### Ingress가 ALB로 생성 안 됨

**확인**:
```bash
kubectl describe ingress <ingress-name>
kubectl logs -f deployment/aws-load-balancer-controller -n kube-system
```

**원인 1**: IngressClass 지정 안 됨
- `spec.ingressClassName: alb` 추가

**원인 2**: Subnet 태그 누락
- Public subnet에 태그 필요:
  - `kubernetes.io/role/elb = 1`

---

## 참고

- [공식 문서](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Ingress Annotations](https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/)
- [IAM Policy](https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json)
