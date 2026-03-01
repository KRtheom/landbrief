# Landbrief Handover v007 (2026-03-01)

**⚠ 수정 규칙**: 수정사항 안내 시 반드시 **섹션 단위**로 전체 교체 블록을 마크다운 원문으로 제공할 것. 줄 단위 지시, 화살표(→) 표기, diff 형식 금지.

## 문서 체계
- INTENT_v3.0.md: 제품 정의/원칙/범위/Phase 구분/지표/시트 구성.
- ENGINE.md (미작성): 정렬 엔진 세부 명세.
- HANDOVER: 현재 상태. 매 세션 공유.
- AGENTS.md (v1.1): Codex 작업 운영 규칙.
- DDL.md (v0.3 미작성, v0.2.1 현행): 데이터베이스 스키마 정의.
- MIGRATION_COLUMN_MAP.md: LandScanner → Landbrief 이관 매핑 (58개 컬럼, dedup 키 정의).
- ERROR_CODE_HANDLING.md (v1.2): 6개 소스 에러코드 통합 처리 규정.
- API 기술문서: API_SPEC_trade.md (실거래 13종), API_SPEC.md (ECOS·REB·청약홈·건축HUB·미분양).

## 프로젝트 요약
공공 부동산 데이터를 동일 기간·동일 단위로 정렬·정제하여 실무자가 즉시 엑셀로 추출할 수 있는 부동산 데이터 추출 도구.
- Phase 1: 회사 파일럿 CLI 엑셀 (시군구 + 단지, 월별 36개월 / 연별 10년)
- Phase 2: 웹 기반 추출 SaaS (지도 연계)
- Phase 3: 리포트 자동화 (기업 요청 기반)
- KB 데이터 사용 안 함 (약관상 상업적 이용 불가)
- 상세 → INTENT.md v3.1

## 서버
Ubuntu 24.04, i7-10700, 32GB, ssh -p 2222 deploy@122.45.64.200
개인 PC, 파일럿 후 VPS 전환 예정. 디스크 419GB 여유, 메모리 14GB 가용.
1TB SSD 추가 장착 예정 (PostgreSQL 데이터 디렉토리용).

## 경로
- LandScanner: ~/real_estate_report (서버)
- Landbrief: 로컬 개발 (d:/landbrief), 서버 배포 경로 ~/landbrief (미생성)
- LandScanner DB: ~/real_estate_report/data/real_estate.db (서버, SQLite, ~6GB 추정)
- Landbrief DB: PostgreSQL (로컬 설치 완료, 서버 미설치)

## Git
- LandScanner: github.com/KRtheom/real-estate-report.git (private)
- Landbrief: github.com/KRtheom/landbrief (private)

## 확정 지표

### 수집 지표 13종
| # | 코드 | 소스 | 상태 |
|---|---|---|---|
| 1 | APT_SALE_DTL | MOLIT | 수집 완료 |
| 2 | APT_RENT | MOLIT | 수집 완료 |
| 3 | REB_SALE_PRICE_INDEX | R-ONE | 수집 완료 (207지역 × 124개월) |
| 4 | REB_RENT_PRICE_INDEX | R-ONE | 수집 완료 (207지역 × 124개월) |
| 5 | REB_TRADE_VOLUME | R-ONE | 수집 완료 (207지역 × 124개월) |
| 6 | UNSOLD_UNITS_SIGUNGU | STAT_MOLIT | 테스트 완료 (강남구, 500 에러 해결) |
| 7 | UNSOLD_UNITS_COMPLETED | STAT_MOLIT | 테스트 완료 (강남구, 500 에러 해결) |
| 8 | MACRO_BASE_RATE | ECOS | 수집 완료 (121개월) |
| 9 | DEMO_POPULATION | MOIS | 부분 완료 (2022-09~, CSV 보완 필요) |
| 10 | DEMO_HOUSEHOLD | MOIS | 부분 완료 (2022-09~, CSV 보완 필요) |
| 11 | SUPPLY_INCOMING | APPLYHOME | 미착수 |
| 12 | HOUSING_PRICE_OUTLOOK_CSI | ECOS | 수집 완료 (13지역 × 122개월) |
| 13 | HUG_AVG_PRICE_PER_SQM | HUG | 미착수 (KOSIS CSV 다운로드 예정) |

### 파생 지표 1종
SUPPLY_PRICE_PER_SQM – 청약홈 APT 주택형별 분양정보에서 산출. 세대수 최다 주택형 기준 최고분양가 ÷ 주택공급면적.

### 참고 지표 3종 (수집 완료, 엑셀 시트4 참고자료)
CPI (MACRO_CPI), CSI (MACRO_CSI), ESI (SENTIMENT_ESI)

### 드랍
- HF_PIR (세션 11)
- KB 지표 전종 (세션 14, 약관상 상업적 이용 불가)

## 단지코드
- apt_seq 기반 dim_complex 자체 구축 (KB 단지코드 의존 없음)
- 검증 완료: bldg_nm 1:1 매칭, 매매/임대 동일 코드 체계 (37,289개 공유, 90.6%)
- dim_complex: lat/lng nullable 선설계 (Phase 2 반경 검색용)
- 건축물대장 API로 좌표·세대수·공급면적 보강 예정

## 데이터 확보 전략
- 월별 데이터 (최근 36개월): API 자동 수집
- 연별 데이터 (10년): CSV 다운로드 → PostgreSQL 적재
- 시트1 연별 분양 평단가: HUG #15061057 (KOSIS CSV)
- 시트2 월별 분양 평단가: 청약홈 건별 데이터에서 산출 (#15101047 CSV + #15098547 API)
- LandScanner에서 전 지표 수집·검증 완료 후 Landbrief 본격 착수.
- Landbrief는 LandScanner에서 1회 이관 후 독립 파이프라인으로 운영.
- 서버 1대 환경: SQLite(LandScanner, 기존 SSD) + PostgreSQL(Landbrief, 신규 1TB SSD) 디스크 분리.

## 수집 현황 (2026-03-01 20:18 KST 기준)

| 데이터 | 상태 | 비고 |
|---|---|---|
| 실거래 12종 (2020~) | 완료 (각 19,832건 OK) | PRESALE 포함 (322,997건, apt_seq 없음) |
| 실거래 2종 백필 (2016~2019) | 진행 중 (~25%) | APT_SALE_DTL + APT_RENT nohup, 3/4~5 완료 예상. ERROR 1건(44130 201601 502) |
| LAND_SALE | 진행 중 (OK 2,995 / PENDING 556) | cron 매일 00:05 KST |
| REB 매매/전세가격지수 | 완료 (207지역 × 124개월) | 전국(00000) + 시도(17) + 시군구(189), 201510~202601 |
| REB 거래량 | 완료 (207지역 × 124개월) | 201509~202601, 202203 복구 완료 |
| ECOS 경제지표 (4종) | 완료 (121~122개월) | BASE_RATE·CPI 201601~202601, CSI·ESI 201601~202602. ECOS_FIXED_YEARS=10 적용 |
| HOUSING_PRICE_OUTLOOK_CSI | 완료 (13지역 × 122개월) | 511Y004 FMFB, 전국+ECOS 권역 12개, 201601~202602 |
| MOIS 인구/세대 (2022-09~) | 완료 (20,996건, 299지역) | |
| MOIS 인구/세대 (2016~2022-08) | ❌ 미착수 | CSV 다운로드 필요 |
| UNSOLD 미분양 | 테스트 완료 (강남구) | 500 에러 해결 (end_dt 캡, 청크 분할). 전국 수집 미실행 |
| 청약홈 분양정보 | CSV 구조 확인 완료 | #15101047(주택형별) + #15101046(메타). API #15098547 자동화 가능 확인 |
| HUG 분양가격 동향 | ❌ 미착수 | KOSIS CSV 다운로드 예정. 공공데이터포털 #15061057 CSV 미갱신(2024-07) |
| 연별 10년 CSV | ❌ 미착수 | |

- fact_trade_raw: 18,452,773건 (백필 진행 중, PRESALE 322,997건 포함)
- fact_indicator_month: ~103,600건, 20 indicators (HOUSING_PRICE_OUTLOOK_CSI 추가)
- 공공데이터포털 한도: 3/5 이전 10,000건/일, 3/5 이후 1,000건/일. API 서비스별 독립 한도.

### 실행 중 프로세스
- prefetch_trade_raw.py – nohup, 로그: logs/prefetch_backfill.log

### 크론 주의
- 00:05 LAND_SALE prefetch, 03:00 load_all.py – SQLite WAL 충돌 가능. 백필 완료 전 수동 실행 시 주간 시간대 권장.

## 데이터 검증 현황 (세션 14 완료)
- fact_trade_raw 검증: PASS 8 / WARN 3(정상) / FAIL 2(N/A)
- 인코딩·포맷 전항목 PASS, 한글깨짐 0건, 쉼표 0건
- 컬럼 매핑 58개 확정 (MIGRATION_COLUMN_MAP.md)
- dedup 키 검증: 14,152,214건 전수 스캔, 중복 0건
- 2020 이전 851건: 이관 시 deal_year >= 2016 필터 (백필 적용)

## DDL
- v0.3 확정 (2026-03-01)
- v0.2.1 대비 변경: source_enum에 HUG 추가, fact_supply_raw 테이블 추가
- calendar_month는 ENGINE.md 설계 후 v0.4에서 추가
- 파일: ~/landbrief/docs/DDL.md (로컬)

## 이관 정책
- fact_trade_raw: 실거래 12종 이관 (LAND_SALE 제외, PRESALE 포함)
- 이관 필터: deal_year >= 2016 (백필 완료 후 적용)
- PRESALE: 322,997건, apt_seq 전건 빈값 (단지 매칭 불가)
- dim_region: 이관 (컬럼명 매핑 필요)
- MOIS 인구/세대: 이관
- ECOS 경제지표: 이관 (region_key='00000' 유지)
- HOUSING_PRICE_OUTLOOK_CSI: 이관 (ECOS 권역코드 → 시도코드 매핑 필요)
- fact_indicator_month: 이관 안 함
- HOUSTAT 40건 (HF 지표): 이관 안 함 (드랍 확정 지표, enum만 유지)

## 미결/블로커
- ENGINE.md 미작성 (P1) — 정렬 엔진 핵심 IP
- 건축물대장 API 공급면적 확보 가능 여부 미검증 (P2) — 공급평단가 산출 필수
- 연별 10년 CSV 다운로드 미착수 (P2)
- MOIS 인구/세대 2016~2022-08 CSV 미착수 (P2)
- serviceKey 로그 평문 노출 (P1)
- serviceKey 인코딩 이슈 (P2) — curl 시 -A "Mozilla/5.0" 필수
- dim_region 자동적재 미구현 (P2)
- API 한도 축소 3/5 적용 (10,000 → 1,000건/일)
- 비아파트 dedup 키 과소정의 (Phase 2 전 분석)
- 신고 지연 데이터 재수집 전략 (P3)
- 강원/전북 행정코드 변경 매핑 (P2)
- HTTP 401 연속 N회 조기 중단 미구현 (P3)
- LandScanner DB 확정 외 지표 잔존 (P3) — 20 indicators 중 이관 대상 외 지표 정리 필요
- 공공데이터포털 #15061057 HUG CSV 미갱신 (P3) — 2024-07 이후 업데이트 중단. KOSIS 대체
- 청약홈 공급지역코드 → sgg_cd 매핑 미구현 (P2)

## LandScanner cron (현행 유지, Landbrief ETL 가동 전까지)
- 0 3 * * * load_all.py --region 11680 --months 12
- 0 0 * * * daily_check.sh (수집 진행률 모니터링)
- 5 0 * * * prefetch LAND_SALE --max-calls 990

## 다음 세션 작업 (우선순위 순)

### 최우선 (LandScanner 수집·검증)
1. 백필 완료 확인 + ERROR 1건 재시도 (44130 201601)
2. UNSOLD 전국 수집 (--region all --include-unsold)
3. ENGINE.md 설계 착수 (캘린더 테이블, 지표별 월/연 집계 규칙, 결측 처리, 입출력 구조)

### 중순위 (LandScanner 수집·검증)
4. 청약홈 CSV 적재 (fact_supply_raw, #15101046 + #15101047 조인)
5. HUG 분양가격 동향 KOSIS CSV 다운로드
6. MOIS 인구/세대 2016~2022-08 CSV 다운로드
7. 연별 10년 CSV 다운로드 계획 수립
8. 건축물대장 API 공급면적 확보 가능 여부 검증

### 후순위 (Landbrief 착수 — 전 지표 수집·검증 완료 후)
9. 로컬 PostgreSQL DDL v0.3 적용 + 샘플 데이터 적재 테스트
10. DDL v0.4 확정 (calendar_month 추가, ENGINE.md 의존)
11. 서버 1TB SSD 장착 + PostgreSQL 설치 + 전량 이관
12. ECOS API 기술문서에 주택가격전망CSI 통계표코드 추가

## 코드 컨벤션
- DB 접속: 단일 connect() 강제
- 타임스탬프: DB=UTC, 출력=KST
- 타입: fact_trade_raw VARCHAR 유지, Mart에서 CAST
- dedup COALESCE: NULL → '' (빈문자열) 통일, 숫자 0 치환 안 함
- 정본 = 코드. 문서 불일치 시 문서 수정.
- prefetch 실행: --region 기본값 seoul, 전국 수집 시 반드시 --region all 지정
- curl MOLIT API 테스트: 반드시 -A "Mozilla/5.0" 포함
- Codex 운영 규칙: AGENTS.md에 통합 정의. 매 세션 말미 AGENTS.md 업데이트 필요 여부 점검.

---
**블록 2: CHANGELOG**

#018 – 2026-03-01 (Session 18)

**수집 상태 전수 점검**
- 백필 진행 중: 66,464잡 중 ~16,979번째 (~25%). 3/4~5 완료 예상.
- 백필 적재 정상: APT_RENT 2,388,621건 + APT_SALE_DTL 1,869,582건 (201512~201912).
- ERROR 1건: APT_SALE_DTL 44130(천안시) 201601 HTTP 502. 완료 후 단건 재시도.
- fact_trade_raw 총 18,452,773건.
- LAND_SALE cron 정상: OK 2,995 / PENDING 556.
- fact_indicator_month 20 indicators 확인. UNSOLD_UNITS_EXTRA 12건 레거시 잔존.

**INTENT v3.0 검토 완료**
- 세션 16 미반영 4건(섹션 3.6, 5.2, 시트1 표, 용어사전) 전부 반영 확인.
- 수집 지표 체계 확정: 13종(수집) + 1종(파생) + 3종(참고).

**ECOS 주택가격전망CSI 수집 완료 (Codex #C-018-1)**
- 통계표코드: 511Y004, ITEM_CODE: FMFB.
- 적재: 1,463건, 13개 지역(전국 + ECOS 권역 12개), 201601~202602.
- ECOS 권역은 시도 17개가 아닌 자체 그룹(대구경북, 광주전남 등). ENGINE.md에서 매핑 규칙 처리.

**청약홈 API 자동화 가능 확정 (Codex #C-018-2)**
- #15098547 API에 getAPTLttotPblancMdl 오퍼레이션 확인.
- 핵심 필드: SUPLY_AR, LTTOT_TOP_AMOUNT, SUPLY_HSHLDCO 모두 제공.
- 수집 전략: CSV 백필(#15101047) + API 증분(#15098547).

**UNSOLD 500 에러 해결 (Codex #C-018-3 + #C-018-4)**
- 원인: 요청 구간 과대/미래월 포함 시 간헐적 500.
- 수정: end_dt 전월 캡, 6개월 청크 분할, 3회 재시도, 500 로깅 강화.
- form_id 정합화: UNSOLD_UNITS_SIGUNGU=2082, UNSOLD_UNITS_COMPLETED=5328. 2080 주석 처리.
- --include-unsold 플래그 추가.
- 강남구 테스트 정상: SIGUNGU 11건 + COMPLETED 364건, ERROR 0.

**청약홈 CSV 구조 확인 + fact_supply_raw 설계**
- #15101047 (주택형별): 15개 컬럼, dedup 키 = house_manage_no + pblanc_no + model_no.
- #15101046 (메타): 46개 컬럼, 조인키 = house_manage_no + pblanc_no.
- 공급금액 단위: 만원 확정.
- fact_supply_raw 테이블 설계 확정: 17개 비즈니스 컬럼 + 메타 3개.

**HUG 분양가격 동향 데이터 확보 전략 확정**
- #15128701은 HUG가 아닌 한국부동산원(REB) 청약홈 데이터. 혼동 해소.
- HUG 실제 데이터: #15061057 (공공데이터포털 CSV, 미갱신 2024-07).
- HUG 자체 공표는 매월 정상 (2026-01 기준 발표 확인).
- 확정: 시트1 연별 = HUG KOSIS CSV, 시트2 월별 = 청약홈 건별 산출.

**DDL v0.3 확정**
- source_enum에 HUG 추가.
- fact_supply_raw 테이블 + 인덱스 2개 + updated_at 트리거 추가.
- calendar_month는 ENGINE.md 설계 후 v0.4에서 추가.

**HANDOVER 업데이트**
- 수집 지표 12종 → 13종 (HUG_AVG_PRICE_PER_SQM 추가).
- 파생 지표 1종 유지 (SUPPLY_PRICE_PER_SQM).
- 참고 지표 3종 유지 (CPI, CSI, ESI).
- INTENT 파일명: INTENT_v3.0.md (기존 파일 내 수정, 버전업 아님).
- DDL 버전: v0.2.1 → v0.3.
- 미결 목록 업데이트: INTENT 수정 4건 해결, UNSOLD 500 에러 해결. 신규 3건 추가.
- "Codex 태스크 #C-016-1 (REB 백필)" 제거 (#C-017-1에서 해결).
