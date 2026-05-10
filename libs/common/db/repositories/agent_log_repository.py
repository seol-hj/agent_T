"""
AgentLog Repository
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import AgentLog
from .base_repository import BaseRepository


class AgentLogRepository(BaseRepository[AgentLog]):
    """Agent 로그 Repository"""

    def __init__(self, session: Session):
        super().__init__(AgentLog, session)

    def get_by_experiment(self, experiment_id: str) -> List[AgentLog]:
        """
        실험별 로그 조회

        Args:
            experiment_id: 실험 ID

        Returns:
            로그 리스트
        """
        return (
            self.session.query(AgentLog)
            .filter(AgentLog.experiment_id == experiment_id)
            .order_by(AgentLog.created_at.asc())
            .all()
        )

    def get_by_step(self, step_name: str, limit: Optional[int] = None) -> List[AgentLog]:
        """
        단계별 로그 조회

        Args:
            step_name: 단계 이름 (orchestrator, scenario_builder, etc.)
            limit: 최대 개수

        Returns:
            로그 리스트
        """
        query = (
            self.session.query(AgentLog)
            .filter(AgentLog.step_name == step_name)
            .order_by(AgentLog.created_at.desc())
        )

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[AgentLog]:
        """
        상태별 로그 조회

        Args:
            status: 상태 (success, failure)
            limit: 최대 개수

        Returns:
            로그 리스트
        """
        query = (
            self.session.query(AgentLog)
            .filter(AgentLog.status == status)
            .order_by(AgentLog.created_at.desc())
        )

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def get_token_usage_by_experiment(self, experiment_id: str) -> int:
        """
        실험별 토큰 사용량 합계

        Args:
            experiment_id: 실험 ID

        Returns:
            총 토큰 사용량
        """
        result = (
            self.session.query(func.sum(AgentLog.tokens_used))
            .filter(AgentLog.experiment_id == experiment_id)
            .scalar()
        )
        return result or 0

    def get_average_execution_time_by_step(self, step_name: str) -> float:
        """
        단계별 평균 실행 시간

        Args:
            step_name: 단계 이름

        Returns:
            평균 실행 시간 (ms)
        """
        result = (
            self.session.query(func.avg(AgentLog.execution_time_ms))
            .filter(AgentLog.step_name == step_name, AgentLog.status == "success")
            .scalar()
        )
        return result or 0.0
