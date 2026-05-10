# scripts

로컬/CI 환경에서 사용하는 헬퍼 스크립트.

| 스크립트 | 용도 |
|---|---|
| `bootstrap-dev.sh`    | 개발자 머신 초기화 (도구 설치 안내, pre-commit, kubectl context 등) |
| `check-env.sh`        | 필수 도구·버전·자격증명 점검 |
| `sync-kubeconfig.sh`  | EKS kubeconfig를 로컬에 갱신 |

## 작성 원칙

- 모든 스크립트는 `set -euo pipefail`
- POSIX bash 가정 (macOS/Linux/WSL2 호환)
- 부작용이 있는 작업은 항상 사용자 확인 거침
- 실패 시 명확한 메시지로 종료

현재는 placeholder. 각 단계가 진행되면서 실제 로직으로 채워진다.
