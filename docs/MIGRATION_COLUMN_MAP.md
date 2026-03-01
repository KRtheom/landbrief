# Migration Column Map (fact_trade_raw)

- 작성일: 2026-02-28 (KST)
- LandScanner DB: `/home/deploy/real_estate_report/data/real_estate.db` (read-only)
- LandScanner 소스: `/home/deploy/real_estate_report` (read-only)
- Landbrief DDL 기준: `docs/DDL.md` (v0.2)

## 1. 컬럼 매핑 테이블

### 1.1 A-1/A-2 통합 매핑 (전 컬럼)

| # | LandScanner 컬럼 | 타입 | NN | DEF | Landbrief 컬럼 | 타입 | NN | DEF | 매핑 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | id | INTEGER | N | - | id | BIGSERIAL | N | - | 미사용 | PG BIGSERIAL 새 채번 |
| 2 | trade_type | TEXT | Y | - | trade_type | trade_type_enum | Y | - | 변환 필요 | TEXT 값을 trade_type_enum으로 캐스팅 |
| 3 | sgg_cd | TEXT | Y | - | sgg_cd | CHAR(5) | Y | - | 직접 매핑 | - |
| 4 | umd_nm | TEXT | N | - | umd_nm | VARCHAR(100) | N | - | 직접 매핑 | - |
| 5 | deal_year | TEXT | Y | - | deal_year | SMALLINT | N | - | 변환 필요 | TEXT -> SMALLINT 캐스팅 |
| 6 | deal_month | TEXT | Y | - | deal_month | SMALLINT | N | - | 변환 필요 | TEXT -> SMALLINT 캐스팅 |
| 7 | deal_day | TEXT | N | - | deal_day | VARCHAR(10) | N | - | 직접 매핑 | - |
| 8 | deal_amount | INTEGER | N | - | deal_amount | VARCHAR(40) | N | - | 직접 매핑 | - |
| 9 | deposit | INTEGER | N | - | deposit | VARCHAR(40) | N | - | 직접 매핑 | - |
| 10 | monthly_rent | INTEGER | N | - | monthly_rent | VARCHAR(40) | N | - | 직접 매핑 | - |
| 11 | contract_term | TEXT | N | - | contract_term | VARCHAR(40) | N | - | 직접 매핑 | - |
| 12 | contract_type | TEXT | N | - | contract_type | VARCHAR(20) | N | - | 직접 매핑 | - |
| 13 | use_rr_right | TEXT | N | - | use_rr_right | VARCHAR(10) | N | - | 직접 매핑 | - |
| 14 | pre_deposit | INTEGER | N | - | pre_deposit | VARCHAR(40) | N | - | 직접 매핑 | - |
| 15 | pre_monthly_rent | INTEGER | N | - | pre_monthly_rent | VARCHAR(40) | N | - | 직접 매핑 | - |
| 16 | bldg_nm | TEXT | N | - | bldg_nm | VARCHAR(200) | N | - | 직접 매핑 | - |
| 17 | exclu_use_ar | REAL | N | - | exclu_use_ar | VARCHAR(20) | N | - | 직접 매핑 | - |
| 18 | floor | TEXT | N | - | floor | VARCHAR(10) | N | - | 직접 매핑 | - |
| 19 | build_year | TEXT | N | - | build_year | VARCHAR(10) | N | - | 직접 매핑 | - |
| 20 | jibun | TEXT | N | - | jibun | VARCHAR(50) | N | - | 직접 매핑 | - |
| 21 | apt_seq | TEXT | N | - | apt_seq | VARCHAR(30) | N | - | 직접 매핑 | - |
| 22 | apt_dong | TEXT | N | - | apt_dong | VARCHAR(100) | N | - | 직접 매핑 | - |
| 23 | umd_cd | TEXT | N | - | umd_cd | VARCHAR(10) | N | - | 직접 매핑 | - |
| 24 | land_cd | TEXT | N | - | land_cd | VARCHAR(10) | N | - | 직접 매핑 | - |
| 25 | bonbun | TEXT | N | - | bonbun | VARCHAR(10) | N | - | 직접 매핑 | - |
| 26 | bubun | TEXT | N | - | bubun | VARCHAR(10) | N | - | 직접 매핑 | - |
| 27 | road_nm | TEXT | N | - | road_nm | VARCHAR(200) | N | - | 직접 매핑 | - |
| 28 | road_nm_sgg_cd | TEXT | N | - | road_nm_sgg_cd | VARCHAR(10) | N | - | 직접 매핑 | - |
| 29 | road_nm_cd | TEXT | N | - | road_nm_cd | VARCHAR(20) | N | - | 직접 매핑 | - |
| 30 | road_nm_seq | TEXT | N | - | road_nm_seq | VARCHAR(10) | N | - | 직접 매핑 | - |
| 31 | road_nm_b_cd | TEXT | N | - | road_nm_b_cd | VARCHAR(10) | N | - | 직접 매핑 | - |
| 32 | road_nm_bonbun | TEXT | N | - | road_nm_bonbun | VARCHAR(10) | N | - | 직접 매핑 | - |
| 33 | road_nm_bubun | TEXT | N | - | road_nm_bubun | VARCHAR(10) | N | - | 직접 매핑 | - |
| 34 | rgst_date | TEXT | N | - | rgst_date | VARCHAR(10) | N | - | 직접 매핑 | - |
| 35 | land_leasehold | TEXT | N | - | land_leasehold | VARCHAR(10) | N | - | 직접 매핑 | - |
| 36 | sgg_nm | TEXT | N | - | sgg_nm | VARCHAR(50) | N | - | 직접 매핑 | - |
| 37 | deal_area | REAL | N | - | deal_area | VARCHAR(20) | N | - | 직접 매핑 | - |
| 38 | jimok | TEXT | N | - | jimok | VARCHAR(20) | N | - | 직접 매핑 | - |
| 39 | land_use | TEXT | N | - | land_use | VARCHAR(50) | N | - | 직접 매핑 | - |
| 40 | building_type | TEXT | N | - | building_type | VARCHAR(50) | N | - | 직접 매핑 | - |
| 41 | building_use | TEXT | N | - | building_use | VARCHAR(50) | N | - | 직접 매핑 | - |
| 42 | plottage_ar | REAL | N | - | plottage_ar | VARCHAR(20) | N | - | 직접 매핑 | - |
| 43 | building_ar | REAL | N | - | building_ar | VARCHAR(20) | N | - | 직접 매핑 | - |
| 44 | total_floor_ar | REAL | N | - | total_floor_ar | VARCHAR(20) | N | - | 직접 매핑 | - |
| 45 | house_type | TEXT | N | - | house_type | VARCHAR(50) | N | - | 직접 매핑 | - |
| 46 | share_dealing | TEXT | N | - | share_dealing | VARCHAR(10) | N | - | 직접 매핑 | - |
| 47 | cdeal_type | TEXT | N | - | cdeal_type | VARCHAR(20) | N | - | 직접 매핑 | - |
| 48 | cdeal_day | TEXT | N | - | cdeal_day | VARCHAR(10) | N | - | 직접 매핑 | - |
| 49 | dealing_gbn | TEXT | N | - | dealing_gbn | VARCHAR(20) | N | - | 직접 매핑 | - |
| 50 | estate_agent | TEXT | N | - | estate_agent | VARCHAR(200) | N | - | 직접 매핑 | - |
| 51 | sler_gbn | TEXT | N | - | sler_gbn | VARCHAR(20) | N | - | 직접 매핑 | - |
| 52 | buyer_gbn | TEXT | N | - | buyer_gbn | VARCHAR(20) | N | - | 직접 매핑 | - |
| 53 | yyyymm | TEXT | Y | - | yyyymm | CHAR(6) | Y | - | 직접 매핑 | - |
| 54 | source | TEXT | N | 'DATA_GO_KR' | source | source_enum | Y | 'DATA_GO_KR' | 변환 필요 | TEXT -> source_enum 캐스팅 |
| 55 | created_at | TEXT | N | datetime('now','localtime') | created_at | TIMESTAMPTZ | Y | NOW() | 변환 필요 | TEXT(localtime) -> TIMESTAMPTZ(UTC 권장) |
| 56 | updated_at | TEXT | N | datetime('now','localtime') | updated_at | TIMESTAMPTZ | Y | NOW() | 변환 필요 | TEXT(localtime) -> TIMESTAMPTZ(UTC 권장) |
| 57 | ownership_gbn | TEXT | N | - | ownership_gbn | VARCHAR(20) | N | - | 직접 매핑 | - |
| 58 | land_ar | REAL | N | - | land_ar | VARCHAR(20) | N | - | 직접 매핑 | - |

### 1.2 매핑 분류 요약

- 직접 매핑: 51개
- 변환 필요: 6개 (`trade_type`, `deal_year`, `deal_month`, `source`, `created_at`, `updated_at`)
- 미사용: 1개 (`id`)
- 이름 변경: 0개
- 신규(DDL에만 존재): 0개

## 2. 불일치 목록 및 처리 방안

### 2.1 LandScanner에만 있고 Landbrief에 없는 컬럼
- 없음

### 2.2 Landbrief에만 있고 LandScanner에 없는 컬럼
- 없음

### 2.3 타입/제약 불일치

1. `trade_type`: `TEXT` vs `trade_type_enum`
- 처리: `::trade_type_enum` 캐스팅 이관
- 사전 점검: LandScanner distinct 값 12종이 enum 허용값과 일치 확인

2. `deal_year`, `deal_month`: `TEXT` vs `SMALLINT`
- 처리: 숫자 캐스팅 후 이관 (`NULLIF(col,'')::smallint`)
- 사전 점검: `deal_year` 범위 2019~2026 확인, 필터 조건(`>=2020`) 적용

3. `source`: `TEXT` vs `source_enum`
- 처리: `::source_enum` 캐스팅
- 사전 점검: 현재 distinct 값 `DATA_GO_KR` 단일값 확인

4. `created_at`, `updated_at`: `TEXT(localtime)` vs `TIMESTAMPTZ`
- 처리: 로컬시간 문자열 파싱 후 KST 기준 `timestamptz` 변환
- 권장: 이관 파이프라인에서 UTC 정규화

5. 수치형/문자형 표현 차이 (`INTEGER/REAL` -> `VARCHAR`)
- 처리: 문자열 캐스팅 후 이관 (`col::text`)
- 비고: Landbrief는 원천값 보존 전략(VARCHAR) 채택

### 2.4 dedup 기준 불일치(중요)

- LandScanner `uix_ftr_dedup`: 숫자 필드에 `COALESCE(..., 0)` 사용
  - `exclu_use_ar`, `deal_amount`, `deposit`, `monthly_rent`
- Landbrief `uix_ftr_dedup`: 동일 필드에 `COALESCE(..., '')` 사용
- 영향: `NULL`과 `0`을 같은 값으로 볼지 여부가 시스템 간 달라질 수 있음
- 처리 방안:
  - 이관 전 dedup 정책 하나로 통일 (권장: LandScanner 운영 기준과 일치)
  - 최소한 초기 이관 시에는 LandScanner dedup 기준으로 선검증 후 적재

## 3. dedup 키 정의

- LandScanner:
  - 키 조합:
    - `trade_type`
    - `sgg_cd`
    - `deal_year`
    - `deal_month`
    - `COALESCE(deal_day, '')`
    - `COALESCE(bldg_nm, '')`
    - `COALESCE(exclu_use_ar, 0)`
    - `COALESCE(floor, '')`
    - `COALESCE(deal_amount, 0)`
    - `COALESCE(deposit, 0)`
    - `COALESCE(monthly_rent, 0)`
    - `COALESCE(jibun, '')`
  - 소스 근거:
    - `scripts/prefetch_trade_raw.py:273-287`
    - `scripts/prefetch_trade_raw.py:487-492` (`INSERT OR IGNORE` 설명/적용)
    - `scripts/migrate_trade_raw_dedup.py:14-27`
    - `scripts/migrate_trade_raw_dedup.py:230-244`
  - SQLite 스키마 근거:
    - `sqlite_master` index `uix_ftr_dedup` 정의 확인

- Landbrief DDL v0.2:
  - `docs/DDL.md:106-118`의 `uix_ftr_dedup`
  - 조합 컬럼은 동일하나 `COALESCE` 기본값이 일부 상이(`0` vs `''`)

- 일치 여부: **N(부분 불일치)**
- 불일치 조치:
  - DDL dedup 정책 확정 전, 운영계(LandScanner) 기준 중복 검사 결과를 기준으로 이관
  - Landbrief `uix_ftr_dedup`의 COALESCE 기본값 정합성 재검토 권장

## 4. 중복 검사 결과

- 검사 기준: LandScanner dedup 키 조합(위 12요소)
- 총 건수: 14,152,214
- 중복 키 수: 0
- 중복 행 합계: 0
- 초과 행 수(`cnt-1` 합계): 0
- `trade_type`별 중복 분포: 중복 없음
- 상위 10건 샘플: 중복 없음

## 5. 이관 SQL 가이드

- 필터: `deal_year >= 2020`
- `id`: PostgreSQL `BIGSERIAL` 새 채번 (source `id` 미이관)
- dedup_key: PostgreSQL 측 `uix_ftr_dedup`로 보장 (정책 확정 필요)

예시(개념 SQL):

```sql
INSERT INTO fact_trade_raw (
    trade_type, sgg_cd, umd_nm, deal_year, deal_month, deal_day,
    deal_amount, deposit, monthly_rent, contract_term, contract_type,
    use_rr_right, pre_deposit, pre_monthly_rent, bldg_nm, exclu_use_ar,
    floor, build_year, jibun, apt_seq, apt_dong, umd_cd, land_cd, bonbun, bubun,
    road_nm, road_nm_sgg_cd, road_nm_cd, road_nm_seq, road_nm_b_cd,
    road_nm_bonbun, road_nm_bubun, rgst_date, land_leasehold, sgg_nm, deal_area,
    jimok, land_use, building_type, building_use, plottage_ar, building_ar,
    total_floor_ar, house_type, share_dealing, cdeal_type, cdeal_day, dealing_gbn,
    estate_agent, sler_gbn, buyer_gbn, ownership_gbn, land_ar, yyyymm,
    source, created_at, updated_at
)
SELECT
    trade_type::trade_type_enum,
    sgg_cd,
    umd_nm,
    NULLIF(deal_year, '')::smallint,
    NULLIF(deal_month, '')::smallint,
    deal_day,
    deal_amount::text,
    deposit::text,
    monthly_rent::text,
    contract_term,
    contract_type,
    use_rr_right,
    pre_deposit::text,
    pre_monthly_rent::text,
    bldg_nm,
    exclu_use_ar::text,
    floor,
    build_year,
    jibun,
    apt_seq,
    apt_dong,
    umd_cd,
    land_cd,
    bonbun,
    bubun,
    road_nm,
    road_nm_sgg_cd,
    road_nm_cd,
    road_nm_seq,
    road_nm_b_cd,
    road_nm_bonbun,
    road_nm_bubun,
    rgst_date,
    land_leasehold,
    sgg_nm,
    deal_area::text,
    jimok,
    land_use,
    building_type,
    building_use,
    plottage_ar::text,
    building_ar::text,
    total_floor_ar::text,
    house_type,
    share_dealing,
    cdeal_type,
    cdeal_day,
    dealing_gbn,
    estate_agent,
    sler_gbn,
    buyer_gbn,
    ownership_gbn,
    land_ar::text,
    yyyymm,
    source::source_enum,
    -- created_at/updated_at는 ETL에서 KST->UTC 변환 후 주입 권장
    created_at::timestamptz,
    updated_at::timestamptz
FROM staging_fact_trade_raw
WHERE NULLIF(deal_year, '')::int >= 2020;
```

## D-1. 자율 추가 항목: 소형 길이 제약 사전 점검

- 점검 항목 최대 길이:
  - `sgg_cd=5`, `yyyymm=6`, `deal_day=2`, `build_year=4`, `floor=2`
  - `road_nm_sgg_cd=5`, `road_nm_b_cd=1`, `road_nm_bonbun=5`, `road_nm_bubun=5`
  - `rgst_date=8`, `cdeal_day=8`, `cdeal_type=1`, `sler_gbn=4`, `buyer_gbn=4`
- 결론: DDL의 소형 길이 제한(CHAR/VARCHAR) 대비 즉시 초과 징후 없음

## D-2. 자율 추가 항목: 컬럼 순서 이력 차이

- LandScanner 실제 테이블 SQL에서 `ownership_gbn`, `land_ar`가 말미에 추가된 형태로 확인됨
- 컬럼명/타입은 동일하므로 이관 시 **이름 기반 매핑**이면 문제 없음
- 주의: `SELECT *` 기반 순서 매핑 금지

## E. 소스 확인 사항

1. `dedup_key` 물리 컬럼은 LandScanner `fact_trade_raw`에 존재하지 않음
- 실제 dedup은 `uix_ftr_dedup`(표현식 UNIQUE INDEX) + `INSERT OR IGNORE` 조합으로 구현됨

2. 지시 경로 표기 차이
- 지시서의 `~/landbrief/docs/DDL.md`와 현재 로컬 경로 `d:/landbrief/docs/DDL.md`는 동일 대상(환경 차이)으로 처리

3. `fact_trade_raw` 총건수 최신값 차이
- 이번 실측 기준 `14,152,214`건 (기존 handover 수치와 차이 존재)

## F. 개선 제안

1. dedup 정책 단일화
- LandScanner/ Landbrief 간 `COALESCE` 기본값(`0` vs `''`)을 통일해 이관 후 중복 판정 일관성 확보

2. 타임스탬프 표준화
- `created_at/updated_at` 이관 시 KST 문자열 파싱 규칙과 UTC 저장 규칙을 ETL에 명시

3. 이관 SQL 안전장치
- `WHERE NULLIF(deal_year,'') ~ '^[0-9]{4}$'` 같은 숫자 형식 가드로 캐스팅 오류 방지

