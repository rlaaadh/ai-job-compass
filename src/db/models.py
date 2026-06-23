from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Column, DateTime, Integer, String, UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "job_compass.db"


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    seq              = Column(Integer, primary_key=True)
    name             = Column(String, nullable=False)
    business_reg_no  = Column(String)
    address          = Column(String)
    industry_code    = Column(String)
    industry_name    = Column(String)
    workplace_type   = Column(String)
    join_status      = Column(String)
    join_date        = Column(String)
    employee_count   = Column(Integer)
    # 국민연금 보험료 고지 기준 — 실제 임금과 다름, 연봉 추정 참고값으로만 사용
    monthly_charge_amt = Column(Integer)
    sido_code        = Column(String)
    sigungu_code     = Column(String)
    data_created_ym  = Column(String)
    synced_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at       = Column(DateTime, default=datetime.utcnow)


class CompanyMonthlyStats(Base):
    __tablename__ = "company_monthly_stats"
    __table_args__ = (UniqueConstraint("seq", "year_month"),)

    id             = Column(Integer, primary_key=True, autoincrement=True)
    seq            = Column(Integer, nullable=False)
    year_month     = Column(String, nullable=False)
    employee_count = Column(Integer)
    new_joiners    = Column(Integer)   # 신규 취득자 (입사자)
    leavers        = Column(Integer)   # 상실 가입자 (퇴사자)
    created_at     = Column(DateTime, default=datetime.utcnow)


class WithdrawnCompany(Base):
    __tablename__ = "withdrawn_companies"

    seq             = Column(Integer, primary_key=True)
    name            = Column(String, nullable=False)
    business_reg_no = Column(String)
    address         = Column(String)
    withdrawal_date = Column(String)
    created_at      = Column(DateTime, default=datetime.utcnow)


def get_engine(db_path: str | Path = _DEFAULT_DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db(db_path: str | Path = _DEFAULT_DB_PATH):
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path: str | Path = _DEFAULT_DB_PATH) -> Session:
    engine = get_engine(db_path)
    return sessionmaker(bind=engine)()
