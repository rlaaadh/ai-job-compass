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
