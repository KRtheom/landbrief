-- ============================================================
-- Landbrief DDL — PostgreSQL
-- Version: 0.2.1 (2026-03-01)
-- 변경사항: source_enum 수정(KB 제거, APPLYHOME/ARCH_HUB 추가),
--          dim_complex 추가, apt_seq 인덱스 추가,
--          주석 3건(yyyymm, region_key GLOBAL, is_fallback)
-- ============================================================

-- 1) ENUM types
CREATE TYPE trade_type_enum AS ENUM (
    'APT_SALE_DTL', 'APT_RENT', 'APT_SALE',
    'OFFI_SALE', 'OFFI_RENT',
    'RH_SALE', 'RH_RENT',
    'SH_SALE', 'SH_RENT',
    'COMM_SALE',
    'INDU_SALE',
    'LAND_SALE',
    'PRESALE'
);

CREATE TYPE source_enum AS ENUM (
    'DATA_GO_KR', 'REB_RONE', 'STAT_MOLIT', 'ECOS',
    'HOUSTAT', 'MOIS', 'APPLYHOME', 'ARCH_HUB'
);

CREATE TYPE region_level_enum AS ENUM (
    'GLOBAL', 'SIDO', 'SIGUNGU', 'ZONE'
);

CREATE TYPE etl_status_enum AS ENUM (
    'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED'
);

-- 2) dim_region
CREATE TABLE dim_region (
    sgg_cd      CHAR(5)     PRIMARY KEY,
    sgg_nm      VARCHAR(50) NOT NULL,
    sido_cd     CHAR(2)     NOT NULL,
    sido_nm     VARCHAR(30) NOT NULL,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_region_sido ON dim_region (sido_cd);

-- 3) dim_complex
-- PK: apt_seq (국토부 단지일련번호)
-- 1차 생성: fact_trade_raw에서 추출
-- 2차 보강: 건축물대장 API (좌표, 세대수, 공급면적) — Phase 2 전 완료
CREATE TABLE dim_complex (
    apt_seq     VARCHAR(30) PRIMARY KEY,
    bldg_nm     VARCHAR(200) NOT NULL,
    sgg_cd      CHAR(5)     NOT NULL REFERENCES dim_region(sgg_cd),
    umd_nm      VARCHAR(100),
    lat         NUMERIC,
    lng         NUMERIC,
    households  INTEGER,
    supply_ar   NUMERIC,
    built_year  SMALLINT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_complex_sgg ON dim_complex (sgg_cd);

-- 4) fact_trade_raw
CREATE TABLE fact_trade_raw (
    id                  BIGSERIAL       PRIMARY KEY,
    trade_type          trade_type_enum NOT NULL,
    sgg_cd              CHAR(5)         NOT NULL,
    umd_nm              VARCHAR(100),
    deal_year           SMALLINT,
    deal_month          SMALLINT,
    deal_day            VARCHAR(10),
    deal_amount         VARCHAR(40),
    deposit             VARCHAR(40),
    monthly_rent        VARCHAR(40),
    contract_term       VARCHAR(40),
    contract_type       VARCHAR(20),
    use_rr_right        VARCHAR(10),
    pre_deposit         VARCHAR(40),
    pre_monthly_rent    VARCHAR(40),
    bldg_nm             VARCHAR(200),
    exclu_use_ar        VARCHAR(20),
    floor               VARCHAR(10),
    build_year          VARCHAR(10),
    jibun               VARCHAR(50),
    apt_seq             VARCHAR(30),
    apt_dong            VARCHAR(100),
    umd_cd              VARCHAR(10),
    land_cd             VARCHAR(10),
    bonbun              VARCHAR(10),
    bubun               VARCHAR(10),
    road_nm             VARCHAR(200),
    road_nm_sgg_cd      VARCHAR(10),
    road_nm_cd          VARCHAR(20),
    road_nm_seq         VARCHAR(10),
    road_nm_b_cd        VARCHAR(10),
    road_nm_bonbun      VARCHAR(10),
    road_nm_bubun       VARCHAR(10),
    rgst_date           VARCHAR(10),
    land_leasehold      VARCHAR(10),
    sgg_nm              VARCHAR(50),
    deal_area           VARCHAR(20),
    jimok               VARCHAR(20),
    land_use            VARCHAR(50),
    building_type       VARCHAR(50),
    building_use        VARCHAR(50),
    plottage_ar         VARCHAR(20),
    building_ar         VARCHAR(20),
    total_floor_ar      VARCHAR(20),
    house_type          VARCHAR(50),
    share_dealing       VARCHAR(10),
    cdeal_type          VARCHAR(20),
    cdeal_day           VARCHAR(10),
    dealing_gbn         VARCHAR(20),
    estate_agent        VARCHAR(200),
    sler_gbn            VARCHAR(20),
    buyer_gbn           VARCHAR(20),
    ownership_gbn       VARCHAR(20),
    land_ar             VARCHAR(20),

    -- yyyymm: API 요청 파라미터 DEAL_YMD 원본 저장.
    -- deal_year/deal_month는 API 응답 필드.
    -- deal_year || LPAD(deal_month) 파생이 아님.
    yyyymm              CHAR(6)         NOT NULL,

    source              source_enum     NOT NULL DEFAULT 'DATA_GO_KR',
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- dedup COALESCE 정책:
-- NULL -> '' 통일 (Landbrief VARCHAR 저장 정책)
-- LandScanner(SQLite)는 INTEGER 컬럼 특성상 COALESCE(..., 0) 사용
-- 목적 동일: NULL 행이 dedup 비교에서 누락되지 않도록 확정값 치환
-- 타입 환경 차이에 따른 구현 차이이며, 정책 변경 아님
CREATE UNIQUE INDEX uix_ftr_dedup ON fact_trade_raw (
    trade_type,
    sgg_cd,
    deal_year,
    deal_month,
    COALESCE(deal_day, ''),
    COALESCE(bldg_nm, ''),
    COALESCE(exclu_use_ar, ''),
    COALESCE(floor, ''),
    COALESCE(deal_amount, ''),
    COALESCE(deposit, ''),
    COALESCE(monthly_rent, ''),
    COALESCE(jibun, '')
);

-- 조회용 인덱스
CREATE INDEX idx_ftr_lookup ON fact_trade_raw (trade_type, sgg_cd, yyyymm);
CREATE INDEX idx_ftr_bldg   ON fact_trade_raw (trade_type, sgg_cd, bldg_nm);
CREATE INDEX idx_ftr_aptseq ON fact_trade_raw (trade_type, apt_seq, yyyymm);

-- 5) fact_indicator_month
--
-- is_fallback: 0=실측값, 1=이월/보간값. SMALLINT 유지 (확장 여지).
-- region_key GLOBAL 규칙: region_level='GLOBAL'일 때 region_key='00000'.
CREATE TABLE fact_indicator_month (
    id              BIGSERIAL           PRIMARY KEY,
    indicator_code  VARCHAR(50)         NOT NULL,
    region_level    region_level_enum   NOT NULL,
    region_key      VARCHAR(10)         NOT NULL,
    yyyymm          CHAR(6)             NOT NULL,
    value           NUMERIC,
    source          source_enum         NOT NULL,
    unit            VARCHAR(50)         NOT NULL DEFAULT '',
    is_fallback     SMALLINT            NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uix_fim_dedup ON fact_indicator_month (
    indicator_code, region_level, region_key, yyyymm
);

CREATE INDEX idx_fim_lookup ON fact_indicator_month (indicator_code, region_key, yyyymm);

-- 6) etl_log
CREATE TABLE etl_log (
    id              BIGSERIAL       PRIMARY KEY,
    job_type        VARCHAR(50)     NOT NULL,
    indicator_code  VARCHAR(50),
    sgg_cd          CHAR(5),
    yyyymm          CHAR(6),
    status          etl_status_enum NOT NULL DEFAULT 'RUNNING',
    rows_affected   INTEGER         NOT NULL DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX idx_etl_job ON etl_log (job_type, status, started_at DESC);

-- 7) updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;

$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_region_updated
    BEFORE UPDATE ON dim_region
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_complex_updated
    BEFORE UPDATE ON dim_complex
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_ftr_updated
    BEFORE UPDATE ON fact_trade_raw
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_fim_updated
    BEFORE UPDATE ON fact_indicator_month
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


###v0.2 대비 변경 요약:

source_enum — KB 제거, APPLYHOME·ARCH_HUB 추가. HOUSTAT 유지.

dim_complex 신규 — apt_seq PK, supply_ar(공급면적) 포함, lat/lng/households/built_year nullable, sgg_cd FK.

idx_ftr_aptseq 신규 — trade_type + apt_seq + yyyymm 복합 인덱스. 단지별 시트 조회용.

주석 3건 — yyyymm 저장 규칙, is_fallback 의미, region_key GLOBAL='00000' 규칙.

trg_complex_updated 신규 — dim_complex용 updated_at 트리거.

calendar_month는 ENGINE.md 설계 후 DDL v0.3에서 추가합니다.
###