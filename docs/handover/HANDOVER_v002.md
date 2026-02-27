# Landbrief Handover v002 (2026-02-26)

**블록 1: HANDOVER(기반 문서)**

## 문서 체계
- INTENT.md: 프로젝트 정의/원칙/범위/지표 상세. 심화 작업 시 공유.
- HANDOVER: 현재 상태. 매 세션 공유.
- 코드 레벨 검증: Codex 에이전트에 위임.

## 프로젝트 요약
판단/점수화 없이 공공 부동산 데이터를 정렬해 A/B/C 3지역 비교 리포트 생성.
Phase 1: 아파트, 36개월, 웹 기본 + 유료 PDF. 상세 → INTENT.md

## 서버
Ubuntu 24.04, i7-10700, 32GB, ssh -p 2222 deploy@122.45.64.200
개인 PC, 파일럿 후 VPS 전환 예정.

## 경로
- LandScanner: ~/real_estate_report (서버)
- Landbrief: 로컬 개발, 서버 배포 경로 ~/landbrief (하드 확장 후 생성 예정)
- DB: ~/real_estate_report/data/real_estate.db (서버, SQLite)
- Landbrief DB: PostgreSQL (서버 설치 예정)

## Git
- LandScanner: github.com/KRtheom/real-estate-report.git (private)
- Landbrief: 저장소 미생성, 첫 커밋 cf3d336

## 확정 12종 지표
APT_SALE_DTL, APT_RENT, REB_SALE_PRICE_INDEX, REB_TRADE_VOLUME, REB_RENT_PRICE_INDEX, UNSOLD_UNITS_SIGUNGU, UNSOLD_UNITS_COMPLETED, MACRO_BASE_RATE, HF_PIR, DEMO_POPULATION, DEMO_HOUSEHOLD, SUPPLY_INCOMING

## source CHECK 6종
REB_RONE, STAT_MOLIT, ECOS, HOUSTAT, MOIS, DATA_GO_KR

## 수집 현황
- APT 2종 74개월: 완료
- 10종 74개월: PID 980574 진행 중 (198,320건 중 ~1,300건, 예상 3/1)
- 기간: 202001~202602
- fact_indicator_month: 테스트 데이터만, Landbrief ETL로 재수집 예정

## 이관 정책
- fact_trade_raw: 전량 이관 (SQLite→PostgreSQL, VARCHAR 그대로)
- fact_indicator_month: 이관 안 함
- dim_region: 이관 (컬럼명 매핑 필요)

## 미결/블로커
- serviceKey 로그 평문 노출 (P1)
- API 타임아웃/재시도 미구현 (P1) — PID 468336 hang 원인, Landbrief ETL 신규 구현 시 필수
- serviceKey 인코딩 이슈 (P2) — curl 400 원인, 수집 정상 동작 중이나 재발 가능
- dim_region 자동적재 미구현 (P2)
- API 한도 축소 3/5 전후 (적용 범위 미확인)
- 비아파트 dedup 키 과소정의 (Phase 2 전 분석)
- SUPPLY_INCOMING 수집기 미구현 (Landbrief 신규 작성)
- 신고 지연 데이터 재수집 전략 (P3) — 슬라이딩 윈도우 N개월 재수집 방식, 지표별 윈도우 크기·대상 지역 범위 ETL 설계 시 결정

## 태스크
G1 ✅ | G2 DDL ⏳ (v0.2 작성 완료, Codex #003 검증 대기) | G3~G10 대기

## 코드 컨벤션
- DB 접속: 단일 connect() 강제
- 타임스탬프: DB=UTC, 출력=KST
- 타입: fact_trade_raw VARCHAR 유지, Mart에서 CAST
- 정본 = 코드. 문서 불일치 시 문서 수정.

---

**블록 2: CHANGELOG**

## 2026-02-26 #006
- Codex 검증 #001 분석 완료
  - source 코드 실제 값 6종 확정 (REB_RONE, STAT_MOLIT, ECOS, HOUSTAT, MOIS, DATA_GO_KR)
  - DEMO 2종 source: KOSIS→MOIS 정정 (API=공공데이터포털, 원천=행안부)
  - 정본 원칙 확정: 정본=코드, 문서 불일치 시 문서 수정
- DDL 설계 결정 3건 확정
  - source: 코드 실제 값 기준, 매핑 테이블 없음
  - dedup: 변경 불필요 (APT 2종 중복 0건 서버 검증 완료)
  - busy_timeout: 단일 connect() 함수 강제
- HANDOVER v002 확정
  - INTENT 압축 섹션 추가, 코드 레벨 상세 제거
  - 일반 모드(HANDOVER만) / 심화 모드(+INTENT) 운영
- PostgreSQL 채택 (SQLite 경유 없이 바로 전환)
- DDL v0.2 작성 (~/landbrief/docs/DDL.md)
  - trade_type ENUM 13종 (SH_SALE, SH_RENT, COMM_SALE, APT_SALE 추가)
  - uuid-ossp 제거, unit VARCHAR(50), etl_status ENUM
  - dedup: deal_year+deal_month 유지, COALESCE(_, '') 통일
  - VARCHAR 유지 + Mart CAST 확정
  - FK 미설정, ETL 로깅으로 대체
- Codex 검증 #002 분석 완료
  - trade_type 13종 확인, dedup 원본과 DDL 차이 발견→수정 반영
  - dim_region 컬럼명 차이 확인 (이관 시 매핑)
  - SUPPLY_INCOMING 수집기 미구현 확인
- fact_indicator_month 서버 점검
  - SIGUNGU 지표: 강남구 1곳×12개월 테스트 데이터만 존재
  - SUPPLY_INCOMING, UNSOLD_UNITS_SIGUNGU: 미수집
  - 이관 정책 수정: fact_indicator_month 이관 안 함, Landbrief ETL로 재수집
- INTENT.md v0.3 작성
  - API 제공기관: API 키 기준 통일
  - 섹션 5 [매크로/부담능력] 추가
  - 결측 표현: 월별("-") vs 반기/분기(직전값 캐리) 경계 명확화
  - Phase 2 세대수 별도 API 필요 명시
  - Database: PostgreSQL 단일
- 수집 모니터링
  - PID 468336 hang 발견 (금정구 PRESALE 202308, 17시간 대기) → kill
  - PID 980574 재시작, 정상 진행 (198,320건 중 ~1,300건)
  - curl 400은 serviceKey 인코딩 이슈, API 차단 아님
  - 예상완료 3/1, 3/5 한도 축소 전 여유 있음
- Codex 검증 지시서 #003 작성 (DDL 최종 검증 + INTENT 데이터 정합성)
- **다음: Codex #003 결과 분석 → DDL 확정 → 수집 완료 모니터링 → 서버 COALESCE 재검증**

## 블록 3: 세션 작업 기록 (v003, 2026-02-26)

### 서버 점검 결과
- PID 980574 가동 중 (~10h30m), RH_RENT 완도군 202310 수집 중
- 총 13,168,180건, DB 5.1GB
- 디스크 4% 사용 (419GB 여유), 메모리 14GB 가용
- PostgreSQL 미설치, ~/landbrief 서버 미생성
- 11종 수집 완료, RH_RENT 수집 중, LAND_SALE 이상 의심 (1,732건, 2023-03~만)


[]### 회사 요청 6종 분석
- 평균평단가 → 공급면적 필요 → 실거래 API는 전용면적만 제공
- apt_seq 100% 채움 (41,176개 고유 단지)
- KB 공식 오픈 API 없음 (dataapi.co.kr은 유료 제3자)
- kbland.kr 내부 엔드포인트로 SUPPLYAR/TOTALAR 조회 가능 확인
- 단지별 평단가는 사용자 조회 시 KB에서 가져와 캐시하는 방식으로 결정
- 한국부동산원 공동주택 단지 식별정보 API 확인: 면적 정보 없음 (단지ID, 주소, 세대수만)

### KB PublicDataReader 검증
- 무료, API키 불필요, pip install PublicDataReader
- 시군구 단위 확인: 서울 25구, 부산 16구군 모두 반환
- 1회 호출로 해당 시도 전 시군구 데이터 반환, 전국 17회 호출
- 월간 기본, 일부 지표 주간 가능 (월간주간구분코드 파라미터)
- 검증 결과:
  - ✅ ㎡당매매평균가격 (시군구, 2004~)
  - ✅ 가격지수증감률 (시군구, 1986~)
  - ✅ 전세가격비율 (시군구, 1998~)
  - ✅ 전월세전환율 (시도급, 2015~)
  - ✅ 매수우위지수 (시도급, 2000~)
  - ✅ 매매가격전망지수 (시도급, 2013~)
  - ✅ 중위가격 (시도급, 2008~)
  - ✅ 면적별가격지수 (시도급, 2013~)
  - ❌ 가격지수(월간매매): NoneType 에러, 파라미터 재확인 필요
  - ❌ PIR: 메뉴코드 파라미터 누락, 재시도 필요

### 3트랙 구조 확정
- 트랙 A: Landbrief PF (공인기관 12종, 36개월, 웹+PDF)
- 트랙 B: 회사 투자심의용 (공인기관+KB, 10년 2016~2025, 시군구, 광역시는 구까지)
- 트랙 C: 공인중개사 대응 (KB 시장심리/전망 지표 중심)

### 회사 요청 6종 소스 매핑 확정
| 요청 | 소스 | 긴급도 |
|---|---|---|
| 시별 인구 | MOIS 공공데이터 | 3/5전 긴급 |
| 시별 거래량 | fact_trade_raw COUNT | 수집완료 후 산출 |
| 시별 분양물량 | 미확정(SUPPLY_INCOMING) | 소스 확인 필요 |
| 시별 미분양물량 | STAT_MOLIT 공공데이터 | 3/5전 긴급 |
| 시별 평균평단가 | KB ㎡당평균가격 | KB 확정 |
| 단지별 전년도 평단가 | KB 캐시방식 | KB 확정 |

### 일일검증 스크립트 작성
- 파일: daily_check.sh (서버 미배포)
- 체크 항목 11개: 프로세스 생존, 최신 로그, DB 크기, 유형별 건수, 총건수+전일 증감, 시군구 커버리지, 월별 커버리지, 진행률(%), 이상 데이터(금액NULL/yyyymm비정상/미매칭시군구), fact_indicator_month 상태, 디스크/메모리

### 미결 추가
- B7: SUPPLY_INCOMING 소스 미확정 → P1 격상
- B9: LAND_SALE 2023-03부터만 존재 → P2 신규

### 다음 세션 작업 (우선순위 순)
1. daily_check.sh 서버 배포 + cron 등록
2. 인구 수집 스크립트 (MOIS API) — 3/5전 긴급
3. 미분양 수집 스크립트 (STAT_MOLIT API) — 3/5전 긴급
4. 분양물량(SUPPLY_INCOMING) 소스 확정
5. 10종 수집 완료 검증 (LAND_SALE 포함)
6. KB 평단가 10년치 수집 스크립트
7. PostgreSQL 설치 + DDL v0.2 적용