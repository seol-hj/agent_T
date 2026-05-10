"""
ObservabilityContext 테스트
"""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from common.observability.context import (
    ObservabilityContext,
    set_context,
    get_context,
    create_context,
    with_context,
)


def test_create_context():
    """컨텍스트 생성 테스트"""
    context = create_context(
        experiment_id="exp_001",
        run_id="run_001",
        step_name="orchestrator"
    )

    assert context.request_id.startswith("req_")
    assert context.experiment_id == "exp_001"
    assert context.run_id == "run_001"
    assert context.step_name == "orchestrator"
    assert context.created_at is not None


def test_set_and_get_context():
    """컨텍스트 설정 및 조회 테스트"""
    context = create_context(experiment_id="exp_001")
    set_context(context)

    retrieved = get_context()
    assert retrieved is not None
    assert retrieved.experiment_id == "exp_001"
    assert retrieved.request_id == context.request_id


def test_context_to_dict():
    """컨텍스트 딕셔너리 변환 테스트"""
    context = create_context(
        experiment_id="exp_001",
        step_name="orchestrator",
        metadata={"foo": "bar"}
    )

    data = context.to_dict()
    assert data["experiment_id"] == "exp_001"
    assert data["step_name"] == "orchestrator"
    assert data["metadata"]["foo"] == "bar"


def test_context_copy():
    """컨텍스트 복사 및 업데이트 테스트"""
    context = create_context(experiment_id="exp_001", step_name="orchestrator")
    updated = context.copy(step_name="scenario_builder", variant_id="baseline")

    assert updated.experiment_id == "exp_001"  # 유지
    assert updated.step_name == "scenario_builder"  # 변경
    assert updated.variant_id == "baseline"  # 추가
    assert context.step_name == "orchestrator"  # 원본 유지


def test_with_context_manager():
    """with_context 매니저 테스트"""
    # 컨텍스트 없음
    assert get_context() is None

    # 새 컨텍스트 생성
    with with_context(experiment_id="exp_001", step_name="orchestrator"):
        context = get_context()
        assert context is not None
        assert context.experiment_id == "exp_001"
        assert context.step_name == "orchestrator"

    # 컨텍스트 복원 (None)
    assert get_context() is None


def test_with_context_nesting():
    """중첩된 with_context 테스트"""
    with with_context(experiment_id="exp_001", step_name="orchestrator"):
        ctx1 = get_context()
        assert ctx1.step_name == "orchestrator"

        # 중첩된 컨텍스트 (업데이트)
        with with_context(step_name="scenario_builder"):
            ctx2 = get_context()
            assert ctx2.experiment_id == "exp_001"  # 유지
            assert ctx2.step_name == "scenario_builder"  # 변경

        # 이전 컨텍스트 복원
        ctx3 = get_context()
        assert ctx3.step_name == "orchestrator"


def test_with_context_exception():
    """with_context 예외 발생 시 복원 테스트"""
    initial_context = create_context(experiment_id="exp_initial")
    set_context(initial_context)

    try:
        with with_context(experiment_id="exp_exception"):
            assert get_context().experiment_id == "exp_exception"
            raise ValueError("Test exception")
    except ValueError:
        pass

    # 이전 컨텍스트 복원
    assert get_context().experiment_id == "exp_initial"
