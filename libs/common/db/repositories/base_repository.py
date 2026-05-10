"""
Base Repository

모든 Repository의 기본 클래스
"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    기본 Repository 클래스

    CRUD 공통 로직 제공
    """

    def __init__(self, model: Type[ModelType], session: Session):
        """
        Args:
            model: SQLAlchemy 모델 클래스
            session: SQLAlchemy 세션
        """
        self.model = model
        self.session = session

    def create(self, **kwargs) -> ModelType:
        """
        레코드 생성

        Args:
            **kwargs: 모델 필드

        Returns:
            생성된 모델 인스턴스
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def get(self, id: str) -> Optional[ModelType]:
        """
        ID로 레코드 조회

        Args:
            id: Primary Key

        Returns:
            모델 인스턴스 또는 None
        """
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[ModelType]:
        """
        모든 레코드 조회

        Args:
            limit: 최대 개수
            offset: 시작 위치

        Returns:
            모델 인스턴스 리스트
        """
        query = self.session.query(self.model)

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def get_by_filter(self, limit: Optional[int] = None, offset: Optional[int] = None, **filters) -> List[ModelType]:
        """
        필터 조건으로 레코드 조회

        Args:
            limit: 최대 개수
            offset: 시작 위치
            **filters: 필터 조건 (필드명=값)

        Returns:
            모델 인스턴스 리스트
        """
        query = self.session.query(self.model).filter_by(**filters)

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """
        레코드 업데이트

        Args:
            id: Primary Key
            **kwargs: 업데이트할 필드

        Returns:
            업데이트된 모델 인스턴스 또는 None
        """
        instance = self.get(id)
        if instance is None:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self, id: str) -> bool:
        """
        레코드 삭제

        Args:
            id: Primary Key

        Returns:
            삭제 성공 여부
        """
        instance = self.get(id)
        if instance is None:
            return False

        self.session.delete(instance)
        self.session.commit()
        return True

    def count(self, **filters) -> int:
        """
        레코드 개수 세기

        Args:
            **filters: 필터 조건

        Returns:
            레코드 개수
        """
        query = self.session.query(func.count(self.model.id))

        if filters:
            query = query.filter_by(**filters)

        return query.scalar()

    def exists(self, id: str) -> bool:
        """
        레코드 존재 여부 확인

        Args:
            id: Primary Key

        Returns:
            존재 여부
        """
        return self.session.query(
            self.session.query(self.model).filter(self.model.id == id).exists()
        ).scalar()
