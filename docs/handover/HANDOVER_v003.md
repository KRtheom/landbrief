---

# Landbrief Handover v003 (2026-02-26)

**블록 1: HANDOVER(기반 문서)**

## 문서 체계
- INTENT.md (v0.4): 프로젝트 정의/원칙/범위/지표/3트랙 상세. 심화 작업 시 공유.
- HANDOVER: 현재 상태. 매 세션 공유.
- 코드 레벨 검증: Codex 에이전트에 위임.

## 프로젝트 요약
판단/점수화 없이 공공·KB 부동산 데이터를 정렬해 3트랙 리포트 생성.
트랙 A: PF심사자료 (공인기관 12종, 36개월, 웹+PDF)
트랙 B: 회사 투자심의 (공인기관+KB, 10년, 시군구)
트랙 C: 공인중개사 대응 (KB, 추후 결정)
상세 → INTENT.md

## 서버
Ubuntu 24.04, i7-10700, 32GB, ssh -p 2222 deploy@122.45.64.200
개인 PC, 파일럿 후 VPS 전환 예정. 디스크 419GB 여유, 메모리 14GB 가용.

## 경로
- LandScanner: ~/real_estate_report (서버)
- Landbrief: 로컬 개발, 서버 배포 경로 ~/landbrief (미생성)
- DB: ~/real_estate_report/data/real_estate.db (서버, SQLite, 5.1GB)
- Landbrief DB: PostgreSQL (서버 미설치)

## Git
- LandScanner: github.com/KRtheom/real-estate-report.git (private)
- Landbrief: 저장소 미생성, 첫 커밋 cf3d336

## 확정 12종 지표 (공인기관)
APT_SALE_DTL, APT_RENT, REB_SALE_PRICE_INDEX, REB_TRADE_VOLUME, REB_RENT_PRICE_INDEX, UNSOLD_UNITS_SIGUNGU, UNSOLD_UNITS_COMPLETED, MACRO_BASE_RATE, HF_PIR, DEMO_POPULATION, DEMO_HOUSEHOLD, SUPPLY_INCOMING

## KB 지표 (PublicDataReader, API키 불필요)
검증완료 8종: KB_AVG_PRICE_PER_SQM, KB_PRICE_INDEX_CHANGE, KB_JEONSE_RATIO, KB_RENT_CONVERSION, KB_BUYER_INDEX, KB_PRICE_OUTLOOK, KB_MEDIAN_PRICE, KB_SIZE_PRICE_INDEX
미검증 2종: KB_PRICE_INDEX_MONTHLY (파라미터 재확인), KB_PIR (메뉴코드 누락)

## source CHECK 6종
REB_RONE, STAT_MOLIT, ECOS, HOUSTAT, MOIS, DATA_GO_KR

## 수집 현황
- APT 2종: 완료 (78개월, 201909~202602, 이관 시 202001 이전 제외)
- 10종 74개월: PID 980574 진행 중 (13,168,180건, 11종 완료, RH_RENT 수집 중)
- LAND_SALE: 1,732건, 1개 지역만 존재 (수집 미도달, P2)
- 202303 APT 급증: API 제공범위 변경 추정, 시계열 비교 시 경계 인지 필요
- fact_indicator_month: 테스트 데이터만, Landbrief ETL로 재수집 예정

## DDL
- v0.2 사실상 확정 (Codex #003 검증 5건 통과, dedup 전수 검증 12종 중복 0건)
- 파일: ~/landbrief/docs/DDL.md (로컬)
- PostgreSQL 설치 후 적용 대기

## 이관 정책
- fact_trade_raw: 전량 이관 (SQLite→PostgreSQL, VARCHAR 그대로, 202001~ 기준)
- fact_indicator_month: 이관 안 함
- dim_region: 이관 (컬럼명 매핑 필요)

## 미결/블로커
- serviceKey 로그 평문 노출 (P1)
- API 타임아웃/재시도 미구현 (P1) — PID 468336 hang 원인, Landbrief ETL 신규 구현 시 필수
- SUPPLY_INCOMING 소스 미확정 (P1) — 트랙 B 분양물량 대응
- serviceKey 인코딩 이슈 (P2) — curl 테스트 시 400, 수집 스크립트(Python)는 정상. 모니터링용 curl 수정 필요
- dim_region 자동적재 미구현 (P2)
- LAND_SALE 2023-03부터만 존재 (P2) — 수집 완료 후 재확인
- API 한도 축소 3/5 전후 (적용 범위 미확인)
- KB 미검증 2종 (P3) — KB_PRICE_INDEX_MONTHLY, KB_PIR
- 비아파트 dedup 키 과소정의 (Phase 2 전 분석)
- 신고 지연 데이터 재수집 전략 (P3) — 슬라이딩 윈도우 N개월, ETL 설계 시 결정

## 태스크
G1 ✅ | G2 DDL ✅ (확정 대기, PG 설치 후 적용) | G3~G10 대기

## 다음 세션 작업 (우선순위 순)

### 최우선 (3/5 전)
1. daily_check.sh 서버 배포 + cron 등록
2. 실거래가 12종 수집 완료 + 검증 (PID 980574 완료 대기)
3. 인구 수집 스크립트 (MOIS API, 시군구/월별 2016~2025)
4. 미분양 수집 스크립트 (STAT_MOLIT API, 시군구/월별 2016~2025)

### 후순위
5. SUPPLY_INCOMING 소스 확정
6. KB 평단가 10년치 수집 스크립트
7. PostgreSQL 설치 + DDL v0.2 적용 + 이관

## 코드 컨벤션
- DB 접속: 단일 connect() 강제
- 타임스탬프: DB=UTC, 출력=KST
- 타입: fact_trade_raw VARCHAR 유지, Mart에서 CAST
- dedup COALESCE: NULL → '' (빈문자열) 통일, 숫자 0 치환 안 함
- 정본 = 코드. 문서 불일치 시 문서 수정.
```

**블록 2: CHANGELOG**

## 2026-02-26 #007
- Codex #003 결과 분석 완료
  - 검증 5건 중 4건 OK, dedup(검증2) 조건부 NG
  - trade_type ENUM 13종 확정, dim_region 269행 정합, 컬럼 54개 호환, source_enum 6종 확정
  - dedup: COALESCE(_, '') 기준 전수 검증 실시 → 12종 12,587,637건 중복 0건 → OK
  - DDL v0.2 사실상 확정
- 이관 기준 시작월 확정
  - APT 201909~201912: 테스트 데이터(303건), 이관 제외
  - 전 trade_type 통일 202001~ 기준 확정
- 수집 현황 점검
  - PID 980574 정상 가동, 13,168,180건, 11종 완료, RH_RENT 수집 중
  - LAND_SALE: 1,732건, 1개 지역(11680), 수집 미도달 확인 → P2 블로커 등록
  - 202303 APT 급증(APT_RENT 42K→107K, APT_SALE_DTL 12K→35K): API 제공범위 변경 추정
  - 202602 전 유형 건수 저조: 월 미종료+신고 지연, 정상
  - NULL 검증: 전 12종 핵심 컬럼 NULL 0건, 금액 3개 동시 NULL 0건
- healthcheck_monthly.csv 로컬 보관
- 서버 상태: 디스크 4%(419GB 여유), 메모리 14GB 가용, PostgreSQL 미설치
- 12종 trade_type 데이터 구조 확인
  - SH_RENT: exclu_use_ar 없음(deal_area로 면적 표현), Codex #003 NULL 원인 확인
  - PRESALE: build_year 대부분 NULL(미완공), 정상
  - 비주거(COMM/INDU/LAND): 주거용 컬럼 NULL, 토지/건물 컬럼 채워짐, 정상
- KB PublicDataReader 검증
  - 무료, API키 불필요, pip install PublicDataReader
  - 8종 검증 완료, 2종 미검증(KB_PRICE_INDEX_MONTHLY, KB_PIR)
  - 수집: 시도당 1회 호출, 전국 17회, 월간 기본
- 3트랙 구조 확정
  - 트랙 A: PF심사자료 / 트랙 B: 회사 투자심의 / 트랙 C: 공인중개사 대응
- 회사 요청 6종 소스 매핑 확정 (INTENT 5-B)
- 평단가 산출 방식 확정: KB ㎡당평균가격(공급면적기준), 단지별은 KB 캐시
- daily_check.sh 작성 완료 (서버 미배포)
- INTENT.md v0.4 작성
- HANDOVER v003 작성
- **다음: daily_check.sh 배포 → 실거래 12종 수집 완료+검증 → 인구/미분양 수집(3/5전 긴급) → PostgreSQL 이관은 후순위**