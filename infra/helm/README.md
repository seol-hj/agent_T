# infra/helm

서비스별 Helm 차트. **Argo CD가 이 디렉터리를 동기화 소스로 본다.**

## 예정 구조

```
helm/
├── api-service/
├── agent-service/
├── simulation-service/
├── analysis-service/
├── report-service/
└── frontend/
```

각 차트:

```
<service>/
├── Chart.yaml
├── values.yaml          # 기본값
├── values-dev.yaml      # dev 오버라이드
├── values-prod.yaml     # prod 오버라이드
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml     # api-service 만 (ALB)
    ├── hpa.yaml
    ├── serviceaccount.yaml  # IRSA
    └── _helpers.tpl
```

## 원칙

- **이미지 태그는 명시적 버전** (`latest` 금지)
- 환경별 차이는 `values-<env>.yaml` 오버라이드로만 표현
- 시크릿은 차트에 평문 저장 금지 — Secrets Manager + External Secrets Operator 또는 IRSA 경유
- ALB Ingress는 `api-service`에만 (그 외는 ClusterIP)
- HPA/PDB는 production 워크로드에 기본 적용

7단계에서 구체화.
