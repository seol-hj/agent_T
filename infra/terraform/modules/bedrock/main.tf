# ============================================================================
# module: bedrock
# 책임: Bedrock 모델 호출에 필요한 IAM 정책 / Logging / Guardrail 정의.
# 활성화 단계: 4
# 메모:
#   - Bedrock 모델 access 자체는 콘솔에서 enable (account 레벨, IaC 외부)
#   - IRSA 에 attach 할 IAM Policy 만 본 모듈에서 생성:
#       - bedrock:InvokeModel, bedrock:InvokeModelWithResponseStream
#       - bedrock:ListFoundationModels (옵션)
#   - Guardrail / Knowledge Base 는 본격 사용 시 추가
#   - 비즈니스 로직은 직접 호출 금지 → LLM Gateway 경유 (CLAUDE.md 참조)
# ============================================================================

# 구현은 4단계에서 추가된다.
