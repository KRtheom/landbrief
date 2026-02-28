# Landbrief Handover v004 (2026-02-28)

**블록 1: HANDOVER(기반 문서)**

> **⚠ 수정 규칙**: 수정사항 안내 시 반드시 **섹션 단위**로 전체 교체 블록을 마크다운 원문으로 제공할 것. 줄 단위 지시, 화살표(→) 표기, diff 형식 금지.

## 문서 체계
- INTENT.md (v0.4): 프로젝트 정의/원칙/범위/지표/3트랙 상세. 심화 작업 시 공유.
- HANDOVER: 현재 상태. 매 세션 공유.
- API 기술문서 정리: MOLIT_TRADE_API_SPEC.md (실거래 13종) + ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md (ECOS·REB·청약홈·건축HUB) + MOLIT_STAT_API_SPEC.md (미분양 2종). 수집 스크립트 개발·ERROR_CODE_HANDLING.md 작성 기반.
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
APT_SALE_DTL, APT_RENT, REB_SALE_PRICE_INDEX, REB_TRADE_VOLUME, REB_RENT_PRICE_INDEX, UNSOLD_UNITS_SIGUNGU, UNSOLD_UNITS_COMPLETED, MACRO_BASE_RATE, HF_PIR(드랍), DEMO_POPULATION, DEMO_HOUSEHOLD, SUPPLY_INCOMING

- HF_PIR 드랍 (세션 11 확정) → 확정 지표 실질 11종
- SUPPLY_INCOMING 소스: 청약홈 분양정보 API (APPLYHOME, 서비스키 #15098547, odcloud 경유)

## KB 지표 (PublicDataReader, API키 불필요)
검증완료 8종: KB_AVG_PRICE_PER_SQM, KB_PRICE_INDEX_CHANGE, KB_JEONSE_RATIO, KB_RENT_CONVERSION, KB_BUYER_INDEX, KB_PRICE_OUTLOOK, KB_MEDIAN_PRICE, KB_SIZE_PRICE_INDEX
미검증 2종: KB_PRICE_INDEX_MONTHLY (파라미터 재확인), KB_PIR (메뉴코드 누락)

## source CHECK 8종
REB_RONE, STAT_MOLIT, ECOS, HOUSTAT, MOIS, DATA_GO_KR, KB, APPLYHOME

## API 기술문서 정리 현황 (2026-02-28 기준)

| 소스 | 상태 | 비고 |
|---|---|---|
| MOLIT 실거래 13종 (apis.data.go.kr) | ✅ 정리 완료 | MOLIT_TRADE_API_SPEC.md |
| ECOS 3종 (ecos.bok.or.kr) | ✅ 정리 완료 | 통계표코드(기준금리/CPI/CSI/ESI) 코드에서 확인 필요 |
| REB R-ONE 3종 (reb.or.kr) | ✅ 정리 완료 | 통계표ID(매매가격지수/거래량/전세가격지수) 미확인 |
| 청약홈 10종 (api.odcloud.kr) | ✅ 정리 완료 | |
| MOLIT_STAT 2종 (stat.molit.go.kr) | ✅ 정리 완료 | form_id=2082(미분양), 5328(공사완료후) |
| 건축HUB 17종 (apis.data.go.kr) | ✅ 정리 완료 | 향후 확장용, 현재 스코프 밖 |
| MOIS (apis.data.go.kr) | 미정리 (팩트 미확인) | 수집 완료됐으나 기술문서 PDF 없음, Swagger UI 동적 로딩 |
| HF (주택금융공사) | 드랍 | HF_PIR 지표 자체 드랍 |
| KB (PublicDataReader) | 별도 경로 | 라이브러리 경유, 공식 기술문서 없음 |

## 수집 현황 (2026-02-28 기준)

| 데이터 | 상태 | 비고 |
|---|---|---|
| 실거래 11종 | 완료 (각 19,832건 OK) | 429 피해 없음 확인 |
| 실거래 LAND_SALE | 미완 (OK 1,432 / PENDING 653 / 미실행 ~17,747) | 429 피해 1,049건 PENDING 리셋 완료, 재수집 중 |
| MOIS 인구/세대 | 완료 (20,996건, 299지역, 202209~202601) | 빈 응답 4건은 화성시 분구 신설코드 (정상) |
| ECOS 경제지표 | 완료 | 기준금리, CPI, CSI, ESI |
| UNSOLD 미분양 | 테스트 수준 | 11건, MOLIT_STAT_API_KEY 별도 키 |
| KB 지표 | 미착수 | 메뉴코드 미확인 |
| 청약홈 분양정보 | 미착수 | 서비스키 신청 완료, 테스트 호출 미실행 |

- fact_trade_raw: 14,139,806건 (전체 OK 219,281 / 219,934, 99.7%)
- LAND_SALE: 가장 느림, 일일 한도 도달 반복
- MOIS API 제공 시작: 2022-09 (2016~2022-08은 CSV 34회 수동 다운로드 후순위)
- MOIS region_key 299개 > dim_region 269개 = 강원/전북/화성 신·구 코드 공존
- 강원(51xxx) 2023-06~, 전북(52xxx) 2024-01~, 구 코드(42xxx/45xxx) 데이터 공존
- fact_indicator_month: LandScanner 테스트 데이터, Landbrief ETL로 재수집 예정
- 입주예정물량 CSV 임시 확보 (한국부동산원_20251231), DDL 추후 작성, API 자동수집 전환 예정

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
- API 429/타임아웃 미처리 (P1) — prefetch_trade_raw.py가 HTTP 429를 OK/row_count=0으로 기록, resume 로직이 skip. 통합 처리 원칙 5개 확정, ERROR_CODE_HANDLING.md 미작성, 코드 수정은 수집 완료 후
- serviceKey 인코딩 이슈 (P2) — curl 테스트 시 400, 수집 스크립트(Python)는 정상. 모니터링용 curl 수정 필요
- dim_region 자동적재 미구현 (P2)
- LAND_SALE 수집 미완 (P2) — OK 1,432 / 전체 19,832, 일일 한도 반복 도달
- API 한도 축소 3/5 전후 (적용 범위 미확인)
- KB 미검증 2종 (P3) — KB_PRICE_INDEX_MONTHLY, KB_PIR
- 비아파트 dedup 키 과소정의 (Phase 2 전 분석)
- 신고 지연 데이터 재수집 전략 (P3) — 슬라이딩 윈도우 N개월, ETL 설계 시 결정
- fact_indicator_month SQLite 스키마 차이 (P3) — inserted_at/updated_at NOT NULL DEFAULT 없음, source CHECK 목록 Landbrief DDL과 불일치
- 강원/전북 행정코드 변경 매핑 (P2) — dim_region에 신규 코드(51xxx/52xxx)만 존재, 구 코드(42xxx/45xxx) 없음. 리포트 시계열 연결 시 구→신 매핑 필수. 화성시 분구(41591~41597)도 동일 패턴.

## 태스크
G1 ✅ | G2 DDL ✅ (확정 대기, PG 설치 후 적용) | G3~G10 대기

## 다음 세션 작업 (우선순위 순)

### 최우선
  1. LAND_SALE 재수집 완료 확인
  2. ERROR_CODE_HANDLING.md 작성 (API 기술문서 정리 완료, 6개 소스 에러코드 통합)
  3. API 에러코드 에러 유도 테스트 (MOLIT/ECOS/REB/청약홈/MOLIT_STAT)

### 중순위
  4. DDL 및 문서 업데이트 (source CHECK 8종 반영, 청약홈 DDL, MOLIT_STAT DDL 등)
  5. 수집 완료 후 전체 데이터 검증 (리모트 SQLite Viewer 실데이터 확인)
     — NrgTrade cdealtype 소문자 t, AptRent 도로명 소문자, dealAmount 쉼표 등 확인
  6. UNSOLD 미분양 수집 (MOLIT_STAT API, form_id=2082/5328, 별도 키)

### 후순위
  7. 청약홈 API 테스트 호출 + 수집 스크립트
  8. MOIS 인구 CSV 2016~2022-08 (17시도 × 2회 = 34회 다운로드 + 파싱)
  9. KB 평단가 10년치 수집 스크립트
  10. PostgreSQL 설치 + DDL v0.2 적용 + 이관
  11. db-schema SKILL.md fact_indicator_month 스키마 실제 확인 및 수정

## 코드 컨벤션
- DB 접속: 단일 connect() 강제
- 타임스탬프: DB=UTC, 출력=KST
- 타입: fact_trade_raw VARCHAR 유지, Mart에서 CAST
- dedup COALESCE: NULL → '' (빈문자열) 통일, 숫자 0 치환 안 함
- 정본 = 코드. 문서 불일치 시 문서 수정.
- prefetch 실행: --region 기본값 seoul, 전국 수집 시 반드시 --region all 지정

---

**블록 2: CHANGELOG**

### #010 – 2026-02-28 (Session 10)

**429 오류 근본원인 분석**
- prefetch_trade_raw.py가 HTTP 429를 감지하지 못하고 row_count=0, status='OK'로 기록
- resume 로직이 해당 건을 "완료"로 판단하고 skip → 데이터 누락
- mark_done()이 무조건 OK 기록, fetch_and_store()에서 예외 시 continue만 하고 로그 미기록
- LAND_SALE 429 피해: row_count=0 1,049건 → PENDING 리셋 후 재수집 실행
- 11종은 429 피해 0건 확인 (finished_at 시간대 분석으로 판별 완료)

**API 에러코드 전수조사**
- 4개 소스 에러 체계 정리 완료
  - 소스 A/B: 국토교통부 실거래 12종 + MOIS 인구 (apis.data.go.kr) — XML resultCode + HTTP 상태코드
  - 소스 C: 청약홈 분양정보 (api.odcloud.kr) — HTTP 상태코드만 (200/401/429/500)
  - 소스 D: 한국은행 ECOS (ecos.bok.or.kr) — JSON RESULT.CODE 별도 체계
- 통합 처리 원칙 5개 확정
  - 원칙 1: 한도 초과 즉시 전체 중단 (MOLIT/MOIS 22·HTTP 429 / odcloud 429 / ECOS ERROR-602)
  - 원칙 2: 데이터 없음 = 정상 (MOLIT 03 / odcloud 200+currentCount=0 / ECOS INFO-200)
  - 원칙 3: 키/서비스 문제 = 전체 중단
  - 원칙 4: 일시 장애 = 재시도 최대 3회 (30→60→120초)
  - 원칙 5: row_count=0 + 정상코드일 때만 OK (429 사고 재발 방지 핵심)
- ERROR_CODE_HANDLING.md 미생성, API 전수조사 후 작성 예정

**청약홈 API 분석**
- 기술문서 분석 완료: 10개 엔드포인트 (분양정보 상세 5종 + 주택형별 상세 5종)
- 국가데이터포털 경유 odcloud 기반, 서비스키 신청 완료 (#15098547)
- 전국 건별 페이징 조회, 갱신주기 매일, 시군구별 반복 불필요
- 분양가 필드 포함 (LTTOT_TOP_AMOUNT, SUPLY_AMOUNT) — 별도 API 불필요
- 입주예정물량 CSV 임시 확보 (한국부동산원_주택공급정보_입주예정물량정보_20251231), DDL 추후 작성, API 자동수집 전환 예정
- 테스트 호출 미실행, 후순위

**LAND_SALE 수집**
- prefetch_trade_raw.py --region 기본값이 seoul — 전국 수집 시 --region all 필수 (1차 재수집 실패 원인)
- 전체 19,832 jobs 중 OK 1,432건 (41,263행), PENDING 653건, 미실행 ~17,747건
- 429 피해 1,049건 PENDING 리셋 완료
- 재수집 1차: 396건 처리 (10,937행), limit 도달로 종료
- 재수집 2차: --region all로 재실행, PID 2004687 가동 중
- 금일 재수집분 중 row_count=0 8건 (429 아닌 실제 빈 데이터)

**MOIS 인구 수집 검증 완료**
- 20,996건, 인구·세대 각 10,498건, 299개 시군구(SIGUNGU), 202209~202601
- 264/268 수집 성공, 빈 응답 4건은 화성시 분구 신설코드 (정상)
- region_key 299개 > dim_region 269개 = 강원/전북/화성 신·구 코드 공존

**수집 현황 (2026-02-28 기준)**
- 전체: 219,281 / 219,934 OK (99.7%), fact_trade_raw 14,139,806건
- 실거래 11종: 19,832건 전부 OK, 429 피해 없음
- LAND_SALE: 미완 (OK 1,486 / PENDING 599 / 미실행 ~17,747), PID 2004687 가동 중
- MOIS 인구/세대: 검증 완료

**Git**
- 커밋 91a410a: HANDOVER v004 - #010 세션 반영 (amend)
- ERROR_CODE_HANDLING.md 미생성

**다음: LAND_SALE 재수집 완료 확인 → API 전수조사·에러코드 테스트 → DDL·문서 업데이트 → 수집 데이터 검증 → UNSOLD·청약홈 수집 (후순위)**

### #011 – 2026-02-28 (Session 11)

**API 기술문서 전수조사 및 규정문서 작성**
- 6개 소스 기술문서 정리 완료, 3개 MD 파일 생성
  - MOLIT_TRADE_API_SPEC.md: 실거래 13종 (에러코드 공통 + 엔드포인트 + 응답 필드 전수)
  - ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md: ECOS 3종, REB R-ONE 3종, 청약홈 10종, 건축HUB 17종
  - MOLIT_STAT_API_SPEC.md: 미분양 2종 (form_id=2082, 5328)
- 건축HUB 17종은 현재 스코프 밖이나 향후 확장용으로 포함

**API 기술문서 이슈 통합 정리 (30건)**
- 코드 작업 즉시 영향 6건: NrgTrade cdealtype 소문자 t, AptRent 도로명 소문자, 기술문서 함수명 오기재 3건, 청약홈 날짜 형식·필드명 불일치, 금액 필드 쉼표
- 에러 처리 관련 10건: HTTP 429 미명시(MOLIT/청약홈), ECOS INFO-100 vs ERROR-100, 각 소스별 한도 초과·빈 응답 코드 매핑
- DDL/스키마 설계 영향 10건: 단지명·면적 필드명 차이, 청약홈 10종 통합 설계, REB/ECOS 통계표코드 미확인
- 프로토콜/인프라 4건: http/https 혼재

**4개 소스 에러코드 체계 비교 정리**
- MOLIT: XML resultCode + HTTP status
- ECOS: JSON RESULT.CODE (INFO-/ERROR- 접두어)
- REB: XML/JSON RESULT.CODE (INFO-/ERROR- 접두어)
- 청약홈: HTTP 상태코드만 (200/401/429/500)
- MOLIT_STAT: JSON status_code (INFO-/ERROR- 접두어)
- 통합 처리 원칙 5개 매핑 완료 (소스별)

**MOLIT_STAT (국토교통 통계누리) API 확인**
- stat.molit.go.kr 웹에서 API 명세 확인 (별도 PDF 없음)
- 요청 URL: http://stat.molit.go.kr/portal/openapi/service/rest/getList.do
- 파라미터: key, form_id, style_num, start_dt, end_dt
- UNSOLD_UNITS_SIGUNGU: form_id=2082 (200012~)
- UNSOLD_UNITS_COMPLETED: form_id=5328 (200701~)
- 에러코드 9종 확인 (INFO-000/100/200/300, ERROR-301/334/335/500/600)
- 한도 초과 에러코드 미명시 (안내문만 존재)
- MOLIT_STAT_API_KEY 별도 키 사용 (MOLIT 실거래 키와 다름)

**HF_PIR 드랍**
- HF(주택금융공사) PIR 지표 드랍 확정
- 확정 12종 → 실질 11종

**MOIS 기술문서 — 패스**
- 기술문서 PDF 없음, 공공데이터포털 Swagger UI 동적 로딩으로 크롤링 불가
- apis.data.go.kr 공통 에러코드 체계 적용 추정이나 팩트 미확인 → 규정문서 목적상 패스
- 수집은 완료 상태, 향후 기술문서 확보 시 정리

**Git**
- API 기술문서 3개 MD 파일 로컬 생성
- HANDOVER v004 작성

**다음: LAND_SALE 재수집 완료 확인 → ERROR_CODE_HANDLING.md 작성 → 에러 유도 테스트 → DDL 업데이트 → 데이터 검증 → UNSOLD·청약홈 수집**