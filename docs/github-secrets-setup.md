# GitHub Secrets 설정 가이드

**최종 업데이트**: 2026-05-11

---

## 개요

GitHub Actions에서 AWS 리소스에 접근하려면 AWS 자격증명을 GitHub Secrets에 등록해야 합니다.

**필수 Secret**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

---

## 1. AWS Access Key 확인

### 현재 사용 중인 키 확인
```bash
# Access Key ID 확인
aws configure get aws_access_key_id

# 또는 credentials 파일 직접 확인
cat ~/.aws/credentials
```

**현재 프로젝트 키**:
```
Access Key ID: AKIASYWOIAWEV7AC6YYM
Secret Access Key: (보안상 여기 기록 안 함)
```

### 새 Access Key 생성 (필요 시)
```bash
# AWS Console 방법
# IAM → Users → 사용자 선택 → Security credentials
# → Create access key → Command Line Interface (CLI)
# → Download .csv file

# 또는 AWS CLI
aws iam create-access-key --user-name YOUR_USERNAME
```

---

## 2. GitHub Repository Secrets 추가

### 방법 1: GitHub Web UI (권장) ⭐

#### 단계
1. **GitHub Repository 접속**
   ```
   https://github.com/YOUR_USERNAME/agent-t
   ```

2. **Settings 탭 클릭**
   - Repository 상단 메뉴에서 `Settings` 클릭

3. **Secrets and variables → Actions**
   - 왼쪽 메뉴에서 `Secrets and variables` 펼치기
   - `Actions` 클릭

4. **New repository secret 클릭**
   - 우측 상단 녹색 버튼 클릭

5. **첫 번째 Secret 추가**
   - **Name**: `AWS_ACCESS_KEY_ID`
   - **Secret**: `AKIASYWOIAWEV7AC6YYM` (또는 실제 Access Key ID)
   - `Add secret` 버튼 클릭

6. **두 번째 Secret 추가**
   - 다시 `New repository secret` 클릭
   - **Name**: `AWS_SECRET_ACCESS_KEY`
   - **Secret**: `여기에_실제_Secret_Access_Key_입력`
   - `Add secret` 버튼 클릭

#### 스크린샷 위치
```
Repository 페이지
  └─ Settings (상단 탭)
      └─ Secrets and variables (왼쪽 메뉴)
          └─ Actions
              └─ Repository secrets
                  ├─ AWS_ACCESS_KEY_ID
                  └─ AWS_SECRET_ACCESS_KEY
```

---

### 방법 2: GitHub CLI

#### 설치 확인
```bash
# GitHub CLI 버전 확인
gh --version

# 없으면 설치
# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

#### 인증
```bash
# GitHub 로그인
gh auth login
# → GitHub.com
# → HTTPS
# → Yes (Authenticate Git)
# → Login with a web browser
```

#### Secret 추가
```bash
# Repository로 이동
cd /mnt/c/Users/gandd/OneDrive/Desktop/proj/agent-t

# 인터랙티브 방식 (권장)
gh secret set AWS_ACCESS_KEY_ID
# 프롬프트에서 값 입력: AKIASYWOIAWEV7AC6YYM
# Press Enter, then Ctrl+D (Linux/macOS) or Ctrl+Z (Windows)

gh secret set AWS_SECRET_ACCESS_KEY
# 프롬프트에서 Secret Key 입력
# Press Enter, then Ctrl+D (Linux/macOS) or Ctrl+Z (Windows)

# 또는 파이프 방식
echo "AKIASYWOIAWEV7AC6YYM" | gh secret set AWS_ACCESS_KEY_ID
echo "YOUR_SECRET_KEY_HERE" | gh secret set AWS_SECRET_ACCESS_KEY
```

---

## 3. Secret 확인

### GitHub Web UI
```
Settings → Secrets and variables → Actions → Repository secrets
```

**확인 사항**:
- ✅ `AWS_ACCESS_KEY_ID` (Updated X minutes ago)
- ✅ `AWS_SECRET_ACCESS_KEY` (Updated X minutes ago)

**주의**: Secret 값은 추가 후 다시 볼 수 없습니다 (보안)

---

### GitHub CLI
```bash
# Secret 목록 확인
gh secret list

# 출력 예시
# AWS_ACCESS_KEY_ID        Updated 2024-05-11
# AWS_SECRET_ACCESS_KEY    Updated 2024-05-11
```

---

## 4. Workflow에서 Secret 사용

### 현재 Workflow 구조

#### build-and-push.yml (재사용 가능한 workflow)
```yaml
on:
  workflow_call:
    secrets:
      AWS_ACCESS_KEY_ID:
        required: true
      AWS_SECRET_ACCESS_KEY:
        required: true

jobs:
  build-and-push:
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-2
```

#### ci-frontend.yml (호출하는 workflow)
```yaml
jobs:
  build-and-push:
    uses: ./.github/workflows/build-and-push.yml
    secrets:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

**중요**: Secret 이름은 대소문자를 정확히 일치시켜야 함!

---

## 5. 테스트

### Secret 설정 후 테스트
```bash
# 코드 변경 (아무거나)
cd /mnt/c/Users/gandd/OneDrive/Desktop/proj/agent-t
echo "# test" >> README.md

# Commit & Push
git add README.md
git commit -m "test: trigger GitHub Actions"
git push origin main
```

### GitHub Actions 확인
1. **Repository → Actions 탭**
2. **최신 Workflow 클릭**
3. **build-and-push job 확인**

**성공 시**:
```
✅ Configure AWS credentials (0s)
✅ Login to Amazon ECR (2s)
✅ Build and push Docker image (3m 45s)
```

**실패 시** (Secret 없음):
```
❌ Configure AWS credentials (0s)
Error: Credentials could not be loaded, please check your action inputs
```

---

## 6. 트러블슈팅

### 문제: "Credentials could not be loaded"

**원인**:
- Secret이 추가되지 않음
- Secret 이름이 일치하지 않음 (대소문자)

**해결**:
```bash
# Secret 확인
gh secret list

# 없으면 추가
gh secret set AWS_ACCESS_KEY_ID
gh secret set AWS_SECRET_ACCESS_KEY
```

---

### 문제: "Access Denied" 또는 "UnauthorizedOperation"

**원인**:
- Access Key에 권한이 부족함

**해결**:
```bash
# IAM User 권한 확인
aws iam list-attached-user-policies --user-name YOUR_USERNAME

# 필요한 권한
# - AmazonEC2ContainerRegistryFullAccess (ECR 푸시)
# - 또는 커스텀 Policy
```

**필요한 최소 권한**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### 문제: Secret 값 변경

**방법**:
```bash
# GitHub CLI
gh secret set AWS_ACCESS_KEY_ID --body "NEW_VALUE"
gh secret set AWS_SECRET_ACCESS_KEY --body "NEW_VALUE"

# 또는 GitHub Web UI에서
# Settings → Secrets → AWS_ACCESS_KEY_ID → Update
```

---

### 문제: Secret 삭제

**방법**:
```bash
# GitHub CLI
gh secret delete AWS_ACCESS_KEY_ID
gh secret delete AWS_SECRET_ACCESS_KEY

# 또는 GitHub Web UI에서
# Settings → Secrets → AWS_ACCESS_KEY_ID → Remove
```

---

## 7. 보안 모범 사례

### ✅ 권장 사항

1. **IAM User 전용 Access Key 사용**
   - Root 계정 Access Key 사용 금지
   - 최소 권한 원칙 (Least Privilege)

2. **Access Key Rotation**
   ```bash
   # 90일마다 교체 권장
   aws iam create-access-key --user-name YOUR_USERNAME
   # 새 키를 GitHub Secrets에 업데이트
   aws iam delete-access-key --access-key-id OLD_KEY_ID --user-name YOUR_USERNAME
   ```

3. **Access Key 노출 주의**
   - Git에 커밋 금지
   - 로그에 출력 금지
   - 공개 채널 공유 금지

4. **Secret 범위 제한**
   - Repository-level Secrets 사용 (현재 설정)
   - Organization-level은 필요 시에만

---

### ❌ 피해야 할 사항

1. **코드에 하드코딩**
   ```python
   # ❌ 절대 금지
   AWS_ACCESS_KEY_ID = "AKIASYWOIAWEV7AC6YYM"
   ```

2. **Environment 파일에 커밋**
   ```bash
   # ❌ .env 파일을 Git에 커밋 금지
   git add .env  # 절대 안 됨
   ```

3. **Public Repository에 노출**
   - Private Repository 사용 권장
   - 또는 Secret 노출 시 즉시 폐기

---

## 8. 대안: OIDC 방식 (향후 고려)

### 장점
- Access Key 불필요
- 자동 만료 (단기 토큰)
- 더 안전함

### 설정 방법
```yaml
# .github/workflows/build-and-push.yml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::190484841865:role/GitHubActionsRole
    aws-region: ap-northeast-2
```

**필요 작업**:
- AWS IAM Identity Provider 설정
- IAM Role 생성 (Trust Policy)
- GitHub OIDC Token 설정

**참고**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

---

## 요약

### 필수 작업
1. ✅ GitHub Repository → Settings → Secrets
2. ✅ `AWS_ACCESS_KEY_ID` 추가
3. ✅ `AWS_SECRET_ACCESS_KEY` 추가
4. ✅ Git push로 테스트

### 확인 사항
- ✅ Secret 이름 대소문자 일치 (`AWS_ACCESS_KEY_ID`)
- ✅ Access Key에 ECR 권한 있음
- ✅ GitHub Actions에서 정상 동작

---

**관련 문서**:
- [CHANGES-2026-05-11.md](./CHANGES-2026-05-11.md) - Workflow 수정 내역
- [GitHub Actions 공식 문서](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
