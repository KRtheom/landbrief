
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

### 참고 지표 3종 (수집 완료, 엑셀 시트1 참고자료)
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

## 수집 현황 (2026-03-01 기준)

| 데이터 | 상태 | 비고 |
|---|---|---|
| 실거래 11종 | 완료 (각 19,832건 OK) | |
| LAND_SALE | 진행 중 (OK 2,995 / PENDING 556) | cron 매일 00:05 KST, Landbrief에서 신규 수집 전환 예정 |
| MOIS 인구/세대 | 완료 (20,996건, 299지역) | 2016~2022-08은 CSV 미착수 |
| ECOS 경제지표 | 완료 | 기준금리, CPI, CSI, ESI |
| UNSOLD 미분양 | 테스트 수준 (11건) | MOLIT_STAT_API_KEY 별도 키 |
| 청약홈 분양정보 | 미착수 | 서비스키 신청 완료 |
| 주택가격전망CSI | 미착수 | ECOS 통계표코드 미확인 |
| 연별 10년 CSV | 미착수 | |

- fact_trade_raw: 14,152,214건
- 공공데이터포털 한도 리셋: 매일 자정(00:00) KST, API 서비스별 독립 한도

## 데이터 검증 현황 (세션 14 완료)
- fact_trade_raw 검증: PASS 8 / WARN 3(정상) / FAIL 2(N/A)
- 인코딩·포맷 전항목 PASS, 한글깨짐 0건, 쉼표 0건
- 컬럼 매핑 58개 확정 (MIGRATION_COLUMN_MAP.md)
- dedup 키 검증: 14,152,214건 전수 스캔, 중복 0건
- 2020 이전 851건: 이관 시 deal_year >= 2020 필터

## DDL
- v0.2 사실상 확정 (dedup 전수 검증 통과, 중복 0건)
- dedup COALESCE 정책 주석 반영 완료
- 파일: ~/landbrief/docs/DDL.md (로컬)
- v0.3 업데이트 필요: dim_complex 추가, calendar_month 추가

## 이관 정책
- fact_trade_raw: 실거래 11종 이관 (LAND_SALE 제외)
- 이관 필터: deal_year >= 2020
- dim_region: 이관 (컬럼명 매핑 필요)
- MOIS 인구/세대: 이관
- ECOS 경제지표: 이관
- fact_indicator_month: 이관 안 함

## 미결/블로커
- ENGINE.md 미작성 (P1) — 정렬 엔진 핵심 IP
- 건축물대장 API 공급면적 확보 가능 여부 미검증 (P2) — 공급평단가 산출 필수
- 연별 10년 CSV 다운로드 미착수 (P2)
- 주택가격전망CSI ECOS 통계표코드 미확인 (P3)
- serviceKey 로그 평문 노출 (P1)
- serviceKey 인코딩 이슈 (P2) — curl 시 -A "Mozilla/5.0" 필수
- dim_region 자동적재 미구현 (P2)
- API 한도 축소 3/5 전후 (적용 범위 미확인)
- 비아파트 dedup 키 과소정의 (Phase 2 전 분석)
- 신고 지연 데이터 재수집 전략 (P3)
- 강원/전북 행정코드 변경 매핑 (P2)
- HTTP 401 연속 N회 조기 중단 미구현 (P3)

## LandScanner cron (현행 유지, Landbrief ETL 가동 전까지)
- 0 3 * * * load_all.py --region 11680 --months 12
- 0 0 * * * daily_check.sh (수집 진행률 모니터링)
- 5 0 * * * prefetch LAND_SALE --max-calls 990

## 다음 세션 작업 (우선순위 순)

### 최우선
1. ENGINE.md 설계 착수 (캘린더 테이블, 월별/연별 집계 규칙, 결측 처리)

### 중순위
2. DDL v0.3 업데이트 (dim_complex, calendar_month, 주택가격전망CSI 반영)
3. 로컬 PostgreSQL DDL 적용 + 샘플 데이터 적재 테스트
4. UNSOLD 미분양 수집
5. 청약홈 분양정보 수집

### 후순위
6. 주택가격전망CSI 수집 (ECOS 통계표코드 확인)
7. 연별 10년 CSV 다운로드 계획 수립
8. 건축물대장 API 공급면적 확보 가능 여부 검증
9. 서버 1TB SSD 장착 + PostgreSQL 설치 + 전량 이관

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