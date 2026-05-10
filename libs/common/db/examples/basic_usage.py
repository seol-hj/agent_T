"""
DB Repository 기본 사용 예제
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common.db.session import setup_database, get_global_db
from common.db.repositories import (
    ExperimentRepository,
    UserRequestRepository,
    ScenarioRepository,
    AgentLogRepository,
)


def main():
    """기본 사용 예제"""

    # 1. 데이터베이스 초기화 (SQLite 인메모리)
    print("1. 데이터베이스 초기화...")
    setup_database(database_url="sqlite:///:memory:", echo=True)

    # 2. 세션 생성
    for db in get_global_db():
        # 3. Repository 생성
        user_req_repo = UserRequestRepository(db)
        exp_repo = ExperimentRepository(db)
        scenario_repo = ScenarioRepository(db)
        log_repo = AgentLogRepository(db)

        print("\n2. 사용자 요청 생성...")
        # 사용자 요청 생성
        user_request = user_req_repo.create(
            id="req_001",
            request_text="강남역 일대 교통량 20% 증가 시뮬레이션",
            language="ko",
            user_id="user_001"
        )
        print(f"   ✓ 사용자 요청 생성: {user_request.id}")

        print("\n3. 실험 생성...")
        # 실험 생성
        experiment = exp_repo.create(
            id="exp_001",
            user_request_id="req_001",
            status="pending"
        )
        print(f"   ✓ 실험 생성: {experiment.id}, 상태: {experiment.status}")

        print("\n4. 실험 상태 업데이트...")
        # 실험 상태 업데이트
        experiment = exp_repo.update_status("exp_001", "running")
        print(f"   ✓ 실험 상태 변경: {experiment.status}")

        print("\n5. 시나리오 생성...")
        # 시나리오 생성
        baseline = scenario_repo.create(
            id="scenario_baseline",
            experiment_id="exp_001",
            scenario_type="baseline",
            plan_json={"baseline": True}
        )
        alternative = scenario_repo.create(
            id="scenario_alt",
            experiment_id="exp_001",
            scenario_type="demand_increase",
            plan_json={"multiplier": 1.2}
        )
        print(f"   ✓ 베이스라인 시나리오: {baseline.id}")
        print(f"   ✓ 대안 시나리오: {alternative.id}")

        print("\n6. Agent 로그 생성...")
        # Agent 로그 생성
        log1 = log_repo.create(
            experiment_id="exp_001",
            step_name="orchestrator",
            agent_type="llm",
            input_data={"query": "강남역 교통량 증가"},
            output_data={"spec": {"experiment_id": "exp_001"}},
            tokens_used=1500,
            execution_time_ms=2500.0,
            status="success"
        )
        log2 = log_repo.create(
            experiment_id="exp_001",
            step_name="scenario_builder",
            agent_type="rule_based",
            execution_time_ms=800.0,
            status="success"
        )
        print(f"   ✓ Orchestrator 로그: {log1.id}")
        print(f"   ✓ Scenario Builder 로그: {log2.id}")

        print("\n7. 데이터 조회...")
        # 실험별 시나리오 조회
        scenarios = scenario_repo.get_by_experiment("exp_001")
        print(f"   ✓ 실험의 시나리오 수: {len(scenarios)}")

        # 실험별 로그 조회
        logs = log_repo.get_by_experiment("exp_001")
        print(f"   ✓ 실험의 로그 수: {len(logs)}")

        # 토큰 사용량 조회
        total_tokens = log_repo.get_token_usage_by_experiment("exp_001")
        print(f"   ✓ 총 토큰 사용량: {total_tokens}")

        # 평균 실행 시간 조회
        avg_time = log_repo.get_average_execution_time_by_step("orchestrator")
        print(f"   ✓ Orchestrator 평균 실행 시간: {avg_time}ms")

        print("\n8. 실험 완료 처리...")
        # 실험 완료
        from datetime import datetime
        experiment = exp_repo.update_status(
            "exp_001",
            "completed",
            completed_at=datetime.utcnow()
        )
        print(f"   ✓ 실험 상태: {experiment.status}")
        print(f"   ✓ 완료 시간: {experiment.completed_at}")

        print("\n9. 최근 실험 조회...")
        # 최근 실험 조회
        recent_exps = exp_repo.get_recent(limit=10)
        print(f"   ✓ 최근 실험 수: {len(recent_exps)}")
        for exp in recent_exps:
            print(f"     - {exp.id}: {exp.status}")

        print("\n✅ 모든 작업 완료!")


if __name__ == "__main__":
    main()
