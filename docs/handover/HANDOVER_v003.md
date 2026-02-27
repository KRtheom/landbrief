---

# Landbrief Handover v003 (2026-02-26)

**블록 1: HANDOVER(기반 문서)**

> **⚠ 수정 규칙**: 수정사항 안내 시 반드시 **섹션 단위**로 전체 교체 블록을 마크다운 원문으로 제공할 것. 줄 단위 지시, 화살표(→) 표기, diff 형식 금지.

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

## source CHECK 7종
REB_RONE, STAT_MOLIT, ECOS, HOUSTAT, MOIS, DATA_GO_KR, KB

## 수집 현황 (2026-02-27 기준)

| 데이터 | 상태 | 비고 |
|---|---|---|
| 실거래 12종 | 83.3% (165,220/198,320) | API 일일한도 도달, 익일 재실행 |
| MOIS 인구/세대 | 완료 (264/268) | 화성 분구 4건 빈 응답 (정상) |
| ECOS 경제지표 | 완료 | 기준금리, CPI, CSI, ESI |
| HF 지표 | 테스트 수준 | PIR 19건, KHAI 2건 |
| UNSOLD 미분양 | 테스트 수준 | 11건 |
| KB 지표 | 미착수 | 메뉴코드 미확인 |

- 실거래 APT 2종: 78개월 완료 (201909~202602), 나머지 10종 진행 중
- LAND_SALE: 15개 시군구만 수집 (가장 느림)
- MOIS API 제공 시작: 2022-09 (2016~2022-08은 CSV 34회 수동 다운로드 후순위)
- 강원(51xxx) 2023-06~, 전북(52xxx) 2024-01~, 구 코드(42xxx/45xxx) 데이터 공존
- fact_indicator_month: LandScanner 테스트 데이터, Landbrief ETL로 재수집 예정

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
- fact_indicator_month SQLite 스키마 차이 (P3) — inserted_at/updated_at NOT NULL DEFAULT 없음, source CHECK 목록 Landbrief DDL과 불일치
- 강원/전북 행정코드 변경 매핑 (P2) — dim_region에 신규 코드(51xxx/52xxx)만 존재, 구 코드(42xxx/45xxx) 없음. 리포트 시계열 연결 시 구→신 매핑 필수. 화성시 분구(41591~41597)도 동일 패턴.

## 태스크
G1 ✅ | G2 DDL ✅ (확정 대기, PG 설치 후 적용) | G3~G10 대기

## 다음 세션 작업 (우선순위 순)

### 최우선 (3/5 전)
  1. MOIS 인구 수집 완료 검증
  2. 실거래가 12종 수집 완료 + 검증 (PID 980574)
  3. 미분양 수집 스크립트 (STAT_MOLIT API, 별도 키, 긴급도 낮음)

### 후순위
  4. MOIS 인구 CSV 2016~2022-08 (17시도 × 2회 = 34회 다운로드 + 파싱)
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

## 2026-02-26 #008
- daily_check.sh 서버 배포 완료
  - 11개 항목 검증 스크립트, cron 매일 09:00 KST 등록
  - dim_region 컬럼명 불일치 수정 (sgg_cd → region_code)
  - 미매칭 시군구 쿼리 정상 동작 확인
- MOIS 인구 API 조사
  - 현재 API(stdgPpltnHhStus): 2022-09부터만 데이터 제공 (2022-11 신규 등록)
  - 2016~2022-08: jumin.mois.go.kr CSV 다운로드 또는 KOSIS API 대체 필요
  - CSV: 시도 단위 60개월 제한, 17시도 × 2회 = 34회 수동 다운로드
  - EUC-KR 인코딩, 행정기관코드 10자리(앞 5자리=시군구코드)
- MOIS 인구 전국 수집 실행
  - PID 1299217, 268개 시군구 × 202209~202512 (40개월)
  - 시군구당 ~70초, 예상 완료 약 5시간
  - 1차 실행 실패: fact_indicator_month.inserted_at NOT NULL DEFAULT 없음
  - 스크립트 수정 후 재실행, 정상 적재 확인 (종로구 80건)
  - API 호출 한도: 3,752회 예상, 실거래+인구 합산 일일 45K+회인데 제한 미발동
- UNSOLD 미분양 확인
  - MOLIT_STAT_API_KEY 별도 키, 3/5 DATA_GO_KR 한도 축소와 무관
  - 기존 api_molit.py에 fetch_unsold_by_sigungu 존재, 전국 일괄 반환 구조
- fact_indicator_month SQLite 스키마 확인
  - inserted_at/updated_at NOT NULL (DEFAULT 없음)
  - source CHECK: MOLIT_TRADE, STAT_MOLIT, REB_RONE, HOUSTAT, HF_HOUSTAT, HF_ODCLOUD 등 Landbrief DDL과 상이
- **다음: MOIS 수집 완료 검증 → 실거래 12종 완료 검증 → 미분양 수집 → CSV 인구 후순위**

### #009 – 2026-02-27 (Session 9)

**환경 / 도구**
- VS Code Remote-SSH 설정 완료 (analytics-srv 접속)
- SQLite Viewer, Markdown Preview Enhanced, Git Graph 확장 설치
- 계정 SSH 키 GitHub 등록 → 서버에서 직접 push 가능

**Agent Skills 3종 생성**
- `.github/skills/db-schema/SKILL.md` – DB 스키마 정의 (fact_trade_raw 실제 스키마 반영)
- `.github/skills/api-collector/SKILL.md` – API 수집 패턴 정의
- `.github/skills/coding-rules/SKILL.md` – 코딩 규칙 및 데이터 규격

**데이터 수집 현황**
- 실거래 12종: 83.3% 완료 (165,220 / 198,320 호출), API 일일한도 도달로 내일 재실행
- MOIS 인구: 264/268 성공, 4건 빈 응답 (화성 분구 신설 자치구 — 정상)
- 강원(51xxx) 2023-06~, 전북(52xxx) 2024-01~, 구 코드(42xxx/45xxx) 데이터 공존 확인

**Git 정리**
- 서버 계정 SSH 키 등록 (read-only Deploy Key → 계정 키 전환)
- 테스트 xlsx 4건 삭제, test_starts.json .gitignore 추가
- 커밋: 6286a14, 730c558, 61de45c, 97e87c5

**확인된 이슈**
- fact_trade_raw 스키마와 SKILL.md 불일치 → 수정 완료
- API 일일한도(429 Too Many Requests) → 익일 재실행으로 해결

### 다음 세션 (Session 10)
1. 실거래 수집 재실행 (남은 33,100건)
2. 수집 완료 후 전체 데이터 검증
3. UNSOLD 미분양 수집 스크립트 실행 (MOLIT_STAT API)
4. CSV 인구 다운로드 계획 확정 (2016~2022-08, 34회)
5. db-schema SKILL.md fact_indicator_month 스키마 실제 확인 및 수정