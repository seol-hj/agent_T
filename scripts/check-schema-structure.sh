#!/bin/bash
#
# 스키마 구조 확인 스크립트
# 모든 필수 스키마 파일이 존재하는지 확인
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo "스키마 파일 구조 검증"
echo "=========================================="
echo ""

cd "$PROJECT_ROOT"

# 필수 스키마 파일 목록
SCHEMA_FILES=(
    "libs/common/schemas/__init__.py"
    "libs/common/schemas/user_request.py"
    "libs/common/schemas/experiment.py"
    "libs/common/schemas/network.py"
    "libs/common/schemas/demand.py"
    "libs/common/schemas/simulation.py"
    "libs/common/schemas/analysis.py"
    "libs/common/schemas/report.py"
    "libs/common/schemas/logging.py"
    "libs/common/schemas/versioning.py"
)

# 테스트 파일
TEST_FILES=(
    "libs/common/tests/test_schemas.py"
)

missing=0
found=0

echo "1. 스키마 파일 확인"
echo "-------------------"
for file in "${SCHEMA_FILES[@]}"; do
    if [ -f "$file" ]; then
        size=$(wc -l < "$file")
        echo "  ✓ $file ($size lines)"
        ((found++))
    else
        echo "  ✗ $file (누락)"
        ((missing++))
    fi
done
echo ""

echo "2. 테스트 파일 확인"
echo "-------------------"
for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        size=$(wc -l < "$file")
        echo "  ✓ $file ($size lines)"
        ((found++))
    else
        echo "  ✗ $file (누락)"
        ((missing++))
    fi
done
echo ""

echo "3. 주요 클래스 확인 (grep)"
echo "-------------------------"

declare -A CLASSES=(
    ["UserRequest"]="libs/common/schemas/user_request.py"
    ["ExperimentSpec"]="libs/common/schemas/experiment.py"
    ["ScenarioPlan"]="libs/common/schemas/experiment.py"
    ["ScenarioVariant"]="libs/common/schemas/experiment.py"
    ["NetworkBuildRequest"]="libs/common/schemas/network.py"
    ["NetworkArtifact"]="libs/common/schemas/network.py"
    ["DemandBuildRequest"]="libs/common/schemas/demand.py"
    ["DemandArtifact"]="libs/common/schemas/demand.py"
    ["SimulationRunRequest"]="libs/common/schemas/simulation.py"
    ["SimulationRunArtifact"]="libs/common/schemas/simulation.py"
    ["AnalysisResult"]="libs/common/schemas/analysis.py"
    ["BaselineKPI"]="libs/common/schemas/analysis.py"
    ["AlternativeKPI"]="libs/common/schemas/analysis.py"
    ["KPIComparison"]="libs/common/schemas/analysis.py"
    ["ReportArtifact"]="libs/common/schemas/report.py"
    ["ReportSection"]="libs/common/schemas/report.py"
    ["AgentLog"]="libs/common/schemas/logging.py"
    ["LogLevel"]="libs/common/schemas/logging.py"
    ["ModelVersion"]="libs/common/schemas/versioning.py"
    ["PromptVersion"]="libs/common/schemas/versioning.py"
)

class_missing=0
for class in "${!CLASSES[@]}"; do
    file="${CLASSES[$class]}"
    if grep -q "class $class" "$file" 2>/dev/null; then
        echo "  ✓ $class (in $file)"
    else
        echo "  ✗ $class (in $file에서 찾을 수 없음)"
        ((class_missing++))
    fi
done
echo ""

echo "4. 필수 필드 확인 (schema_version)"
echo "-----------------------------------"
for file in "${SCHEMA_FILES[@]}"; do
    if [ -f "$file" ] && [ "$(basename "$file")" != "__init__.py" ]; then
        if grep -q 'schema_version.*=.*Field' "$file"; then
            echo "  ✓ $file"
        else
            echo "  ⚠ $file (schema_version 필드 없음)"
        fi
    fi
done
echo ""

echo "5. Artifact URI 필드 확인"
echo "-------------------------"
ARTIFACT_FILES=(
    "libs/common/schemas/network.py"
    "libs/common/schemas/demand.py"
    "libs/common/schemas/simulation.py"
    "libs/common/schemas/report.py"
)

for file in "${ARTIFACT_FILES[@]}"; do
    if [ -f "$file" ]; then
        if grep -q 'uri.*=.*Field' "$file"; then
            echo "  ✓ $file"
        else
            echo "  ⚠ $file (uri 필드 없음)"
        fi
    fi
done
echo ""

echo "6. AnalysisResult KPI 비교 확인"
echo "--------------------------------"
if grep -q "baseline.*BaselineKPI" "libs/common/schemas/analysis.py" && \
   grep -q "alternatives.*AlternativeKPI" "libs/common/schemas/analysis.py"; then
    echo "  ✓ Baseline/Alternative KPI 비교 구조 확인됨"
else
    echo "  ✗ Baseline/Alternative KPI 비교 구조 누락"
fi
echo ""

echo "=========================================="
if [ $missing -eq 0 ] && [ $class_missing -eq 0 ]; then
    echo "✓ 모든 스키마 파일 및 클래스 확인 완료!"
    echo "  - 파일: $found개 발견"
    echo "  - 클래스: ${#CLASSES[@]}개 확인"
    exit 0
else
    echo "✗ 일부 파일 또는 클래스 누락"
    echo "  - 누락된 파일: $missing개"
    echo "  - 누락된 클래스: $class_missing개"
    exit 1
fi
