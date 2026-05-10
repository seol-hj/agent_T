"""
Experiment Parser Prompts

ExperimentSpec 생성을 위한 프롬프트 템플릿
"""

from typing import Optional


EXPERIMENT_PARSER_SYSTEM_PROMPT = """당신은 교통 시뮬레이션 실험 명세를 생성하는 AI 전문가입니다.

사용자의 자연어 요구사항을 분석하여 구조화된 실험 명세(ExperimentSpec)를 생성합니다.

## 지원하는 요청 타입

1. **demand_increase**: 교통량 증가 시나리오
   - 키워드: "교통량 증가", "차량 증가", "수요 증가"
   - 필수 정보: location, time_settings, traffic_settings.vehicle_count

2. **lane_change**: 차로 변경 시나리오
   - 키워드: "차로 추가", "차선 변경", "도로 확장"
   - 필수 정보: location, modifications (차로 정보)

3. **signal_timing_change**: 신호 타이밍 변경 시나리오
   - 키워드: "신호등", "신호 체계", "신호 타이밍"
   - 필수 정보: location, modifications (신호 정보)

## 출력 규칙

1. 사용자 입력에서 명확한 정보만 추출합니다.
2. 추론하거나 가정하지 않습니다.
3. 필수 정보가 부족하면 missing_fields를 반환합니다.
4. location은 구체적인 지역명이 있어야 합니다.
5. time_settings는 시간대나 기간이 명시되어야 합니다.
6. 모호한 표현은 clarification이 필요합니다.

## ExperimentSpec 구조

{
  "experiment_id": "생성할 고유 ID (exp-YYYYMMDD-NNN 형식)",
  "request_id": "사용자 요청 ID",
  "title": "실험 제목 (한국어, 간결하게)",
  "description": "실험 설명 (사용자 의도 반영)",
  "location": {
    "region": "지역명 (예: 서울특별시 강남구)",
    "bbox": [경도_min, 위도_min, 경도_max, 위도_max],
    "osm_query": "OpenStreetMap 쿼리"
  },
  "time_settings": {
    "start_time": "시작 시간 (HH:MM)",
    "end_time": "종료 시간 (HH:MM)",
    "duration_hours": 시뮬레이션 시간(시간),
    "time_period": "시간대 구분 (예: weekday_morning_rush)"
  },
  "traffic_settings": {
    "vehicle_count": 차량 수,
    "vehicle_types": ["passenger", "bus", "truck"],
    "vehicle_distribution": {"passenger": 0.8, "bus": 0.1, "truck": 0.1},
    "demand_level": "high | medium | low"
  },
  "objectives": ["목표 1", "목표 2", ...],
  "constraints": ["제약 1", "제약 2", ...]
}

## 지역별 bbox 참고 (정확한 값이 필요하면 사용)

- 서울 강남구: [127.0276, 37.4959, 127.0948, 37.5219]
- 서울 종로구: [126.9684, 37.5700, 127.0104, 37.5990]
- 부산 해운대구: [129.1296, 35.1580, 129.1800, 35.1860]

## 출퇴근 시간대 참고

- weekday_morning_rush: 07:00-09:00
- weekday_evening_rush: 18:00-20:00
- weekend_daytime: 10:00-18:00
"""


def build_experiment_parser_prompt(
    user_input: str,
    request_id: str,
    rag_context: Optional[str] = None
) -> str:
    """
    ExperimentSpec 생성 프롬프트 빌드

    Args:
        user_input: 사용자 자연어 입력
        request_id: 요청 ID
        rag_context: RAG 컨텍스트 (Optional)

    Returns:
        완성된 프롬프트
    """
    prompt = f"""사용자 요청을 분석하여 ExperimentSpec JSON을 생성하세요.

## 사용자 입력
{user_input}

## 요청 ID
{request_id}
"""

    if rag_context:
        prompt += f"""
## 참고 컨텍스트 (RAG)
{rag_context}
"""

    prompt += """
## 작업

1. 사용자 입력에서 요청 타입을 분류하세요 (demand_increase, lane_change, signal_timing_change).
2. 명시된 정보만 사용하여 ExperimentSpec JSON을 생성하세요.
3. 필수 정보가 부족하면 missing_fields 목록을 반환하세요.
4. bbox가 없으면 지역명만으로 osm_query를 생성하세요 (bbox는 나중에 채움).
5. 시간대가 모호하면 출퇴근 시간을 기본으로 가정하지 말고 missing_fields에 추가하세요.

## 출력 형식

반드시 다음 JSON 구조로 응답하세요:

```json
{
  "request_type": "요청 타입",
  "confidence_score": 0.0-1.0 사이 신뢰도,
  "experiment_spec": ExperimentSpec JSON 또는 null,
  "missing_fields": ["누락된 필드"] 또는 null,
  "clarification_question": "보완 질문" 또는 null
}
```

**중요**: missing_fields가 있으면 experiment_spec는 null이어야 합니다.
"""

    return prompt


MISSING_FIELDS_CLARIFICATION_MAP = {
    "location": "시뮬레이션할 지역의 위치를 알려주세요. 예: 서울 강남구",
    "location.bbox": "구체적인 지역 범위를 알려주세요. 예: 서울 강남구 전체 또는 특정 구역",
    "location.region": "어느 지역에서 시뮬레이션을 실행하시겠습니까?",
    "time_settings": "시뮬레이션할 시간대를 알려주세요. 예: 평일 오전 출퇴근 시간(07:00-09:00)",
    "time_settings.start_time": "시뮬레이션 시작 시간을 알려주세요. 예: 07:00",
    "time_settings.end_time": "시뮬레이션 종료 시간을 알려주세요. 예: 09:00",
    "time_settings.time_period": "어떤 시간대를 시뮬레이션하시겠습니까? 예: 평일 아침 출퇴근 시간",
    "traffic_settings.vehicle_count": "시뮬레이션할 차량 수를 알려주세요. 예: 5000대",
    "traffic_settings.demand_level": "교통량 수준을 알려주세요 (높음/보통/낮음)",
    "modifications": "어떤 변경사항을 시뮬레이션하시겠습니까? 예: 신호등 타이밍 조정, 차로 추가",
    "objectives": "이 시뮬레이션의 목표를 알려주세요. 예: 통행 시간 단축, 배출량 감소",
}


def generate_clarification_question(missing_fields: list[str]) -> str:
    """
    누락된 필드에 대한 보완 질문 생성

    Args:
        missing_fields: 누락된 필드 목록

    Returns:
        보완 질문 문자열
    """
    if not missing_fields:
        return ""

    questions = []
    for field in missing_fields:
        if field in MISSING_FIELDS_CLARIFICATION_MAP:
            questions.append(MISSING_FIELDS_CLARIFICATION_MAP[field])
        else:
            questions.append(f"{field} 정보를 제공해 주세요.")

    if len(questions) == 1:
        return questions[0]
    else:
        return "다음 정보를 추가로 알려주세요:\n" + "\n".join(
            f"{i+1}. {q}" for i, q in enumerate(questions)
        )
