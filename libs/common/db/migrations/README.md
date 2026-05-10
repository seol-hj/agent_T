# Database Migrations

Alembic 기반 데이터베이스 마이그레이션 관리.

---

## 설정

### 1. Alembic 초기화 (향후 작업)

```bash
# libs/common/db/migrations 디렉토리에서
alembic init alembic
```

### 2. alembic.ini 수정

```ini
# DATABASE_URL 환경변수 사용
sqlalchemy.url = driver://user:pass@localhost/dbname
# → 환경변수로 오버라이드
```

### 3. env.py 수정

```python
from libs.common.db.models import Base
target_metadata = Base.metadata
```

---

## 마이그레이션 생성

### 자동 생성 (모델 변경 감지)

```bash
alembic revision --autogenerate -m "Add experiments table"
```

### 수동 생성

```bash
alembic revision -m "Custom migration"
```

---

## 마이그레이션 실행

### 최신 버전으로 업그레이드

```bash
alembic upgrade head
```

### 특정 버전으로 업그레이드

```bash
alembic upgrade <revision_id>
```

### 다운그레이드

```bash
alembic downgrade -1  # 한 단계 되돌리기
alembic downgrade base  # 전체 되돌리기
```

---

## 마이그레이션 이력

### 현재 버전 확인

```bash
alembic current
```

### 이력 조회

```bash
alembic history --verbose
```

---

## 환경별 마이그레이션

### Local (SQLite)

```bash
export DATABASE_URL=sqlite:///./agent_t.db
alembic upgrade head
```

### Development (RDS PostgreSQL)

```bash
export DATABASE_URL=postgresql://user:pass@dev-rds.amazonaws.com:5432/agent_t_dev
alembic upgrade head
```

### Production (RDS PostgreSQL)

```bash
export DATABASE_URL=postgresql://user:pass@prod-rds.amazonaws.com:5432/agent_t_prod
alembic upgrade head
```

---

## Placeholder 마이그레이션

현재는 SQLAlchemy의 `Base.metadata.create_all()`을 사용하여 테이블 생성.

향후 프로덕션 배포 시 Alembic으로 전환 예정.

---

## 참고

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations](https://docs.sqlalchemy.org/en/14/core/metadata.html#creating-and-dropping-database-tables)
