


```markdown
# Landbrief Handover v000 (2026-02-25)

> **목적**: 새 채팅 세션에서 프로젝트 컨텍스트를 완전히 복원하기 위한 인수인계서.
> **작성 기준**: 2026-02-25 00:00 KST 시점.
> **저장 경로**: `~/landbrief/docs/handover/HANDOVER_v000_20260225.md`


---

## 1. 프로젝트 개요

Landbrief는 PF(프로젝트 파이낸싱) 사업성 평가 보고서 자동화 서비스이다.

- **Phase 1**: 공공 통계 기반 3페이지 검증 리포트 (공적 수치 대조용)
- **Phase 2**: 중개사·금융기관 대상 시장 해설 리포트
- **전신**: LandScanner (실거래가 수집·지표 파이프라인). 서비스는 종료 예정이나, 수집된 Raw 데이터와 ETL 로직을 Landbrief가 승계한다.
- **운영 형태**: 1인 파일럿. 과도한 스코프 확장 금지.


---

## 2. 서버 환경

| 항목 | 값 |
|---|---|
| OS | Ubuntu 24.04.4 LTS |
| CPU / RAM | i7-10700 / 32 GB |
| SSH | `ssh -p 2222 deploy@122.45.64.200` |
| UFW | 2222/tcp만 허용 |
| 타임존 | KST (Asia/Seoul) |
| Python | 3.12, venv 사용 |
| 프로젝트 경로 (LandScanner) | `~/real_estate_report` |
| 프로젝트 경로 (Landbrief) | `~/landbrief` (신규 생성 예정) |
| 백업 | Synology rsync |
| 향후 스택 | FastAPI, Next.js, Nginx + systemd/PM2 |


---

## 3. Git 현황

| 항목 | 값 |
|---|---|
| 저장소 | `https://github.com/KRtheom/real-estate-report.git` (private) |
| 서버 반영 커밋 | fa15c5c (G23) |
| 미반영 커밋 | d8a62d5 (G24) — 문서 정리, 중복 제거, 정본 체계 확립 |
| Landbrief 저장소 | 미생성 (G2 DDL 확정 후 초기화 예정) |

### 주요 커밋 이력 (Sprint 2~현재)

G24 d8a62d5 → G23 fa15c5c (서버) → G22 98ec998 → G21 962d015 → G20 0d19e54 → G19 ece6033 → G18 e47cfae → … → G6-A 42a6976

Landbrief 첫 커밋: cf3d336 (G1 DECISIONS.md)


---

## 4. 확정 사항

### 4-1. 최종 12종 지표

| # | 코드 | 설명 | API 출처 | API 키 변수 |
|---|---|---|---|---|
| 1 | APT_SALE_DTL | 아파트 매매 실거래 | 국토부 실거래 OpenAPI | DATA_GO_KR_API_KEY |
| 2 | APT_RENT | 아파트 전월세 실거래 | 국토부 실거래 OpenAPI | DATA_GO_KR_API_KEY |
| 3 | REB_SALE_PRICE_INDEX | 매매가격지수 | R-ONE | REB_API_KEY |
| 4 | REB_TRADE_VOLUME | 매매거래량 | R-ONE | REB_API_KEY |
| 5 | REB_RENT_PRICE_INDEX | 전세가격지수 | R-ONE | REB_API_KEY |
| 6 | UNSOLD_UNITS_SIGUNGU | 미분양 (시군구) | STAT_MOLIT | MOLIT_STAT_API_KEY |
| 7 | UNSOLD_UNITS_COMPLETED | 준공후 미분양 | STAT_MOLIT | MOLIT_STAT_API_KEY |
| 8 | MACRO_BASE_RATE | 기준금리 | ECOS | ECOS_API_KEY |
| 9 | HF_PIR | 주택구입부담지수 (PIR) | HUG | HUG_API_KEY |
| 10 | DEMO_POPULATION | 인구 | KOSIS | KOSIS_API_KEY |
| 11 | DEMO_HOUSEHOLD | 세대수 | KOSIS | KOSIS_API_KEY |
| 12 | SUPPLY_INCOMING | 입주예정물량 | 한국부동산원 (odcloud) | DATA_GO_KR_API_KEY |

### 4-2. SUPPLY_INCOMING 상세

- **엔드포인트**: `GET https://api.odcloud.kr/api/15111714/v1/uddi:0b257760-ac19-4841-adb4-b38b4d153397`
- **인증**: `serviceKey` 쿼리 파라미터 (DATA_GO_KR_API_KEY)
- **총 건수**: 697건 (2025-06 기준)
- **갱신 주기**: 반기 1회 (다음 갱신 2026-01-27 예정)
- **핵심 필드**: 연월, 지역, 사업유형, 주소, 주택명, 세대수
- **시군구 매핑**: `주소` 필드에서 시군구명 파싱 (예: "강원특별자치도 강릉시 견소동 219-0" → 강릉시)
- **수집 방식**: `perPage=700`으로 1회 호출 전체 수집
- **한계**: 반기 갱신이므로 월별 Mart에는 스냅샷 형태로 적재

### 4-3. 드랍/제외 항목

- **KB 부동산 지수**: 라이선스 리스크 — 완전 삭제 (LandScanner DB에서도 제거)
- **상업용 R-ONE 10종**: Phase 1 스코프 밖 — 추후 datasets.yml 추가로 확장 가능
- **CONDITIONAL 6종**: 안정성/라이선스 미확인 — 보류
- **SUPPLY_STARTS (착공실적)**: STAT_MOLIT form_id=5386, 시도 단위만 제공 — 시군구 불가로 보류
- **ArchPmsService 인허가 데이터**: 500 에러 지속, bjdongCd 필수 — 보류

### 4-4. 설계 원칙 (DECISIONS.md 주요 항목)

- DB 저장: UTC, 리포트 출력: KST
- BOM 없음
- Mart 기반 리포트 생성
- PDF 자동 삭제 정책
- 금칙어 필터 (승인, 부결, 위험 등)
- 원자적 ETL swap (Mart)
- 공적 통계 정정 시 meta_formula_version 로깅 후 Mart 재계산
- 입력값 검증: 분양가 5~80백만원/3.3㎡, 기간 1~60개월, 세대수 양의 정수
- 파이프라인 확장: datasets.yml에 항목 추가 + 수집 함수 1개 작성으로 완료 (스키마 변경 불필요)


---

## 5. DB 현황 (LandScanner — Landbrief 이관 대상)

### 5-1. DB 파일 위치

- **실제 경로**: `~/real_estate_report/data/real_estate.db` (SQLite)
- **빈 파일**: `~/real_estate_report/db/real_estate.db` (사용하지 않음)
- 문서에는 `db/` 경로로 기재되어 있으나 실제 데이터는 `data/`에 있음

### 5-2. 테이블 현황 (2026-02-25 기준)

| 테이블 | 행 수 | 컬럼 수 | 비고 |
|---|---|---|---|
| fact_trade_raw | ~5,724,225 | 58 | 12종 실거래, prefetch 진행 중 |
| fact_indicator_month | 283 | 10 | 17개 지표 (강남구 기준) |
| dim_region | 269 | 5 | 17시도 + 268시군구 (GLOBAL 포함하여 269) |
| dim_zone | 0 | 5 | 미실행 |
| etl_trade_raw_log | ~27,978 | 9 | prefetch 진행 추적 |
| etl_run_log | 162 | 6 | 지표 ETL 실행 로그 |
| etl_run_log_legacy | 0 | 11 | 미사용 |
| raw_api_log | 0 | 14 | 미사용 |

### 5-3. fact_trade_raw 유형별 건수

| trade_type | 건수 |
|---|---|
| APT_RENT | ~3,180,130 |
| APT_SALE_DTL | ~1,363,349 |
| RH_RENT | ~383,826 |
| SH_RENT | ~380,859 |
| OFFI_RENT | ~250,364 |
| RH_SALE | ~85,179 |
| OFFI_SALE | ~30,092 |
| COMM_SALE | ~27,712 |
| SH_SALE | ~10,003 |
| INDU_SALE | ~3,318 |
| PRESALE | ~3,031 |
| LAND_SALE | ~1,732 |

### 5-4. 문서 vs 실제 스키마 차이 (중요)

| 인수인계 문서 컬럼명 | 실제 DB 컬럼명 |
|---|---|
| sigungu_code | sgg_cd |
| deal_ymd | yyyymm (+ deal_year, deal_month 별도) |
| apt_name | bldg_nm |
| exclusive_area | exclu_use_ar |

**Landbrief DDL은 반드시 실제 DB 컬럼명 기준으로 작성할 것.**

### 5-5. 핵심 인덱스

- `uix_ftr_dedup`: 12개 컬럼 COALESCE 기반 UNIQUE 인덱스 (중복 방지)
- `idx_ftr_type_region`: trade_type, sgg_cd
- `idx_ftr_yyyymm`: yyyymm
- `idx_ftr_bldg`: bldg_nm, sgg_cd

### 5-6. fact_indicator_month 지표 목록 (SUCCESS 17건)

REB_SALE_PRICE_INDEX, REB_TRADE_VOLUME, REB_RENT_PRICE_INDEX, UNSOLD_UNITS_SIGUNGU, UNSOLD_UNITS_COMPLETED, MACRO_BASE_RATE, HF_PIR, DEMO_POPULATION, DEMO_HOUSEHOLD, DEMO_POP_CHANGE 등 17종. PENDING 7건은 미수집.


---

## 6. LandScanner Prefetch 현황

| 항목 | 값 |
|---|---|
| PID | 436797 (재시작됨, 이전 232708 종료) |
| 대상 | 12종 × 268시군구 × 36개월 = 115,776건 |
| 완료 | ~27,978건 (etl_trade_raw_log 기준, ~24%) |
| 속도 | ~1.3초/건 |
| 예상 완료 | 2/27 저녁 ~ 2/28 |
| 로그 | `~/real_estate_report/logs/prefetch_all.log` |
| resume | 지원됨 — 재시작 시 완료 건 스킵 |
| 완료 후 | 데이터 검증 → LandScanner 서비스 종료 → Landbrief로 이관 |


---

## 7. 데이터 품질 점검 (미완료)

### 점검 스크립트

12개 항목을 점검하는 Python 스크립트가 준비되어 있으며 서버에서 실행 대기 중이다.

**점검 항목:**
1. 총 건수
2. 유형별 건수
3. 수집 시군구 수
4. 계약월 범위
5. 핵심 14개 컬럼 NULL/빈값 비율 (30% 초과 시 경고)
6. deal_amount ≤ 0 이상값
7. 임대 유형 deposit/monthly_rent NULL 비율
8. 12개 dedup 키 기준 중복 의심 건수
9. 시군구별 건수 분포 (상위/하위 10)
10. 최근 적재 시점
11. ETL 로그 성공/실패 현황
12. fact_indicator_month 지표별 건수

**실행 명령**: `cd ~/real_estate_report && source venv/bin/activate && python3 << 'PYEOF' ... PYEOF`
(전체 스크립트는 이전 세션에서 제공됨 — 이 인수인계서 하단 부록 A 참조)

### 실행 후 조치

결과를 바탕으로 Landbrief DDL에 반영할 사항 결정:
- NOT NULL 제약 대상 컬럼
- 데이터 타입 조정 (TEXT → INTEGER 등)
- 추가 인덱스 필요 여부
- 이관 시 정제/변환 규칙


---

## 8. 작업 진행 상태

### Landbrief 태스크

| 태스크 | 상태 | 비고 |
|---|---|---|
| G1: DECISIONS.md | ✅ 완료 | 커밋 cf3d336 |
| G2: DDL (001_init.sql + init_db.py) | ⏳ 대기 | 12종 확정, 품질 점검 후 착수 |
| G3: config/datasets.yml | 대기 | 12종 지표 정의 |
| G4: src/db_utils.py | 대기 | LandScanner 유틸리티 재사용 |
| G5: ETL 배치 스크립트 | 대기 | 11 API + SUPPLY_INCOMING, Mart swap, 알림 |
| G6~G10: Backend/Frontend | 대기 | FastAPI, PDF, Next.js, Nginx |

### LandScanner 잔여 태스크

| 태스크 | 상태 |
|---|---|
| 전국 prefetch 완료 | 진행 중 (~24%) |
| 데이터 품질 점검 | 스크립트 준비, 실행 대기 |
| KB 등 드랍 항목 삭제 | 미실행 |
| G24 pull | 미실행 (prefetch 완료 후) |
| DECISIONS.md 오타 수정 (2025→2026) | 미실행 |
| 서비스 종료 | prefetch + 검증 완료 후 |


---

## 9. 미결 사항 / 블로커

| 항목 | 상태 | 영향 |
|---|---|---|
| 데이터 품질 점검 미실행 | 스크립트 준비됨 | G2 DDL 설계에 영향 |
| SUPPLY_INCOMING 반기 갱신 한계 | 인지됨, 수용 | 스냅샷 적재 방식 |
| 착공실적 시군구 단위 불가 | 보류 | 엑셀 크롤링 또는 포기 |
| busy_timeout 미설정 | P0 | DB 경쟁 방지 필요 |
| serviceKey 로그 평문 노출 | P1 | 마스킹 패치 필요 |
| dim_region 자동 적재 미구현 | P2 | 수동 적재로 대체 중 |
| API 한도 10k→1k 축소 (3/5 전후) | 인지됨 | prefetch 완료 시 영향 없음 |


---

## 10. API 호출 한도

| API | 일일 한도 | 비고 |
|---|---|---|
| data.go.kr | 10,000건/일 (토요일 1,000) | 2026-03-05 전후 1,000으로 축소 예정 |
| R-ONE | 명시적 한도 없음 | |
| STAT_MOLIT | 명시적 한도 없음 | |
| ECOS | 명시적 한도 없음 | |
| HUG | 명시적 한도 없음 | |
| KOSIS | 명시적 한도 없음 | |
| odcloud (SUPPLY_INCOMING) | DATA_GO_KR_API_KEY 공유 | |


---

## 11. .env 키 목록

| 변수명 | 길이 | 형식 | 용도 |
|---|---|---|---|
| DATA_GO_KR_API_KEY | 64 | 문자열 | 실거래 OpenAPI + odcloud |
| REB_API_KEY | 32 | 문자열 | R-ONE 지표 |
| ECOS_API_KEY | 20 | 문자열 | 한국은행 기준금리 |
| KOSIS_API_KEY | 44 | Base64 | 통계청 인구/세대 |
| HUG_API_KEY | 36 | UUID | 주택금융공사 PIR |
| MOLIT_STAT_API_KEY | 32 | 문자열 | 통계누리 미분양/착공 |

**주의**: Sprint 2에서 HUG_API_KEY ↔ MOLIT_STAT_API_KEY가 뒤바뀐 사건 있음. 수정 시 반드시 `datasets.yml`과 대조할 것.

HOUSTAT_API_KEY (len32)는 Landbrief에서 미사용 — 삭제 가능.


---

## 12. 참조 파일 경로

### LandScanner (~/real_estate_report)

| 파일 | 용도 |
|---|---|
| docs/DECISIONS.md | 설계 결정 문서 |
| data/real_estate.db | 실제 DB (fact_trade_raw 등) |
| migrations/001_init.sql | DDL 정의 |
| config/datasets.yml | 지표/데이터셋 정의 (v2.3) |
| collectors/api_molit.py | STAT_MOLIT 수집기 |
| scripts/load_all.py | 지표 ETL 메인 |
| scripts/prefetch_trade_raw.py | 실거래 전국 수집 |
| logs/prefetch_all.log | prefetch 로그 |
| docs/API_SPEC.md | API 스펙 문서 |
| docs/ARCHITECTURE.md | 아키텍처 문서 |
| docs/DATA_CATALOG.md | 데이터 카탈로그 |
| docs/DOMAIN_MODEL.md | 도메인 모델 |
| docs/pg_compat_report.md | PostgreSQL 마이그레이션 리포트 |

### Landbrief (~/landbrief — 생성 예정)

| 파일 | 용도 |
|---|---|
| docs/DECISIONS.md | 설계 결정 (커밋 cf3d336) |
| docs/handover/ | 인수인계서 버전별 저장 |
| db/migrations/001_init.sql | DDL (G2에서 생성) |
| config/datasets.yml | 12종 지표 정의 (G3에서 생성) |
| src/db_utils.py | DB 유틸리티 (G4에서 생성) |


---

## 13. 작업 프로세스

1. **지시서 작성** → 2. **코드 실행** → 3. **diff 리뷰** → 4. **Git push** → 5. **서버 pull** → 6. **동적 검증**

- DECISIONS.md 제약은 반드시 인라인 준수
- 수행 불가 시 `BLOCKED: [사유]` 출력
- 인수인계서는 세션 종료 시 또는 주요 마일스톤마다 새 버전 커밋


---

## 14. 다음 단계 (우선순위순)

1. 데이터 품질 점검 스크립트 실행 → 결과 분석
2. 결과 반영하여 G2 DDL 설계 (13 테이블: 4 meta, 2 dimension, 2 fact, 2 ETL, 1 Mart, 2 business)
3. G2 커밋 → G3~G10 순차 진행
4. LandScanner prefetch 완료 확인 → 데이터 검증 → KB 삭제 → 이관 → 서비스 종료


---

## 부록 A: 데이터 품질 점검 스크립트

```bash
cd ~/real_estate_report && source venv/bin/activate && python3 << 'PYEOF'
import sqlite3

conn = sqlite3.connect('data/real_estate.db')
cur = conn.cursor()

# 1. 총 건수
cur.execute('SELECT COUNT(*) FROM fact_trade_raw')
total = cur.fetchone()[0]
print(f'=== 총 행수: {total:,} ===')

# 2. 유형별 건수
print('\n--- 유형별 건수 ---')
cur.execute('SELECT trade_type, COUNT(*) FROM fact_trade_raw GROUP BY trade_type ORDER BY COUNT(*) DESC')
for r in cur.fetchall(): print(f'  {r[0]:20s}: {r[1]:>10,}')

# 3. 수집 시군구 수
cur.execute('SELECT COUNT(DISTINCT sgg_cd) FROM fact_trade_raw')
print(f'\n--- 수집 시군구: {cur.fetchone()[0]}개 ---')

# 4. 연월 범위
cur.execute('SELECT MIN(yyyymm), MAX(yyyymm) FROM fact_trade_raw')
mn, mx = cur.fetchone()
print(f'--- 계약월 범위: {mn} ~ {mx} ---')

# 5. NULL/빈값 비율
print('\n--- NULL/빈값 점검 ---')
key_cols = ['deal_amount', 'exclu_use_ar', 'floor', 'sgg_cd', 'bldg_nm',
            'deal_year', 'deal_month', 'yyyymm', 'trade_type',
            'deposit', 'monthly_rent', 'land_ar', 'building_ar', 'total_floor_ar']
for col in key_cols:
    cur.execute(f'SELECT COUNT(*) FROM fact_trade_raw WHERE [{col}] IS NULL OR CAST([{col}] AS TEXT) = ""')
    n = cur.fetchone()[0]
    pct = n / total * 100 if total else 0
    flag = ' ⚠️' if pct > 30 else ''
    print(f'  {col:20s}: {n:>10,} ({pct:5.1f}%){flag}')

# 6. deal_amount <= 0
cur.execute('''
    SELECT trade_type, COUNT(*)
    FROM fact_trade_raw
    WHERE deal_amount IS NOT NULL AND CAST(deal_amount AS INTEGER) <= 0
    GROUP BY trade_type
''')
zeros = cur.fetchall()
if zeros:
    print('\n--- deal_amount <= 0 ---')
    for r in zeros: print(f'  {r[0]:20s}: {r[1]:>10,}')
else:
    print('\n--- deal_amount <= 0: 없음 ---')

# 7. 임대 유형 deposit/monthly_rent NULL
print('\n--- 임대 유형 deposit/monthly_rent NULL ---')
cur.execute('''
    SELECT trade_type,
           COUNT(*) as total,
           SUM(CASE WHEN deposit IS NULL OR CAST(deposit AS TEXT) = '' THEN 1 ELSE 0 END) as dep_null,
           SUM(CASE WHEN monthly_rent IS NULL OR CAST(monthly_rent AS TEXT) = '' THEN 1 ELSE 0 END) as rent_null
    FROM fact_trade_raw
    WHERE trade_type LIKE '%RENT%'
    GROUP BY trade_type
''')
for r in cur.fetchall():
    dep_pct = r[2] / r[1] * 100 if r[1] else 0
    rent_pct = r[3] / r[1] * 100 if r[1] else 0
    print(f'  {r[0]:20s}: 총 {r[1]:>10,} | deposit NULL {r[2]:>8,} ({dep_pct:.1f}%) | rent NULL {r[3]:>8,} ({rent_pct:.1f}%)')

# 8. 중복 의심
print('\n--- 중복 의심 (dedup 키 기준) ---')
cur.execute('''
    SELECT COUNT(*) FROM (
        SELECT 1 FROM fact_trade_raw
        GROUP BY trade_type, sgg_cd, yyyymm,
                 COALESCE(bldg_nm,''), COALESCE(exclu_use_ar,''),
                 COALESCE(floor,''), COALESCE(deal_amount,''),
                 COALESCE(deposit,''), COALESCE(monthly_rent,''),
                 COALESCE(deal_year,''), COALESCE(deal_month,''),
                 COALESCE(contract_term,'')
        HAVING COUNT(*) > 1
        LIMIT 200
    )
''')
dup_cnt = cur.fetchone()[0]
print(f'  중복 키 조합 수: {dup_cnt}건')
if dup_cnt > 0:
    cur.execute('''
        SELECT trade_type, sgg_cd, yyyymm, bldg_nm, COUNT(*) as cnt
        FROM fact_trade_raw
        GROUP BY trade_type, sgg_cd, yyyymm,
                 COALESCE(bldg_nm,''), COALESCE(exclu_use_ar,''),
                 COALESCE(floor,''), COALESCE(deal_amount,''),
                 COALESCE(deposit,''), COALESCE(monthly_rent,''),
                 COALESCE(deal_year,''), COALESCE(deal_month,''),
                 COALESCE(contract_term,'')
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 5
    ''')
    for r in cur.fetchall():
        print(f'    {r[0]} | {r[1]} | {r[2]} | {r[3]} | x{r[4]}')

# 9. 시군구별 건수
print('\n--- 시군구별 건수 (상위 10) ---')
cur.execute('SELECT sgg_cd, COUNT(*) FROM fact_trade_raw GROUP BY sgg_cd ORDER BY COUNT(*) DESC LIMIT 10')
for r in cur.fetchall(): print(f'  {r[0]}: {r[1]:>10,}')

print('\n--- 시군구별 건수 (하위 10) ---')
cur.execute('SELECT sgg_cd, COUNT(*) FROM fact_trade_raw GROUP BY sgg_cd ORDER BY COUNT(*) ASC LIMIT 10')
for r in cur.fetchall(): print(f'  {r[0]}: {r[1]:>10,}')

# 10. 최근 적재
cur.execute('SELECT MAX(created_at) FROM fact_trade_raw')
print(f'\n--- 최근 적재: {cur.fetchone()[0]} ---')

# 11. ETL 로그
cur.execute('SELECT COUNT(*) FROM etl_trade_raw_log')
log_total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM etl_trade_raw_log WHERE status='SUCCESS'")
log_ok = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM etl_trade_raw_log WHERE status='FAIL'")
log_fail = cur.fetchone()[0]
print(f'\n--- ETL 로그: 총 {log_total:,} | SUCCESS {log_ok:,} | FAIL {log_fail:,} ---')

# 12. fact_indicator_month
print('\n--- fact_indicator_month ---')
cur.execute('SELECT COUNT(*) FROM fact_indicator_month')
print(f'  총 행수: {cur.fetchone()[0]}')
cur.execute('SELECT indicator_code, COUNT(*) FROM fact_indicator_month GROUP BY indicator_code ORDER BY COUNT(*) DESC')
for r in cur.fetchall(): print(f'  {r[0]:35s}: {r[1]:>5,}')

conn.close()
print('\n=== 데이터 품질 점검 완료 ===')
PYEOF
```


---

## 부록 B: STAT_MOLIT 착공실적 API 테스트 결과

- **엔드포인트**: `https://stat.molit.go.kr/portal/openapi/service/rest/getList.do`
- **파라미터**: `key={MOLIT_STAT_API_KEY}&form_id=5386&style_num=1&start_dt=202501&end_dt=202501`
- **결과**: 360건 정상 반환
- **응답 구조**: `{'date': '202501', '부문명': '총계', '착공실적': 10178, '시도별': '전국', '구  분': '총계'}`
- **지역 수준**: 시도 18개 (전국 포함) — **시군구 불가**
- **결론**: 시군구 단위 불가로 SUPPLY_STARTS 지표는 보류. 대신 SUPPLY_INCOMING(odcloud) 채택.


---

## 부록 C: 이관 정책

| 항목 | 정책 |
|---|---|
| fact_trade_raw 12종 | Landbrief로 이관, 월별 수집 파이프라인 구축 |
| fact_indicator_month | Landbrief 12종에 해당하는 것만 이관 |
| KB 지표 | 완전 삭제 |
| 수집 실적 없는 API 전용 항목 | 폐기 |
| dim_region | 이관 (269행) |
| LandScanner 서비스 | prefetch 완료 + 검증 후 종료 |
| LandScanner DB 파일 | 콜드 보관 (Synology 백업) |


---

*끝. 다음 버전은 데이터 품질 점검 결과 반영 후 HANDOVER_v002로 업데이트.*
```

---

이 파일을 서버에 저장하려면:

```bash
mkdir -p ~/landbrief/docs/handover
cat > ~/landbrief/docs/handover/HANDOVER_v001_20260225.md << 'EOF'
(위 내용 전체 붙여넣기)
EOF
```

새 채팅을 시작할 때는 이 파일 내용을 첫 메시지에 붙여넣으면 컨텍스트가 완전히 복원됩니다. 품질 점검 결과가 나오면 v002로 업데이트하겠습니다.