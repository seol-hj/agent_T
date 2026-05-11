# 런타임 오류 수정 - 2026-05-11

## 발견된 오류

### 오류 1: Backend 서비스 - `Retriever` not defined
```python
NameError: name 'Retriever' is not defined
  File "/app/libs/common/__init__.py", line 56, in <module>
    def get_rag_retriever() -> Retriever:
```

**영향받는 서비스**:
- agent-service
- analysis-service
- report-service
- simulation-service

**원인**: 
- `libs/common/__init__.py`에서 `Retriever` import가 주석 처리됨 (Line 13)
- 하지만 타입 힌트로 사용됨 (Line 56)

---

### 오류 2: Frontend - 존재하지 않는 이미지 태그
```
Failed to pull image: sha-a1b2c3d
ImagePullBackOff
```

**원인**: 
- `values-dev.yaml`의 이미지 태그가 `sha-a1b2c3d` (존재하지 않음)
- ECR에는 `sha-ce604f5`, `sha-5647b60`만 존재

---

## 해결 방법

### 1. libs/common/__init__.py 수정

#### Before (오류 발생)
```python
import os
from typing import Optional

# from .rag import Retriever  # 주석 처리됨

def get_rag_retriever() -> Retriever:  # ❌ NameError!
    ...
```

#### After (수정)
```python
import os
from typing import Optional, TYPE_CHECKING

# TYPE_CHECKING을 사용하여 타입 힌트만 import (런타임 에러 방지)
if TYPE_CHECKING:
    from .rag import Retriever  # type: ignore

def get_rag_retriever() -> "Retriever":  # type: ignore  # ✅ 문자열 리터럴
    ...
```

**설명**:
- `TYPE_CHECKING`: 타입 체커만 실행 시 True, 런타임에는 False
- 문자열 리터럴 타입 힌트: Python이 런타임에 평가하지 않음
- `# type: ignore`: mypy 경고 무시

---

### 2. Frontend 이미지 태그 수정

#### Before
```yaml
image:
  repository: 190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/frontend
  tag: "sha-a1b2c3d"  # ❌ 존재하지 않음
```

#### After
```yaml
image:
  repository: 190484841865.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/frontend
  tag: "sha-ce604f5"  # ✅ ECR에 존재
```

---

## 적용 방법

### 1단계: gitops/dev에 직접 Push (완료 ✅)

```bash
# gitops/dev 브랜치로 전환
git checkout gitops/dev
git pull origin gitops/dev

# 수정
# - libs/common/__init__.py
# - infra/helm/services/frontend/values-dev.yaml

# Commit & Push
git add libs/common/__init__.py infra/helm/services/frontend/values-dev.yaml
git commit -m "fix: resolve runtime errors"
git push origin gitops/dev
```

---

### 2단계: Argo CD 수동 동기화 (완료 ✅)

```bash
for app in frontend api-service agent-service analysis-service report-service simulation-service; do
  kubectl patch application $app -n argocd \
    --type merge \
    -p '{"operation":{"sync":{"revision":"gitops/dev"}}}'
done
```

---

### 3단계: 새 이미지 빌드 필요 (Backend 서비스)

**문제**: Pod가 아직 이전 이미지 사용 중
- 이전 이미지에는 `libs/common/__init__.py` 오류가 있음
- 새 이미지를 빌드해야 함

**해결**:
```bash
# 1. feature/cicd → main PR 생성 및 Merge
git push origin feature/cicd
# GitHub에서 PR 생성 → Merge

# 2. GitHub Actions가 자동으로:
#    - 새 이미지 빌드 (libs/common 수정 포함)
#    - ECR에 push (새 sha-xxx 태그)
#    - gitops/dev에 새 태그 업데이트

# 3. Argo CD가 자동으로 배포
```

---

## 현재 상태

### ✅ 정상 작동
- **api-service**: Running (1/1)
- **frontend**: Running (새 Pod 생성됨)

### ❌ CrashLoopBackOff (이전 이미지 사용 중)
- **agent-service**: NameError (이미지 재빌드 필요)
- **analysis-service**: NameError (이미지 재빌드 필요)
- **report-service**: NameError (이미지 재빌드 필요)
- **simulation-service**: NameError (이미지 재빌드 필요)

---

## 다음 단계

### 1. feature/cicd를 main에 Merge

```bash
# 1. feature/cicd 브랜치 push
git checkout feature/cicd
git push origin feature/cicd

# 2. GitHub에서 PR 생성
# feature/cicd → main

# 3. PR Merge
# Merge pull request 버튼 클릭

# 4. GitHub Actions 자동 실행
# - agent-service 이미지 빌드
# - analysis-service 이미지 빌드
# - report-service 이미지 빌드
# - simulation-service 이미지 빌드
# - 각각 ECR에 push
# - gitops/dev에 새 태그 업데이트

# 5. Argo CD 자동 배포 (3분 이내)
```

---

### 2. 검증

```bash
# 10-15분 후 Pod 상태 확인
kubectl get pods -n default

# 예상 결과:
# api-service         1/1  Running
# frontend            1/1  Running
# agent-service       1/1  Running  ✅
# analysis-service    1/1  Running  ✅
# report-service      1/1  Running  ✅
# simulation-service  1/1  Running  ✅

# Pod 로그 확인 (오류 없어야 함)
kubectl logs -n default -l app=agent-service --tail=20
```

---

## 트러블슈팅

### 문제: "여전히 CrashLoopBackOff"

**확인 1**: 이미지 태그가 업데이트되었는지
```bash
kubectl get pod <pod-name> -n default -o jsonpath='{.spec.containers[0].image}'
# 새 sha-xxx 태그여야 함
```

**확인 2**: GitHub Actions 성공했는지
```
https://github.com/seol-hj/agent_T/actions
```

**확인 3**: gitops/dev에 새 태그가 있는지
```bash
git fetch origin gitops/dev
git show origin/gitops/dev:infra/helm/services/agent-service/values-dev.yaml | grep tag
```

---

### 문제: "Argo CD가 업데이트 안 함"

**수동 동기화**:
```bash
kubectl patch application agent-service -n argocd \
  --type merge \
  -p '{"operation":{"sync":{"revision":"gitops/dev"}}}'
```

---

### 문제: "GitHub Actions 실패"

**확인**: Build 로그
```
https://github.com/seol-hj/agent_T/actions
→ 최근 workflow 클릭
→ build-and-push job 로그 확인
```

**가능한 원인**:
- Docker build 실패
- ECR push 권한 없음
- gitops/dev push 실패

---

## 왜 api-service는 성공했는가?

**api-service가 Running인 이유**:
1. `api-service/main.py`가 `libs/common`의 `get_rag_retriever`를 import하지 않음
2. 또는 이전에 빌드된 이미지에 오류가 없었음

**다른 서비스가 실패하는 이유**:
1. `main.py`에서 `from common import ...` 시 `libs/common/__init__.py` 전체가 로드됨
2. Line 56의 `Retriever` 타입 힌트에서 NameError 발생
3. 모듈 import 자체가 실패 → uvicorn 시작 불가

---

## 교훈

### 1. 타입 힌트는 런타임에 영향을 줄 수 있음

**잘못된 방법**:
```python
# from .rag import Retriever  # 주석 처리

def get_rag_retriever() -> Retriever:  # ❌ NameError!
    ...
```

**올바른 방법**:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rag import Retriever

def get_rag_retriever() -> "Retriever":  # ✅ 문자열 리터럴
    ...
```

또는:
```python
from typing import Any

def get_rag_retriever() -> Any:  # ✅ Any 사용
    ...
```

---

### 2. 이미지 태그는 실제로 존재하는 것만 사용

**자동화 필요**:
- GitHub Actions가 ECR에 push한 태그를 gitops/dev에 자동 업데이트
- 수동으로 태그를 변경하지 말 것

**현재 구현**: ✅ 이미 자동화됨 (build-and-push.yml)

---

### 3. 공통 라이브러리(libs) 변경 시 주의

**libs/common 변경 시**:
- 모든 서비스에 영향
- 반드시 테스트 후 배포
- 가능하면 후방 호환성 유지

---

## 파일 변경 목록

### 수정된 파일 (2개)
```
libs/common/__init__.py
  - TYPE_CHECKING 사용
  - 문자열 리터럴 타입 힌트

infra/helm/services/frontend/values-dev.yaml
  - tag: sha-a1b2c3d → sha-ce604f5
```

### 생성된 파일 (1개)
```
scripts/sync-argocd-now.sh
  - Argo CD 수동 동기화 스크립트
```

---

## 예상 타임라인

```
00:00 - gitops/dev에 수정 push ✅
00:01 - Argo CD 수동 동기화 ✅
00:03 - api-service, frontend Running ✅
00:05 - feature/cicd → main PR 생성
00:07 - PR Merge
00:10 - GitHub Actions 시작
00:15 - 새 이미지 ECR에 push
00:17 - gitops/dev에 새 태그 업데이트
00:20 - Argo CD 자동 배포
00:25 - 모든 Pod Running ✅
```

---

**작성일**: 2026-05-11  
**상태**: gitops/dev 수정 완료, 새 이미지 빌드 대기 중

**다음 단계**: feature/cicd → main PR & Merge
