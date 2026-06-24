from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import (
    BigInteger,
    Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "job_compass.db"
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        Index("idx_companies_name", "name"),
        Index("idx_companies_normalized_name", "normalized_name"),
        Index("idx_companies_employee_count", "employee_count"),
    )

    seq              = Column(Integer, primary_key=True)
    name             = Column(String, nullable=False)
    normalized_name  = Column(String)
    name_initials    = Column(String)
    business_reg_no  = Column(String)
    address          = Column(String)
    industry_code    = Column(String)
    industry_name    = Column(String)
    workplace_type   = Column(String)
    join_status      = Column(String)
    join_date        = Column(String)
    employee_count   = Column(Integer)
    # 국민연금 보험료 고지 기준 — 실제 임금과 다름, 연봉 추정 참고값으로만 사용
    monthly_charge_amt = Column(BigInteger)
    sido_code        = Column(String)
    sigungu_code     = Column(String)
    data_created_ym  = Column(String)
    search_rank      = Column(Integer, default=0)
    synced_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at       = Column(DateTime, default=datetime.utcnow)


class CompanyMonthlyStats(Base):
    __tablename__ = "company_monthly_stats"
    __table_args__ = (
        UniqueConstraint("seq", "year_month"),
        Index("idx_monthly_stats_seq_ym", "seq", "year_month"),
    )

    id             = Column(Integer, primary_key=True, autoincrement=True)
    seq            = Column(Integer, nullable=False)
    year_month     = Column(String, nullable=False)
    employee_count = Column(Integer)
    new_joiners    = Column(Integer)   # 신규 취득자 (입사자)
    leavers        = Column(Integer)   # 상실 가입자 (퇴사자)
    created_at     = Column(DateTime, default=datetime.utcnow)


class WithdrawnCompany(Base):
    __tablename__ = "withdrawn_companies"
    __table_args__ = (Index("idx_withdrawn_name", "name"),)

    seq             = Column(Integer, primary_key=True)
    name            = Column(String, nullable=False)
    business_reg_no = Column(String)
    address         = Column(String)
    withdrawal_date = Column(String)
    created_at      = Column(DateTime, default=datetime.utcnow)


class CompanySearchAlias(Base):
    __tablename__ = "company_search_aliases"
    __table_args__ = (
        Index("idx_aliases_normalized_alias", "normalized_alias_text"),
        Index("idx_aliases_seq", "seq"),
    )

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    seq                   = Column(Integer, ForeignKey("companies.seq"), nullable=False)
    alias_text            = Column(String, nullable=False)
    normalized_alias_text = Column(String, nullable=False)
    alias_type            = Column(String, nullable=False, default="normalized")
    created_at            = Column(DateTime, default=datetime.utcnow)


def _load_env_value(key: str) -> str | None:
    env_value = os.environ.get(key)
    if env_value:
        return env_value.strip().strip("\"'")

    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return None


def resolve_database_url(db_path: str | Path = _DEFAULT_DB_PATH) -> str:
    """SUPABASE_DB_URL / DATABASE_URL 우선, 없으면 로컬 SQLite를 사용한다."""
    env_url = _load_env_value("SUPABASE_DB_URL") or _load_env_value("DATABASE_URL")
    if env_url:
        if env_url.startswith("postgresql://"):
            env_url = env_url.replace("postgresql://", "postgresql+psycopg://", 1)

        if env_url.startswith("postgresql+psycopg://"):
            parsed = urlsplit(env_url)
            filtered_query = [
                (key, value)
                for key, value in parse_qsl(parsed.query, keep_blank_values=True)
                if key.lower() != "pgbouncer"
            ]
            env_url = urlunsplit(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    urlencode(filtered_query),
                    parsed.fragment,
                )
            )
        return env_url

    sqlite_path = Path(db_path)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path}"


def get_engine(db_path: str | Path = _DEFAULT_DB_PATH):
    url = resolve_database_url(db_path)
    connect_args = {}
    if url.startswith("postgresql+psycopg://"):
        # Supabase pooler(pgbouncer) 환경에서는 자동 prepared statement를 끈다.
        connect_args["prepare_threshold"] = None
    return create_engine(url, echo=False, connect_args=connect_args)


def init_db(db_path: str | Path = _DEFAULT_DB_PATH):
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path: str | Path = _DEFAULT_DB_PATH) -> Session:
    engine = get_engine(db_path)
    return sessionmaker(bind=engine)()
