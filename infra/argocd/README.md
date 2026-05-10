# infra/argocd

Argo CD **Application / AppProject** 매니페스트. App-of-Apps 패턴으로 관리.

## 예정 구조

```
argocd/
├── projects/
│   └── agent-t.yaml             # AppProject (소스/대상 제한)
├── applications/
│   ├── root.yaml                # App-of-Apps 진입점
│   ├── api-service.yaml
│   ├── agent-service.yaml
│   ├── simulation-service.yaml
│   ├── analysis-service.yaml
│   ├── report-service.yaml
│   └── frontend.yaml
└── README.md
```

## GitOps 흐름

1. 개발자 PR 머지 → GitHub Actions가 이미지 빌드 + ECR push
2. Actions가 `infra/helm/<service>/values-<env>.yaml`의 `image.tag`를 새 SHA로 갱신 + commit
3. Argo CD가 변경 감지 → 클러스터에 자동 동기화 (또는 Manual sync 정책)

자세한 흐름은 [`docs/cicd.md`](../../docs/cicd.md) 참조.

7단계에서 구체화.
