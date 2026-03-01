
---

# INTENT.md v2.1

## 1. 제품 정의

Landbrief는 공공 부동산 데이터를 동일 기간·동일 단위로 정렬·정제하여, 실무자가 즉시 엑셀로 추출해 회사 제출 자료로 활용할 수 있도록 지원하는 부동산 데이터 추출 도구다.

판단 없음. 점수 없음. 예측 없음. 비교 기능 없음. 자체 산출 비율 없음. 정렬 + 정제 + 엑셀 출력에 집중한다. 원천 데이터를 정렬해서 제공하고, 계산은 사용자 몫이다.

## 2. 데이터 원칙

### 2.1 데이터 범위

모든 데이터는 공공데이터 기반으로 구성한다. KB 및 민간 데이터는 사용하지 않는다(KB부동산 이용약관 제12조④ 영리목적 이용 금지, 제14조①-5 크롤링 금지).

### 2.2 데이터 소스

국토교통부 실거래가(DATA_GO_KR), 한국부동산원(REB), 한국은행(ECOS), 행정안전부(MOIS), 국토교통부 통계(MOLIT_STAT), 청약홈(APPLYHOME), 건축물대장(건축HUB, 보강용).

### 2.3 면적 기준

공급평단가 산출 : 거래금액 ÷ 공급면적 × 3.3058(평 환산). 공급면적은 건축물대장 API에서 확보한다(확보 전까지 전용면적 기준으로 제공하며 "전용면적 기준" 명시). 모든 엑셀에 면적 기준을 명기한다.

### 2.4 단지코드

국토부 apt_seq 기반으로 자체 구축한다. KB 단지코드 의존 없음. apt_seq는 매매/임대 간 동일 코드 체계임을 검증 완료(37,289개 단지 공유, 90.6% 일치).

### 2.5 데이터 확보 전략

월별 데이터(최근 36개월): API 자동 수집. 기존 ETL 파이프라인 활용.

연별 데이터(10년): CSV 수동 다운로드 → PostgreSQL 적재. 실거래가 공개시스템, 통계누리, 행안부 등에서 시군구별 연 단위 집계값을 확보한다. API 추가 수집은 하지 않는다.

## 3. Phase 구조

### 우선과제: 공공데이터 확보 (99% 완료)

실거래 11종 수집 완료. LAND_SALE 수집 진행 중(cron). MOIS 인구/세대 완료. ECOS 경제지표 완료. 미수집: UNSOLD(미분양), 청약홈(분양정보), 주택가격전망CSI(ECOS 추가 수집), 연별 10년 CSV.

### Phase 1: 회사 파일럿 — CLI 엑셀 출력

목표: 개발지역 인근 정보를 회사 제출용 엑셀로 자동 생성한다.

입력: 시군구 1개 이상 지정, 단지 apt_seq 직접 지정, 기간 옵션(월별 36개월 또는 연별 10년).

```
python generate_excel.py --sgg 11680 --complex 11680-123 11680-456 --months 36
python generate_excel.py --sgg 11680 --complex 11680-123 11680-456 --years 10
```

산출물: 엑셀 파일 (7시트).

시트 1. 개요 및 참고자료 — 산식, 면적 기준, 데이터 출처, 집계 방식. 참고 지표: 기준금리 추이, CSI, 주택가격전망CSI, CPI (동일 기간).

시트 2. 매매 — 실거래 중앙값, 거래건수, REB 매매가격지수.

시트 3. 임대 — 전세/월세 중앙값, 거래건수, REB 전세가격지수.

시트 4. 공급 — 미분양, 입주예정물량, 인근 분양가 이력.

시트 5. 인구 — 인구수, 세대수.

시트 6. 단지 매매 — 공급평단가, 중앙값, 거래건수.

시트 7. 단지 임대 — 전세/월세 중앙값, 거래건수.

자체 산출 비율(전세가율, 거래회전율 등)은 제공하지 않는다. 원천 데이터를 정렬하여 제공하고, 계산은 사용자가 한다.

### Phase 2: 웹 기반 추출 SaaS

FastAPI + Jinja2 웹 인터페이스. Kakao Map 기반 시군구 선택. 단지 검색 기능. 좌표 기반 반경 자동 검색. 사용자 인증 및 과금 구조.

### Phase 3: 리포트 자동화 (기업 요청 기반)

PF 심사, 투자심의, 중개사 대응 리포트 자동 생성. Phase 1~2의 정렬 엔진과 엑셀 엔진을 기반으로 확장한다. 기업 수요 확인 후 착수.

## 4. 확정 지표

### 수집 지표 (12종)

APT_SALE_DTL(아파트 매매 상세), APT_RENT(아파트 전월세), REB_SALE_PRICE_INDEX(매매가격지수), REB_TRADE_VOLUME(거래량), REB_RENT_PRICE_INDEX(전세가격지수), UNSOLD_UNITS_SIGUNGU(미분양), UNSOLD_UNITS_COMPLETED(공사완료후 미분양), MACRO_BASE_RATE(기준금리), DEMO_POPULATION(인구), DEMO_HOUSEHOLD(세대수), SUPPLY_INCOMING(입주예정물량), HOUSING_PRICE_OUTLOOK_CSI(주택가격전망CSI).

참고 지표로 CPI(소비자물가지수), CSI(소비자심리지수), ESI(경제심리지수)를 수집한다. 이들은 이미 수집 완료되어 있다.

데이터 수집은 전종 수행한다. 엑셀 출력 범위는 시트 구성에 따른다.

## 5. 핵심 구성요소

### 5.1 데이터 레이어

fact_trade_raw, fact_indicator_month, dim_region, dim_complex. PostgreSQL 기반, raw SQL + view 중심 설계.

### 5.2 단지 마스터 (dim_complex)

PK: apt_seq. 컬럼: apt_seq, bldg_nm, sgg_cd, umd_nm, lat(nullable), lng(nullable), households(nullable), built_year(nullable). 1차 생성은 fact_trade_raw에서 추출. 2차 보강은 건축물대장 API에서 좌표·세대수 등 추가(Phase 2 반경 검색 전 완료).

### 5.3 정렬 엔진 (핵심 IP)

동일 기간 강제 정렬, 월 기준 캘린더 테이블 기반 집계, 중앙값 계산, 표본수 계산, 반기 지표 직전값 캐리, 기준금리 월말 유효값 적용, 결측 처리 정책 일관 적용. 월별/연별 두 가지 집계 모드를 지원한다. 세부 명세는 ENGINE.md에서 정의한다.

### 5.4 엑셀 생성 엔진

Phase 1 산출물인 7시트 엑셀 파일을 생성한다. 모든 시트에 단위, 기준, 집계 방식을 명시한다.

## 6. 기술 스택

Backend: Python 3.12, FastAPI, PostgreSQL 16, raw SQL + view 중심.

Excel: openpyxl (필요 시 pandas.ExcelWriter 병행).

Frontend (Phase 2): FastAPI + Jinja2 템플릿 + vanilla JS + Kakao Map API.

## 7. 문서 체계

INTENT.md(본 문서): 제품 정의, 원칙, 범위, Phase 구분.

ENGINE.md: 정렬 엔진 세부 명세. 캘린더 테이블, 캐리 규칙, 결측 처리, 중앙값 산출 방식, 월별/연별 집계 규칙.

DDL.md: 데이터베이스 스키마 정의.

MIGRATION_COLUMN_MAP.md: LandScanner → Landbrief 이관 매핑.

ERROR_CODE_HANDLING.md: API 에러코드 통합 처리 규정.

HANDOVER.md: 현재 작업 상태. 매 세션 공유.

AGENTS.md: Codex 작업 운영 규칙.

API 기술문서: MOLIT_TRADE_API_SPEC.md(실거래 13종), ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md(ECOS·REB·청약홈·건축HUB), MOLIT_STAT_API_SPEC.md(미분양 2종).

## 8. 범위 제한

Phase 1~2에서 하지 않는 것: 단지 상세 포털화, 대출 계산기, 매물 연동, 중개사 연결, AI 예측, 점수화, KB 데이터 사용, 자체 산출 비율 제공, A/B/C 비교 기능.