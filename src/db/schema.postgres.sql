-- 이직각 Supabase/Postgres 스키마
-- 검색용 companies + 통계 + alias 구조

CREATE TABLE IF NOT EXISTS companies (
    seq                 INTEGER PRIMARY KEY,
    name                TEXT NOT NULL,
    normalized_name     TEXT,
    name_initials       TEXT,
    business_reg_no     TEXT,
    address             TEXT,
    industry_code       TEXT,
    industry_name       TEXT,
    workplace_type      TEXT,
    join_status         TEXT,
    join_date           TEXT,
    employee_count      INTEGER,
    monthly_charge_amt  BIGINT,
    sido_code           TEXT,
    sigungu_code        TEXT,
    data_created_ym     TEXT,
    search_rank         INTEGER DEFAULT 0,
    synced_at           TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_monthly_stats (
    id              BIGSERIAL PRIMARY KEY,
    seq             INTEGER NOT NULL REFERENCES companies(seq) ON DELETE CASCADE,
    year_month      TEXT NOT NULL,
    employee_count  INTEGER,
    new_joiners     INTEGER,
    leavers         INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(seq, year_month)
);

CREATE TABLE IF NOT EXISTS withdrawn_companies (
    seq             INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    business_reg_no TEXT,
    address         TEXT,
    withdrawal_date TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_search_aliases (
    id                    BIGSERIAL PRIMARY KEY,
    seq                   INTEGER NOT NULL REFERENCES companies(seq) ON DELETE CASCADE,
    alias_text            TEXT NOT NULL,
    normalized_alias_text TEXT NOT NULL,
    alias_type            TEXT NOT NULL DEFAULT 'normalized',
    created_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companies_name
    ON companies(name);

CREATE INDEX IF NOT EXISTS idx_companies_normalized_name
    ON companies(normalized_name);

CREATE INDEX IF NOT EXISTS idx_companies_name_initials
    ON companies(name_initials);

CREATE INDEX IF NOT EXISTS idx_companies_employee_count
    ON companies(employee_count DESC);

CREATE INDEX IF NOT EXISTS idx_monthly_stats_seq_ym
    ON company_monthly_stats(seq, year_month);

CREATE INDEX IF NOT EXISTS idx_withdrawn_name
    ON withdrawn_companies(name);

CREATE INDEX IF NOT EXISTS idx_aliases_normalized_alias
    ON company_search_aliases(normalized_alias_text);

CREATE INDEX IF NOT EXISTS idx_aliases_seq
    ON company_search_aliases(seq);
