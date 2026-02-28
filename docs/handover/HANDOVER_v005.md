
```markdown
# Landbrief Handover v005 (2026-02-28)

**블록 1: HANDOVER(기반 문서)**

> **⚠ 수정 규칙**: 수정사항 안내 시 반드시 **섹션 단위**로 전체 교체 블록을 마크다운 원문으로 제공할 것. 줄 단위 지시, 화살표(→) 표기, diff 형식 금지.

## 문서 체계
- INTENT.md (v0.4): 프로젝트 정의/원칙/범위/지표/3트랙 상세. 심화 작업 시 공유.
- HANDOVER: 현재 상태. 매 세션 공유.
- API 기술문서 정리: MOLIT_TRADE_API_SPEC.md (실거래 13종) + ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md (ECOS·REB·청약홈·건축HUB) + MOLIT_STAT_API_SPEC.md (미분양 2종). 수집 스크립트 개발·ERROR_CODE_HANDLING.md 작성 기반.
- ERROR_CODE_HANDLING.md (v1.2): 6개 소스 에러코드 통합 처리 규정. 에러 유도 테스트 실측 반영.
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

## 에러 유도 테스트 현황 (2026-02-28 기준)

| 소스 | 테스트 | 결과 | 비고 |
|---|---|---|---|
| MOLIT 실거래 | 5건 (4종 교차) | 기술문서 에러코드 미발생 | 000+totalCount=0 또는 평문 |
| ECOS | 5건 | 4건 일치, 1건 불일치 | ERROR-100 유도 시 INFO-200 |
| REB | 4건 | 전건 일치 | |
| 청약홈 | 4건 | 3건 일치, 1건 불일치 | 잘못된 키 시 400+code=-4 |
| MOLIT_STAT | 5건 | 3건 일치, 2건 불일치 | Spring 예외 문자열, 정상 호출 INFO-200 |

## 수집 현황 (2026-02-28 기준)

| 데이터 | 상태 | 비고 |
|---|---|---|
| 실거래 11종 | 완료 (각 19,832건 OK) | 429 피해 없음 확인 |
| 실거래 LAND_SALE | 미완 (OK 2,005 / PENDING 972 / 미실행 ~16,855) | 429 코드 수정 완료, 재수집 cron 미설정 |
| MOIS 인구/세대 | 완료 (20,996건, 299지역, 202209~202601) | 빈 응답 4건은 화성시 분구 신설코드 (정상) |
| ECOS 경제지표 | 완료 | 기준금리, CPI, CSI, ESI |
| UNSOLD 미분양 | 테스트 수준 | 11건, MOLIT_STAT_API_KEY 별도 키 |
| KB 지표 | 미착수 | 메뉴코드 미확인 |
| 청약홈 분양정보 | 미착수 | 서비스키 신청 완료, 테스트 호출 미실행 |

- fact_trade_raw: 14,139,806건 (전체 OK 219,281 / 219,934, 99.7%)
- LAND_SALE: 일일 한도 1,000건 (개발계정), 잔여 ~17,827건, 약 18일 소요
- 공공데이터포털 한도 리셋: 매일 자정(00:00) KST, API 서비스별 독립 한도
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
- "API token quota exceeded" 평문 미감지 (P1) — 한도 소진 시 비XML 평문 반환, 현재 None → mark_done(OK,0) 경로. Codex 수정 지시 발행, 결과 대기 중
- API 429 처리 완료, 평문 감지 미완 (P1) — HTTP 429 + resultCode 22 처리 완료. "API token quota exceeded"/"Unauthorized" 평문 감지 Codex 진행 중
- serviceKey 인코딩 이슈 (P2) — curl User-Agent 없으면 WAF 차단 확인. Python requests는 정상 동작. 모니터링용 curl 시 -A "Mozilla/5.0" 필수
- dim_region 자동적재 미구현 (P2)
- LAND_SALE 수집 미완 (P2) — OK 2,005 / 전체 19,832, 재수집 cron 미설정
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
  1. Codex 결과 확인 (평문 감지 Part A 경로 검증 + Part B 수정 + 테스트 5건)
  2. LAND_SALE 재수집 cron 설정 (자정 이후 자동 실행)

### 중순위
  3. DDL 및 문서 업데이트 (source CHECK 8종 반영, 청약홈 DDL, MOLIT_STAT DDL 등)
  4. 수집 완료 후 전체 데이터 검증 (리모트 SQLite Viewer 실데이터 확인)
     — NrgTrade cdealtype 소문자 t, AptRent 도로명 소문자, dealAmount 쉼표 등 확인
  5. UNSOLD 미분양 수집 (MOLIT_STAT API, form_id=2082/5328, 별도 키)

### 후순위
  6. 청약홈 API 테스트 호출 + 수집 스크립트
  7. MOIS 인구 CSV 2016~2022-08 (17시도 × 2회 = 34회 다운로드 + 파싱)
  8. KB 평단가 10년치 수집 스크립트
  9. PostgreSQL 설치 + DDL v0.2 적용 + 이관
  10. db-schema SKILL.md fact_indicator_month 스키마 실제 확인 및 수정

## 코드 컨벤션
- DB 접속: 단일 connect() 강제
- 타임스탬프: DB=UTC, 출력=KST
- 타입: fact_trade_raw VARCHAR 유지, Mart에서 CAST
- dedup COALESCE: NULL → '' (빈문자열) 통일, 숫자 0 치환 안 함
- 정본 = 코드. 문서 불일치 시 문서 수정.
- prefetch 실행: --region 기본값 seoul, 전국 수집 시 반드시 --region all 지정
- curl MOLIT API 테스트: 반드시 -A "Mozilla/5.0" 포함

---

**블록 2: CHANGELOG**

### #012 – 2026-02-28 (Session 12)

**429 코드 수정 완료**
- RateLimitError 예외 클래스 추가 (utils/api_helpers.py:23)
- extract_items()에서 resultCode 22 → RateLimitError raise
- call_data_go_kr_api()에서 HTTP 429 → RateLimitError raise
- run()에서 RateLimitError catch → 즉시 전체 중단 (break), PENDING 유지
- mark_error() 함수 추가 (일반 에러 시 status=ERROR, error_msg 기록)
- Codex 검증 5건 전 PASS, py_compile 통과
- 429 피해 건 427건 PENDING 리셋 완료
- LAND_SALE 현황: OK 2,005 / PENDING 972 / 미실행 ~16,855

**ERROR_CODE_HANDLING.md v1.2 작성**
- v1.0: 6개 소스 에러코드 매핑, 통합 처리 원칙 5개, 판정 순서 4단계
- v1.1: Codex 검증 FAIL 4건 + WARN 2건 반영 (§2.1 빈문자열 정책, §2.2 None 정책, §4.1 기존 collector 존재 반영)
- v1.2: 에러 유도 테스트 실측 결과 전면 반영 (§2.3 평문 응답 정책, §3.1 MOLIT 실측 기반 재편, §3.4 청약홈 자체 에러코드, §3.5 MOLIT_STAT Spring 예외, 부록 A 테스트 로그)

**에러 유도 테스트 26건 실시 (4종 교차 확인 포함)**
- MOLIT 실거래:
  - 기술문서 에러코드(03,10,11,30) 실제 미발생 확인 (4종: APT_SALE_DTL, APT_RENT, LAND_SALE, OFFI_SALE)
  - 데이터 없음/파라미터 오류 → resultCode=000 + totalCount=0
  - 인증 실패 → "Unauthorized" 평문 (XML 아님)
  - 한도 소진 → "API token quota exceeded" 평문 (신규 발견, LAND_SALE 실측)
  - curl User-Agent 없으면 WAF 차단 (HTTP 400 HTML "Request Blocked")
  - Python requests는 User-Agent 포함되어 정상 동작
- ECOS: 5건 중 4건 일치, ERROR-100 유도 시 INFO-200 반환
- REB: 4건 전건 일치
- 청약홈: 잘못된 키 시 HTTP 400 + code=-4 (기술문서는 401), 키 제거 시 HTTP 401 + code=-401
- MOLIT_STAT: ERROR-301 유도 시 Spring 예외 문자열, 정상 호출(202501) INFO-200 (데이터 미공개 추정), 응답 구조 result_status.status_code

**"API token quota exceeded" 평문 미감지 발견 (긴급)**
- 현재 코드: 비XML → None → 빈 리스트 → mark_done(OK, 0)
- 429 사고와 동일한 데이터 누락 구조
- Codex 지시서 발행: Part A 경로 검증 3건 + Part B 코드 수정 + 테스트 5건
- 수정 내용: call_data_go_kr_api()에 평문 내용 검사 추가 ("API token quota exceeded" → RateLimitError, "Unauthorized" → RateLimitError)
- "Unauthorized"는 ConfigError가 목표이나 미구현이므로 RateLimitError로 임시 처리

**API 한도 확인**
- 공공데이터포털 한도: API 서비스별 독립, 매일 자정(00:00) KST 리셋
- LAND_SALE 개발계정: 일 1,000건 (타 11종은 10,000건)
- 3/5 한도 축소 예정, 운영계정 전환 실익 없음

**Git**
- Codex 커밋: RateLimitError 추가 (api_helpers.py, prefetch_trade_raw.py)
- Codex 진행 중: 평문 감지 추가 (api_helpers.py)
- ERROR_CODE_HANDLING.md v1.2 로컬 생성

**다음: Codex 결과 확인 → LAND_SALE cron 설정 → DDL 업데이트 → 데이터 검증 → UNSOLD·청약홈 수집**
```