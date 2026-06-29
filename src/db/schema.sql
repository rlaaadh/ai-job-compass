-- 이직각 DB 스키마
-- 국민연금공단 공공 API 기반

CREATE TABLE IF NOT EXISTS companies (
    seq                 INTEGER PRIMARY KEY,  -- 사업장 식별번호
    name                TEXT    NOT NULL,     -- 사업장명 (wkplNm)
    business_reg_no     TEXT,                 -- 사업자등록번호 (bzowrRgstNo)
    address             TEXT,                 -- 도로명 주소 (wkplRoadNmDtlAddr)
    industry_code       TEXT,                 -- 업종 코드 (wkplIntpCd)
    industry_name       TEXT,                 -- 업종명 (vldtVlKrnNm)
    workplace_type      TEXT,                 -- 사업장 형태 구분 코드 (wkplStylDvcd)
    join_status         TEXT,                 -- 가입 상태 코드 (wkplJnngStcd: 1=가입)
    join_date           TEXT,                 -- 적용일자 yyyymmdd (adptDt)
    employee_count      INTEGER,              -- 현재 가입자 수 (jnngpCnt)
    -- 당월 국민연금 보험료 고지 기준 금액. 실제 급여와 다름 (연금보험료 ≠ 임금)
    monthly_charge_amt  BIGINT,               -- 당월고지금액 (crrmmNtcAmt)
    sido_code           TEXT,                 -- 시도 코드 (ldongAddrMgplDgCd)
    sigungu_code        TEXT,                 -- 시군구 코드 (ldongAddrMgplSgguCd)
    data_created_ym     TEXT,                 -- 데이터 생성 년월 yyyymm (dataCrtYm)
    synced_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS company_monthly_stats (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    seq             INTEGER NOT NULL,   -- 사업장 식별번호 (FK)
    year_month      TEXT    NOT NULL,   -- 조회 년월 yyyymm
    employee_count  INTEGER,            -- 해당 월 가입자 수
    new_joiners     INTEGER,            -- 신규 취득자 수 / 입사자 (nwAcqzrCnt)
    leavers         INTEGER,            -- 상실 가입자 수 / 퇴사자 (lssJnngpCnt)
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seq) REFERENCES companies(seq),
    UNIQUE(seq, year_month)
);

-- 탈퇴 사업장: 폐업 확정이 아닌 리스크 보조 신호로만 활용
CREATE TABLE IF NOT EXISTS withdrawn_companies (
    seq             INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    business_reg_no TEXT,
    address         TEXT,
    withdrawal_date TEXT,               -- 탈퇴일자 yyyymmdd (scsnDt)
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companies_name        ON companies(name);
CREATE INDEX IF NOT EXISTS idx_monthly_stats_seq_ym  ON company_monthly_stats(seq, year_month);
CREATE INDEX IF NOT EXISTS idx_withdrawn_name        ON withdrawn_companies(name);

-- ────────────────────────────────────────────
-- DART (OpenDART) 재무 데이터
-- 설계 기준: docs/dart-api-score-design.html
-- ────────────────────────────────────────────

-- NPS 회사명 ↔ DART corp_code 매핑 키
CREATE TABLE IF NOT EXISTS dart_corp_codes (
    corp_code   TEXT PRIMARY KEY,  -- DART 고유번호 (8자리)
    corp_name   TEXT NOT NULL,     -- 회사명
    stock_code  TEXT,              -- 종목코드 (비상장이면 NULL)
    modify_date TEXT,              -- 최종 변경일 yyyymmdd
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- companies.seq ↔ dart_corp_codes.corp_code 연결 + 기업개황
CREATE TABLE IF NOT EXISTS company_dart_profiles (
    seq         INTEGER PRIMARY KEY,  -- companies.seq FK
    corp_code   TEXT NOT NULL,        -- dart_corp_codes.corp_code FK
    stock_code  TEXT,
    corp_cls    TEXT,                 -- 법인 구분 (Y=유가, K=코스닥, N=비상장 등)
    induty_code TEXT,                 -- 업종 코드
    est_dt      TEXT,                 -- 설립일 yyyymmdd
    acc_mt      TEXT,                 -- 결산월 mm
    synced_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seq) REFERENCES companies(seq),
    FOREIGN KEY (corp_code) REFERENCES dart_corp_codes(corp_code)
);

-- 핵심 재무 계정 원천 (매출, 이익, 자산, 부채, 자본, 현금흐름)
CREATE TABLE IF NOT EXISTS company_financial_accounts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    seq                  INTEGER NOT NULL,   -- companies.seq FK
    biz_year             TEXT NOT NULL,      -- 사업연도 yyyy
    reprt_code           TEXT NOT NULL,      -- 보고서 코드 (11011=사업보고서 등)
    fs_div               TEXT,               -- 재무제표 구분 (CFS=연결, OFS=별도)
    revenue              BIGINT,             -- 매출액
    operating_income     BIGINT,             -- 영업이익
    net_income           BIGINT,             -- 당기순이익
    total_assets         BIGINT,             -- 자산총계
    total_liabilities    BIGINT,             -- 부채총계
    total_equity         BIGINT,             -- 자본총계
    current_assets       BIGINT,             -- 유동자산
    current_liabilities  BIGINT,             -- 유동부채
    operating_cash_flow  BIGINT,             -- 영업활동현금흐름
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seq) REFERENCES companies(seq),
    UNIQUE(seq, biz_year, reprt_code, fs_div)
);

-- 계산된 재무 지표 (성장률, 비율 등)
CREATE TABLE IF NOT EXISTS company_financial_metrics (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    seq                  INTEGER NOT NULL,   -- companies.seq FK
    biz_year             TEXT NOT NULL,      -- 사업연도 yyyy
    reprt_code           TEXT NOT NULL,
    roe                  REAL,               -- 자기자본이익률 (%)
    roa                  REAL,               -- 총자산이익률 (%)
    debt_ratio           REAL,               -- 부채비율 (%)
    current_ratio        REAL,               -- 유동비율 (%)
    operating_margin     REAL,               -- 영업이익률 (%)
    net_margin           REAL,               -- 순이익률 (%)
    revenue_growth_rate  REAL,               -- 매출액증가율 (%)
    asset_growth_rate    REAL,               -- 총자산증가율 (%)
    equity_ratio         REAL,               -- 자기자본비율 (%) = total_equity / total_assets * 100
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seq) REFERENCES companies(seq),
    UNIQUE(seq, biz_year, reprt_code)
);

CREATE INDEX IF NOT EXISTS idx_dart_corp_codes_name       ON dart_corp_codes(corp_name);
CREATE INDEX IF NOT EXISTS idx_dart_profiles_corp_code    ON company_dart_profiles(corp_code);
CREATE INDEX IF NOT EXISTS idx_financial_accounts_seq_yr  ON company_financial_accounts(seq, biz_year);
CREATE INDEX IF NOT EXISTS idx_financial_metrics_seq_yr   ON company_financial_metrics(seq, biz_year);
