# Bedrock Provider 사용 가이드

Amazon Bedrock을 통한 LLM 호출 가이드

---

## 개요

`BedrockProvider`는 AWS Bedrock을 통해 Claude 3, Titan 등의 LLM을 호출하는 Gateway 구현입니다.

### 핵심 기능

✅ **IAM Role/IRSA 기반 인증** - Credentials 하드코딩 금지  
✅ **Retry with exponential backoff** - 자동 재시도  
✅ **Timeout 설정** - 응답 시간 제한  
✅ **명확한 에러 메시지** - 디버깅 용이  
✅ **Structured output** - JSON 스키마 기반 출력  
✅ **Mock 모드** - 테스트용 더미 응답  
✅ **메타데이터 추적** - model_id, provider, latency, tokens

---

## 환경 설정

### 1. 환경 변수

```bash
# Provider 선택
export LLM_PROVIDER=bedrock

# 모델 ID
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# AWS 리전
export AWS_REGION=ap-northeast-2

# Timeout/Retry (선택 사항)
export BEDROCK_TIMEOUT=60        # 기본: 60초
export BEDROCK_MAX_RETRIES=3     # 기본: 3회
```

### 2. AWS 인증

#### 옵션 A: AWS CLI

```bash
# AWS CLI 설정
aws configure

# 인증 확인
aws sts get-caller-identity
```

#### 옵션 B: IAM Instance Profile (EC2)

EC2 인스턴스에 IAM Role 할당 → 자동 인증

#### 옵션 C: IRSA (EKS)

Kubernetes ServiceAccount에 IAM Role 연결 → 자동 인증

```yaml
# Helm values
serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/agent-service-irsa
```

### 3. IAM 권한

최소 권한:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```

---

## 사용 방법

### 기본 사용

```python
from common import get_llm_gateway

# 환경 변수 기반 자동 선택
llm = get_llm_gateway()

# 텍스트 생성
response = await llm.generate(
    prompt="교통 시뮬레이션이란 무엇인가요?",
    system_prompt="당신은 교통 전문가입니다.",
    max_tokens=500,
    temperature=0.7,
    prompt_version="basic-v1.0",
)

print(response.content)
print(f"Latency: {response.latency_ms}ms")
print(f"Tokens: {response.total_tokens}")
```

### 명시적 Provider 선택

```python
from common.gateways.llm import BedrockProvider

llm = BedrockProvider(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="ap-northeast-2",
    timeout=30,
    max_retries=5,
)

response = await llm.generate("Hello")
```

### 구조화된 JSON 출력

```python
output_schema = {
    "location": "string",
    "duration_hours": "number",
    "vehicle_count": "number",
    "objectives": ["string"],
}

response = await llm.generate_structured_output(
    prompt="서울 강남구 출퇴근 시간대 교통 시뮬레이션 시나리오를 생성하세요",
    output_schema=output_schema,
    temperature=0.3,  # 더 결정적
    prompt_version="scenario-gen-v2.0",
)

import json
scenario = json.loads(response.content)
print(scenario["location"])
```

### 대화 이력 포함 채팅

```python
messages = [
    {"role": "system", "content": "당신은 교통 전문가입니다."},
    {"role": "user", "content": "SUMO가 무엇인가요?"},
    {"role": "assistant", "content": "SUMO는 교통 시뮬레이터입니다."},
    {"role": "user", "content": "어떻게 사용하나요?"},
]

response = await llm.chat(
    messages=messages,
    max_tokens=500,
    temperature=0.7,
    prompt_version="chat-v1.0",
)
```

### 에러 처리

```python
response = await llm.generate("Test prompt")

if response.success:
    print(response.content)
else:
    print(f"에러: {response.error}")
    # 명확한 에러 메시지:
    # "Bedrock 접근 권한 없음: ... (IAM 권한 확인 필요)"
    # "Bedrock 요청 제한 초과: ... (잠시 후 재시도)"
```

### Mock 모드 (테스트)

```python
llm = BedrockProvider(mock_mode=True)

response = await llm.generate("Test")
# 실제 Bedrock API 호출 없이 더미 응답 반환
```

---

## 지원 모델

### Claude 3 Family

```python
# Sonnet (균형잡힌 성능)
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

# Opus (최고 성능)
model_id = "anthropic.claude-3-opus-20240229-v1:0"

# Haiku (빠르고 저렴)
model_id = "anthropic.claude-3-haiku-20240307-v1:0"
```

### Titan

```python
# Titan Text G1 - Express
model_id = "amazon.titan-text-express-v1"

# Titan Text G1 - Lite
model_id = "amazon.titan-text-lite-v1"
```

---

## 파라미터

### generate()

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `prompt` | str | 필수 | 사용자 프롬프트 |
| `system_prompt` | str | None | 시스템 프롬프트 |
| `max_tokens` | int | 1000 | 최대 토큰 수 |
| `temperature` | float | 0.7 | 온도 (0.0 ~ 1.0) |
| `prompt_version` | str | None | 프롬프트 버전 (추적용) |
| `top_p` | float | None | Top-p sampling |
| `top_k` | int | None | Top-k sampling |

### generate_structured_output()

`generate()`와 동일 + `output_schema` (dict)

### chat()

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `messages` | List[Dict] | 필수 | 대화 이력 |
| `max_tokens` | int | 1000 | 최대 토큰 수 |
| `temperature` | float | 0.7 | 온도 |
| `prompt_version` | str | None | 프롬프트 버전 |

---

## 응답 형식

### LLMResponse

```python
@dataclass
class LLMResponse:
    content: str                      # 생성된 텍스트
    model_id: str                     # 모델 ID
    provider: str                     # "bedrock"
    prompt_version: str               # 프롬프트 버전
    latency_ms: float                 # 응답 시간 (ms)
    usage: LLMUsageMetadata           # 토큰 사용량
    request_id: Optional[str]         # Bedrock Request ID
    timestamp: datetime               # 타임스탬프
    error: Optional[str]              # 에러 메시지
    raw_response: Optional[Dict]      # 원본 응답
```

### LLMUsageMetadata

```python
@dataclass
class LLMUsageMetadata:
    prompt_tokens: int       # 입력 토큰
    completion_tokens: int   # 출력 토큰
    total_tokens: int        # 총 토큰
```

---

## 에러 종류

### ValidationException

```
"Bedrock 검증 오류: ... (모델 ID 또는 요청 파라미터 확인)"
```

**원인**: 잘못된 model_id, 파라미터, 또는 요청 포맷

**해결**: model_id 확인, 파라미터 범위 확인

---

### ThrottlingException

```
"Bedrock 요청 제한 초과: ... (잠시 후 재시도)"
```

**원인**: API 호출 한도 초과

**해결**: Exponential backoff로 재시도 (자동), 또는 요청 빈도 감소

---

### AccessDeniedException

```
"Bedrock 접근 권한 없음: ... (IAM 권한 확인 필요)"
```

**원인**: IAM 권한 부족

**해결**: IAM Policy에 `bedrock:InvokeModel` 권한 추가

---

### ResourceNotFoundException

```
"Bedrock 모델 없음: ... (model_id 확인: ...)"
```

**원인**: 존재하지 않는 model_id

**해결**: 올바른 model_id 사용

---

### NoCredentialsError

```
"AWS 인증 실패: ... (IAM Role/IRSA 설정 확인)"
```

**원인**: AWS credentials 없음

**해결**: `aws configure` 실행, IAM Role 할당, IRSA 설정

---

### ConnectTimeoutError

```
"Bedrock 연결 실패: ... (네트워크 또는 리전 확인: ...)"
```

**원인**: 네트워크 문제, 잘못된 리전

**해결**: 네트워크 확인, AWS_REGION 확인

---

## 비용 최적화

### 1. 모델 선택

| 모델 | 입력 (1K tokens) | 출력 (1K tokens) | 용도 |
|---|---|---|---|
| Claude 3 Haiku | $0.00025 | $0.00125 | 간단한 작업 |
| Claude 3 Sonnet | $0.003 | $0.015 | 균형잡힌 작업 |
| Claude 3 Opus | $0.015 | $0.075 | 복잡한 작업 |

### 2. max_tokens 조정

```python
# 짧은 응답이 필요하면 max_tokens 줄이기
response = await llm.generate(
    prompt="SUMO가 무엇인가요?",
    max_tokens=100,  # 기본 1000 → 100
)
```

### 3. 캐싱 (향후)

동일 프롬프트 반복 호출 시 Redis 캐시 사용 (TODO)

### 4. 모니터링

```python
# 비용 추적을 위한 로깅
print(f"Tokens: {response.total_tokens}")
print(f"Cost: ${response.total_tokens / 1000 * 0.003:.6f}")  # Sonnet 기준
```

---

## 테스트

### Mock 모드로 테스트

```bash
export LLM_PROVIDER=mock
pytest tests/test_llm_gateway.py -v
```

### Mock boto3 client로 테스트

```bash
pytest tests/test_bedrock_provider.py -v
```

### 실제 Bedrock API 테스트

```bash
export LLM_PROVIDER=bedrock
export AWS_REGION=ap-northeast-2
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

python libs/common/examples/bedrock_example.py
```

---

## Troubleshooting

### Q1. "AWS 인증 실패" 에러

**확인**:
```bash
aws sts get-caller-identity
```

**해결**:
```bash
aws configure
# 또는
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

### Q2. "Bedrock 접근 권한 없음" 에러

**확인**: IAM Policy

**해결**: `bedrock:InvokeModel` 권한 추가

### Q3. "Bedrock 모델 없음" 에러

**확인**: model_id

**해결**: 올바른 model_id 사용
```python
# ✅ 올바름
"anthropic.claude-3-sonnet-20240229-v1:0"

# ❌ 잘못됨
"claude-3-sonnet"
```

### Q4. IRSA가 동작하지 않음 (EKS)

**확인**:
1. OIDC Provider 생성되었는지
2. ServiceAccount에 annotation 추가되었는지
3. IAM Role Trust Policy 올바른지

```bash
kubectl describe serviceaccount agent-service
# eks.amazonaws.com/role-arn 확인
```

### Q5. Timeout 에러

**해결**: Timeout 늘리기
```python
llm = BedrockProvider(timeout=120)
```

---

## 참고 문서

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude 3 Model Card](https://www.anthropic.com/claude)
- [Common Library README](./README.md)
- [LLM Gateway 테스트](./tests/test_bedrock_provider.py)

---

**버전**: 0.2.0

**상태**: ✅ Production Ready
