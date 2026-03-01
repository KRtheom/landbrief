
---

# Landbrief Handover v006 (2026-03-01)

**블록 1: HANDOVER(기반 문서)**

> **⚠ 수정 규칙**: 수정사항 안내 시 반드시 **섹션 단위**로 전체 교체 블록을 마크다운 원문으로 제공할 것. 줄 단위 지시, 화살표(→) 표기, diff 형식 금지.

## 문서 체계
- INTENT.md (v2.1): 제품 정의/원칙/범위/Phase 구분/지표/시트 구성.
- ENGINE.md (미작성): 정렬 엔진 세부 명세.
- HANDOVER: 현재 상태. 매 세션 공유.
- AGENTS.md (v1.0): Codex 작업 운영 규칙.
- DDL.md (v0.2): 데이터베이스 스키마 정의.
- MIGRATION_COLUMN_MAP.md: LandScanner → Landbrief 이관 매핑 (58개 컬럼, dedup 키 정의).
- ERROR_CODE_HANDLING.md (v1.2): 6개 소스 에러코드 통합 처리 규정.
- API 기술문서: MOLIT_TRADE_API_SPEC.md (실거래 13종), ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md (ECOS·REB·청약홈·건축HUB), MOLIT_STAT_API_SPEC.md (미분양 2종).

## 프로젝트 요약
공공 부동산 데이터를 동일 기간·동일 단위로 정렬·정제하여 실무자가 즉시 엑셀로 추출할 수 있는 부동산 데이터 추출 도구.
- Phase 1: 회사 파일럿 CLI 엑셀 (시군구 + 단지, 월별 36개월 / 연별 10년)
- Phase 2: 웹 기반 추출 SaaS (지도 연계)
- Phase 3: 리포트 자동화 (기업 요청 기반)
- KB 데이터 사용 안 함 (약관상 상업적 이용 불가)
- 상세 → INTENT.md v2.1

## 서버
Ubuntu 24.04, i7-10700, 32GB, ssh -p 2222 deploy@122.45.64.200
개인 PC, 파일럿 후 VPS 전환 예정. 디스크 419GB 여유, 메모리 14GB 가용.
1TB SSD 추가 장착 예정 (PostgreSQL 데이터 디렉토리용).

## 경로
- LandScanner: ~/real_estate_report (서버)
- Landbrief: 로컬 개발 (d:/landbrief), 서버 배포 경로 ~/landbrief (미생성)
- LandScanner DB: ~/real_estate_report/data/real_estate.db (서버, SQLite, 5.1GB)
- Landbrief DB: PostgreSQL (로컬 설치 진행 중, 서버 미설치)

## Git
- LandScanner: github.com/KRtheom/real-estate-report.git (private)
- Landbrief: github.com/KRtheom/landbrief (private)

## 확정 지표

### 수집 지표 12종
APT_SALE_DTL, APT_RENT, REB_SALE_PRICE_INDEX, REB_TRADE_VOLUME, REB_RENT_PRICE_INDEX, UNSOLD_UNITS_SIGUNGU, UNSOLD_UNITS_COMPLETED, MACRO_BASE_RATE, DEMO_POPULATION, DEMO_HOUSEHOLD, SUPPLY_INCOMING, HOUSING_PRICE_OUTLOOK_CSI

### 파생 지표 1종
SUPPLY_PRICE_PER_SQM – 청약홈 APT 주택형별 분양정보에서 산출. 세대수 최다 주택형 기준 최고분양가 ÷ 주택공급면적. 84㎡ 고정 아님.

### 참고 지표 3종 (수집 완료, 엑셀 시트4 참고자료)
CPI, CSI, ESI

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
- LandScanner를 전 지표 수집·검증용 테스트베드로 유지. Landbrief는 LandScanner에서 1회 이관 후 독립 파이프라인으로 운영.
- 서버 1대 환경: SQLite(LandScanner, 기존 SSD) + PostgreSQL(Landbrief, 신규 1TB SSD) 디스크 분리.

## 수집 현황 (2026-03-01 기준)

| 데이터 | 상태 | 비고 |
|---|---|---|
| 실거래 12종 (2020~) | 완료 (각 19,832건 OK) | PRESALE 포함 (322,997건, apt_seq 없음) |
| 실거래 2종 백필 (2016~2019) | 진행 중 | APT_SALE_DTL + APT_RENT, prefetch_trade_raw.py nohup 실행, 3/2 완료 예상 |
| LAND_SALE | 진행 중 (OK 2,995 / PENDING 556) | cron 매일 00:05 KST |
| REB 매매/전세가격지수 | 완료 (207지역 × 124개월) | 전국(00000) + 시도(17) + 시군구(189), 201510~202601 |
| REB 거래량 | 완료 (207지역 × 124개월) | 201509~202601, 202203 복구 완료 |
| ECOS 경제지표 (4종) | 완료 (121~122개월) | BASE_RATE·CPI 201601~202601, CSI·ESI 201601~202602. ECOS_FIXED_YEARS=10 적용 |
| MOIS 인구/세대 (2022-09~) | 완료 (20,996건, 299지역) | |
| MOIS 인구/세대 (2016~2022-08) | ❌ 미착수 | CSV 다운로드 필요 |
| UNSOLD 미분양 | 테스트 수준 (11건) | MOLIT_STAT API 500 에러 확인 필요 |
| 청약홈 분양정보 | ❌ 미착수 | 서비스키 신청 완료. CSV 13,210건 무료 다운로드 가능 |
| 주택가격전망CSI | ❌ 미착수 | ECOS 통계표코드 미확인 |
| 연별 10년 CSV | ❌ 미착수 | |

- fact_trade_raw: 14,195,351건 (PRESALE 322,997건 포함)
- fact_indicator_month: 102,149건, 19 indicators (확정 외 지표 포함, 이관 시 필터링 필요)
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
- 2020 이전 851건: 이관 시 deal_year >= 2020 필터

## DDL
- v0.2.1 확정 (2026-03-01)
- 변경: source_enum 수정(KB 제거, APPLYHOME·ARCH_HUB 추가, HOUSTAT 유지), dim_complex 추가, idx_ftr_aptseq 추가, 주석 3건
- calendar_month는 ENGINE.md 설계 후 v0.3에서 추가
- 파일: ~/landbrief/docs/DDL.md (로컬)

## 이관 정책
- fact_trade_raw: 실거래 12종 이관 (LAND_SALE 제외, PRESALE 포함)
- 이관 필터: deal_year >= 2016 (기존 >= 2020에서 변경, 백필 완료 후 적용)
- PRESALE: 322,997건, apt_seq 전건 빈값 (단지 매칭 불가)
- dim_region: 이관 (컬럼명 매핑 필요)
- MOIS 인구/세대: 이관
- ECOS 경제지표: 이관 (region_key='00000' 유지)
- fact_indicator_month: 이관 안 함
- HOUSTAT 40건 (HF 지표): 이관 안 함 (드랍 확정 지표, enum만 유지)

## 미결/블로커
- ENGINE.md 미작성 (P1) — 정렬 엔진 핵심 IP
- INTENT.md v3.0 수정 4건 미반영 (P1) — 섹션 3.6, 5.2, 시트1 표, 용어사전
- 건축물대장 API 공급면적 확보 가능 여부 미검증 (P2) — 공급평단가 산출 필수
- 연별 10년 CSV 다운로드 미착수 (P2)
- 주택가격전망CSI ECOS 통계표코드 미확인 (P3)
- MOLIT_STAT API 500 에러 (P2) — form_id 2082/5328 서버 에러, unsold_by_size와 unsold_summary 동일 form_id 문제
- MOIS 인구/세대 2016~2022-08 CSV 미착수 (P2)
- serviceKey 로그 평문 노출 (P1)
- serviceKey 인코딩 이슈 (P2) — curl 시 -A "Mozilla/5.0" 필수
- dim_region 자동적재 미구현 (P2)
- API 한도 축소 3/5 적용 (10,000 → 1,000건/일)
- 비아파트 dedup 키 과소정의 (Phase 2 전 분석)
- 신고 지연 데이터 재수집 전략 (P3)
- 강원/전북 행정코드 변경 매핑 (P2)
- HTTP 401 연속 N회 조기 중단 미구현 (P3)
- LandScanner DB 확정 외 지표 잔존 (P3) — 19 indicators 중 이관 대상 외 지표 정리 필요

## LandScanner cron (현행 유지, Landbrief ETL 가동 전까지)
- 0 3 * * * load_all.py --region 11680 --months 12
- 0 0 * * * daily_check.sh (수집 진행률 모니터링)
- 5 0 * * * prefetch LAND_SALE --max-calls 990

## 다음 세션 작업 (우선순위 순)

### 최우선
1. Codex 태스크 제출: REB 백필 적재 실패 원인 추적 + ECOS FIXED_YEARS 변경 (태스크 본문 작성 완료)
2. prefetch 백필 완료 확인 (3/2): `sqlite3 data/real_estate.db "SELECT trade_type, MIN(yyyymm), MAX(yyyymm), COUNT(*) FROM fact_trade_raw WHERE yyyymm < '202000' GROUP BY trade_type;"`
3. INTENT.md v3.0 수정 4건 반영 (섹션 3.6, 5.2, 시트1 표, 용어사전)
4. ENGINE.md 설계 (캘린더 테이블, 지표별 월/연 집계 규칙, 결측 처리, 입출력 구조)

### 중순위
5. DDL v0.3 확정 (calendar_month 추가)
6. 로컬 PostgreSQL DDL v0.3 적용 + 샘플 데이터 적재 테스트
7. UNSOLD 미분양 수집 (MOLIT_STAT 500 에러 해결 후)
8. 청약홈 분양정보 수집 + fact_supply_raw 설계

### 후순위
9. 주택가격전망CSI 수집 (ECOS 통계표코드 확인)
10. 연별 10년 CSV 다운로드 계획 수립
11. 건축물대장 API 공급면적 확보 가능 여부 검증
12. 서버 1TB SSD 장착 + PostgreSQL 설치 + 전량 이관

## 코드 컨벤션
- DB 접속: 단일 connect() 강제
- 타임스탬프: DB=UTC, 출력=KST
- 타입: fact_trade_raw VARCHAR 유지, Mart에서 CAST
- dedup COALESCE: NULL → '' (빈문자열) 통일, 숫자 0 치환 안 함
- 정본 = 코드. 문서 불일치 시 문서 수정.
- prefetch 실행: --region 기본값 seoul, 전국 수집 시 반드시 --region all 지정
- curl MOLIT API 테스트: 반드시 -A "Mozilla/5.0" 포함
- Codex 운영 규칙: AGENTS.md에 통합 정의. 매 세션 말미 AGENTS.md 업데이트 필요 여부 점검.

**블록 2: CHANGELOG**

이 세션은 상당히 길어졌습니다. 컨텍스트가 많이 쌓인 상태입니다.

INTENT v2.1은 방금 확정되었으니 이걸로 저장하시면 됩니다. 다음 단계인 ENGINE.md 설계나 DDL 수정은 새 세션에서 시작하는 게 안전합니다.

지금 세션을 마무리하겠습니다. HANDOVER 업데이트를 드리겠습니다.

---

## HANDOVER 세션 14 CHANGELOG 블록

### #014 – 2026-03-01 (Session 14)

**fact_trade_raw 데이터 검증 완료**
- Codex verify_trade_raw.py 실행: PASS 8 / WARN 3 / FAIL 2
- FAIL 2건(C-1, C-2): dedup_key 컬럼 LandScanner에 미존재 → N/A 재분류
- WARN C-3: id 갭 128만건 (dedup INSERT OR IGNORE 결과, 정상)
- WARN D-2: 2020 이전 851건 (APT_RENT 548 + APT_SALE_DTL 303, 2019년 9~12월, 이관 시 필터)
- WARN D-3: etl OK 합계 > fact 건수 전 타입 (dedup에 의한 차이, 정상)
- 인코딩/포맷 전항목 PASS, 한글깨짐 0건, 쉼표 0건

**컬럼 매핑 + dedup 키 확인 완료**
- MIGRATION_COLUMN_MAP.md 작성: 58개 컬럼 1:1 매핑, 변환 필요 6개
- dedup 키: LandScanner uix_ftr_dedup (12컬럼 표현식 UNIQUE INDEX + INSERT OR IGNORE)
- 중복 검사: 14,152,214건 전수 스캔, 중복 0건
- COALESCE 정책: LandScanner COALESCE(...,0) vs Landbrief COALESCE(...,'') → 타입 환경 차이, 정책 변경 아님 (DDL 주석 반영 완료)

**apt_seq 단지코드 검증 완료**
- apt_seq 1개에 bldg_nm 1개: 0건 불일치 (완벽한 1:1)
- APT_SALE_DTL 41,176개 단지, APT_RENT 42,153개 단지
- 매매/임대 간 동일 코드 체계: 37,289개 공유 (90.6%)
- sgg_cd 2개인 apt_seq 8건: 행정구역 변경 케이스 (정상)
- KB 단지코드 의존성 제거 확정

**KB 데이터 상업적 이용 불가 확정**
- KB부동산 이용약관 제12조④: 영리목적 이용 금지
- KB부동산 이용약관 제14조①-5: 크롤링 금지
- 대안: 공공데이터 only로 전환, KB 지표는 실거래 기반 산출로 대체

**INTENT.md v2.1 확정**
- 제품 재정의: 리포트 소프트웨어 → 부동산 데이터 추출 도구
- KB 제거, 공공데이터 only
- Phase 1: 회사 파일럿 CLI 엑셀 (월별 36개월 + 연별 10년)
- Phase 2: 웹 SaaS, Phase 3: 리포트 자동화
- 단지코드: apt_seq 기반 dim_complex 자체 구축
- 엑셀 7시트 구성 확정
- 수집 지표 12종 + 참고 지표 3종
- 연별 10년 데이터: CSV 다운로드 → PostgreSQL 적재

**AGENTS.md v1.0 확정**
- Codex 운영 규칙 7개 섹션
- Codex 리뷰 2라운드 반영 (범위 완화, 불일치 처리, LandScanner 수정 조건부 허용 등)

**서버 수집 상태 확인**
- LAND_SALE cron 첫 실행 정상: 990건 호출, 47,143행 적재, 에러 0건
- cron 3개 현행 유지 (Landbrief ETL 가동 전까지)
- LAND_SALE: Landbrief에서 신규 수집으로 전환 예정, LandScanner 이관 대상에서 제외

**로컬 PostgreSQL 16 설치**
- Windows용 EDB 인스톨러로 설치 진행

**이관 정책 변경**
- LAND_SALE: 이관 대상에서 제외, Landbrief에서 신규 수집
- 이관 대상: 실거래 11종 (LAND_SALE 제외) + MOIS + ECOS
- 이관 필터: deal_year >= 2020

**HANDOVER 코드 컨벤션 업데이트**
- Codex 운영 규칙: AGENTS.md에 통합 정의
- 매 세션 말미 AGENTS.md 업데이트 필요 여부 점검

## 다음 세션 작업

### 최우선
1. INTENT v2.1 파일 저장 확인
2. ENGINE.md 설계 착수 (캘린더 테이블, 월별/연별 집계 규칙, 결측 처리)

### 중순위
3. DDL v0.3 업데이트 (dim_complex 추가, calendar_month 추가, 주택가격전망CSI 반영)
4. 로컬 PostgreSQL DDL 적용 + 샘플 데이터 적재 테스트

### 후순위
5. UNSOLD 미분양 수집
6. 청약홈 분양정보 수집
7. 주택가격전망CSI 수집 (ECOS 통계표코드 확인)
8. 연별 10년 CSV 다운로드 계획 수립
9. 건축물대장 API 공급면적 확보 가능 여부 검증
10. 서버 1TB SSD 장착 + PostgreSQL 설치 + 전량 이관

#015 – 2026-03-01 (Session 15)
DDL v0.2.1 확정

source_enum: KB 제거, APPLYHOME·ARCH_HUB 추가, HOUSTAT 유지
dim_complex 테이블 신규 추가 (apt_seq PK, supply_ar, lat/lng/households/built_year nullable, sgg_cd FK)
idx_ftr_aptseq 인덱스 추가 (trade_type + apt_seq + yyyymm)
주석 3건 추가: yyyymm 저장 규칙(DEAL_YMD 원본), is_fallback 의미, region_key GLOBAL='00000'
trg_complex_updated 트리거 추가
calendar_month는 ENGINE.md 설계 후 v0.3에서 추가 예정
Codex 조사 결과 반영 (DDL 결정사항 7건)

HOUSTAT: fact_indicator_month에 40건 존재 (HF_KHAI 2건, HF_LIR 19건, HF_PIR 19건, 서울 SIDO). 드랍 확정 지표이나 enum 유지
PRESALE: fact_trade_raw에 322,997건 존재. apt_seq 전건 빈값 (API 미제공). 이관 대상 유지, 단지 매칭 불가
yyyymm: API 요청 DEAL_YMD 원본 저장. deal_year/deal_month 파생 아님 확인
sgg_nm: APT 계열 0%, 오피스텔/상업/토지 99%+. API별 상이, 원천 보존 유지
is_fallback: 현재 distinct 값 0만 존재. SMALLINT 유지
region_key GLOBAL: 기존 데이터 '00000' 사용 중 (기준금리·CPI·CSI·ESI 각 36~37건). 동일 규칙 채택
apt_seq 조회: LandScanner에서 apt_seq WHERE/JOIN 쿼리 0건. Landbrief 단지 시트용으로 인덱스 선추가
HANDOVER 표기 정정

"실거래 11종 수집 완료" → "실거래 12종 수집 완료 (LAND_SALE 제외, PRESALE 포함)"
이관 대상: 실거래 12종 (LAND_SALE 제외) + MOIS + ECOS
ENGINE.md 설계 방향 확인

anchor month: 직전 완결월 (래그는 결측 처리)
연별 기준연도: 실행연도 - 1
DDL v0.2.1에서 calendar_month 제외, ENGINE.md 설계 후 v0.3에서 추가
청약홈 테이블 보류 결정

청약홈 분양정보는 fact_indicator_month 구조에 안 맞음 (건별 상세 데이터)
별도 테이블(fact_supply_raw 등) 필요하나, ENGINE.md에서 시트4 출력 형태 확정 후 설계
DDL v0.3 이후 v0.4에서 추가 예정
다음 세션 작업
최우선
ENGINE.md 설계 (캘린더 테이블, 지표별 월/연 집계 규칙, 결측 처리, 입출력 구조)
DDL v0.3 확정 (calendar_month 추가)
중순위
로컬 PostgreSQL DDL v0.3 적용 + 샘플 데이터 적재 테스트
UNSOLD 미분양 수집
청약홈 분양정보 수집 + fact_supply_raw 설계
후순위
주택가격전망CSI 수집 (ECOS 통계표코드 확인)
연별 10년 CSV 다운로드 계획 수립
건축물대장 API 공급면적 확보 가능 여부 검증
서버 1TB SSD 장착 + PostgreSQL 설치 + 전량 이관

네, 핸드오버 정리합니다.

---

#016 – 2026-03-01 (Session 16)

**INTENT.md v3.0 설계 확정**
- 엑셀 7시트 → 4시트 개편: 시트1 연별 추이(10년), 시트2 월별 추이(36개월), 시트3 로우데이터(유료), 시트4 참고자료.
- 시트1 지표 11행 확정: REB 매매/전세가격지수, 매매/전월세 거래건수, 미분양, 준공후미분양, 분양 평단가, 인구, 세대수, 기준금리, 주택가격전망CSI.
- 분양 평단가: 84㎡ 고정 폐기 → 세대수 최다 주택형 기준 최고분양가 ÷ 주택공급면적.
- 결측값 "-" 표기 + 하단 면책 각주 확정.
- 시군구 데이터 부재 시 시도/전국 대체, 행 레이블에 명기.
- 연별 값 기준(12월 값, 연간 SUM 등) 세부 규칙은 ENGINE.md에 위임.
- 파일 수정 4건 미반영: 섹션 3.6, 5.2, 시트1 표, 용어사전.

**청약홈 분양가 데이터 확인**
- 공공데이터포털 #15101047 CSV: 공급금액_분양최고금액만 제공 (평균/최저 없음).
- 13,210건, 무료, 로그인 없이 다운로드 가능.
- 주택형별 평단가 차이 5% 이내 확인 → 단일 대표 주택형(세대수 최다) 사용 결정.
- 가중평균 사용 안 함 (공식 기준 없는 주관적 계산).

**LandScanner 운영 방침 확정**
- LandScanner를 전 지표 수집·검증용 테스트베드로 유지.
- Landbrief는 LandScanner에서 1회 이관 후 독립 파이프라인 운영.
- 서버 1대: SQLite(LandScanner, 기존 SSD) + PostgreSQL(Landbrief, 신규 1TB SSD).

**실거래 2종 백필 실행**
- APT_SALE_DTL + APT_RENT, 2016-01~2019-12, 전국 268 시군구.
- prefetch_trade_raw.py --region all --months 124 nohup 실행.
- Codex 사전 점검 완료: generate_month_list(124) → 201512~202603 커버, is_done() 자동 스킵 정상.
- 이관 필터 deal_year >= 2020 → deal_year >= 2016으로 변경.

**REB 백필 시도 및 적재 실패 확인**
- load_all.py --region 11680 --months 124 --include-kreb 실행.
- R-ONE API 수집 정상 (statbl=A_2024_00045, 230행 × 다수 호출).
- DB 확인 결과 REB 지표 여전히 202502~202601 (12개월)만 존재.
- 원인 미확인: 수집은 됐으나 적재 로그(upsert/store/SUCCESS) 전무. normalize_subkey 또는 upsert_fact 단계에서 필터링 추정.
- Codex 태스크 작성 완료, 미제출.

**ECOS 10년 커버 불가 확인**
- config FIXED_YEARS=3 제한으로 --months 124 지정해도 3년치만 수집.
- BASE_RATE, CPI, ESI, CSI 모두 동일 제한.
- Codex 태스크에 FIXED_YEARS → 10 변경안 포함.

**MOLIT_STAT API 500 에러 확인**
- form_id 2082 (미분양), 5328 (준공후미분양) 모두 500 Server Error.
- unsold_by_size와 unsold_summary 동일 form_id(2080) 매핑 경고 기존재.

**MOIS 인구/세대 NODATA_ERROR 확인**
- 2015-11~2022-08 구간 전체 NODATA_ERROR.
- API가 과거 데이터를 미제공하는 것으로 추정. CSV 다운로드 필요.

**config 변경**
- QUERY_MONTHS_OPTIONS: [3,12,24,36] → [3,12,24,36,124] 추가.

**공공데이터포털 한도 확인**
- 3/5 이전: 10,000건/일, 3/5 이후: 1,000건/일.
- API 서비스별 독립 한도.

#017 – 2026-03-01 (Session 17)
Codex #C-016-1 완료: ECOS 10년 확장

ECOS_FIXED_YEARS = 10 신설, ECOS 수집 경로에서만 참조. 기존 FIXED_YEARS = 3 유지.
ECOS 외 참조 수집기: api_molit, crawl_kremap → 영향 없음.
DB 결과: BASE_RATE·CPI 201601~202601 (121개월), CSI·ESI 201601~202602 (122개월).
Codex #C-016-2 완료: REB_TRADE_VOLUME 202203 공백 복구

R-ONE API 단건 호출 정상 (강남구 202203, value=2496).
재수집 후 201601~202601 구간 누락 0건.
REB 실데이터 검증 완료

값 분포: NULL 0건, 0값 0건. 매매지수 66~111, 전세지수 91~116, 거래량 1,329~2,663. 정상.
시계열 연속성: 2015-10→2026-01 자연스러운 흐름. R-ONE 기준시점 2025-03=100.0.
region_key: 최초 강남구만 적재 → #C-017-1에서 전국 확장.
R-ONE API 응답 구조 분석

1회 호출당 230행: 전국(1) + 시도(17) + 권역 + 시군구.
CLS_ID: 6자리 R-ONE 자체코드. CLS_FULLNM 깊이로 전국/시도/권역/시군구 구분.
전국값: 한국부동산원 자체 산출 독립 지수 (시군구 합산 아님).
Codex #C-017-1 완료: REB 전국/시도/시군구 전체 적재 + 124개월 재수집

_to_dataframe_all_regions() 확장: 전국(00000) + 시도(2자리) + 시군구(5자리) 적재. 권역 제외.
region_level 자동 추론: region_key 길이 기반 (00000→GLOBAL, 2자리→SIDO, 5자리→SIGUNGU).
DB 결과: 3종 모두 region_cnt 207 (전국1 + 시도17 + 시군구189), 201509/10~202601, null 0건.
단일 지역(--region 11680) 기존 동작 유지 확인.
AGENTS.md v1.1 업데이트

3항 수정: Codex 태스크 지시서에 수정 대상 명시 시 사전 승인으로 간주. LandScanner 테스트베드 역할 명시.
참고 관찰: load_all.py 실행 시 REB_RENT_SUPPLY_DEMAND 등 확정 목록 외 지표도 적재됨 (DB 19 indicators). 이관 시 확정 지표만 필터링 필요.