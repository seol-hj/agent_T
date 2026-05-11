#!/bin/bash
# GitHub Actions Workflow 수정 스크립트
# workflow_call 사용 시 올바른 문법으로 수정

set -e

WORKFLOWS_DIR="/mnt/c/Users/gandd/OneDrive/Desktop/proj/agent-t/.github/workflows"

# 수정할 서비스 목록
SERVICES=(
  "agent-service"
  "analysis-service"
  "api-service"
  "report-service"
  "simulation-runner"
  "simulation-service"
)

for service in "${SERVICES[@]}"; do
  FILE="${WORKFLOWS_DIR}/ci-${service}.yml"

  if [ ! -f "$FILE" ]; then
    echo "⚠️  파일 없음: $FILE"
    continue
  fi

  echo "🔧 수정 중: ci-${service}.yml"

  # 백업 생성
  cp "$FILE" "${FILE}.bak"

  # 서비스 이름에서 하이픈을 언더스코어로 변경 (변수명용)
  SERVICE_VAR=$(echo "$service" | tr '-' '_')

  # Python 스크립트로 YAML 수정 (복잡한 구조 변경)
  python3 << EOF
import re

with open('$FILE', 'r') as f:
    content = f.read()

# jobs: 섹션 찾기
jobs_match = re.search(r'jobs:\s+build-and-push:', content)
if not jobs_match:
    print("⚠️  build-and-push job을 찾을 수 없습니다.")
    exit(0)

# Determine environment 단계 찾기
env_step = re.search(r'- name: Determine environment.*?(?=\n      - |\njobs:|\Z)', content, re.DOTALL)

if env_step:
    # determine-env job 생성
    new_jobs = '''jobs:
  determine-env:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    outputs:
      ecr-repo: \${{ steps.env.outputs.ecr-repo }}
    steps:
''' + env_step.group(0) + '''

  build-and-push:
    needs: determine-env
    uses: ./.github/workflows/build-and-push.yml
    if: github.event_name == 'push'
    with:
      service-name: ${service}
      dockerfile-path: apps/${service}/Dockerfile
      context-path: apps/${service}
      ecr-repository: \${{ needs.determine-env.outputs.ecr-repo }}
      test-command: |
        pip install -r requirements.txt
        pytest tests/
      skip-tests: false
    secrets:
      aws-access-key-id: \${{ secrets.AWS_ACCESS_KEY_ID }}
      aws-secret-access-key: \${{ secrets.AWS_SECRET_ACCESS_KEY }}'''

    # jobs: 이후 부분 교체
    content = re.sub(r'jobs:.*', new_jobs, content, flags=re.DOTALL)
else:
    # Determine environment 단계가 없는 경우 (간단한 케이스)
    new_jobs = '''jobs:
  build-and-push:
    uses: ./.github/workflows/build-and-push.yml
    if: github.event_name == 'push'
    with:
      service-name: ${service}
      dockerfile-path: apps/${service}/Dockerfile
      context-path: apps/${service}
      ecr-repository: agent-t-dev-${service}
      test-command: |
        pip install -r requirements.txt
        pytest tests/
      skip-tests: false
    secrets:
      aws-access-key-id: \${{ secrets.AWS_ACCESS_KEY_ID }}
      aws-secret-access-key: \${{ secrets.AWS_SECRET_ACCESS_KEY }}'''

    content = re.sub(r'jobs:.*', new_jobs, content, flags=re.DOTALL)

with open('$FILE', 'w') as f:
    f.write(content)

print(f"✅ 수정 완료: ${service}")
EOF

done

echo ""
echo "✅ 모든 워크플로우 수정 완료"
echo ""
echo "백업 파일: .github/workflows/*.bak"
echo "변경 사항 확인: git diff .github/workflows/"
