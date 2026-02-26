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