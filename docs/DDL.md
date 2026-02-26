-- ============================================================
-- Landbrief G2 DDL — PostgreSQL
-- Version: 0.2 (2026-02-26)
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
    'REB_RONE', 'STAT_MOLIT', 'ECOS', 'HOUSTAT', 'MOIS', 'DATA_GO_KR'
);

CREATE TYPE region_level_enum AS ENUM (
    'GLOBAL', 'SIDO', 'SIGUNGU'
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

-- 3) fact_trade_raw
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
    yyyymm              CHAR(6)         NOT NULL,
    source              source_enum     NOT NULL DEFAULT 'DATA_GO_KR',
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- dedup index (LandScanner 원본 기준, COALESCE 통일)
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

-- 4) fact_indicator_month
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

-- 5) etl_log
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

-- 6) updated_at 자동 갱신 트리거
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

CREATE TRIGGER trg_ftr_updated
    BEFORE UPDATE ON fact_trade_raw
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_fim_updated
    BEFORE UPDATE ON fact_indicator_month
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();