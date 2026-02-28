

ERROR_CODE_HANDLING.md v1.2 전문입니다. 전체 테스트 결과를 반영했습니다.

```markdown
# ERROR_CODE_HANDLING.md

> 버전: v1.2
> 작성일: 2026-02-28
> 기반 문서: MOLIT_TRADE_API_SPEC.md, ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md, MOLIT_STAT_API_SPEC.md
> 에러 유도 테스트: 2026-02-28 실시 (26건, 4종 API 교차 확인 포함)
> 목적: Landbrief 수집 스크립트 공통 에러 처리 규정

---

## 1. 통합 처리 원칙 (5개)

모든 수집 스크립트는 소스에 관계없이 아래 5개 원칙을 동일하게 적용한다.

### 원칙 1: 한도 초과 → 즉시 전체 중단

일일 호출 한도 초과가 감지되면 해당 소스의 수집을 즉시 전체 중단한다.
한도 초과 후 추가 호출은 전부 실패하므로 낭비이며, 정상 응답으로 오인 기록되면 데이터 누락으로 이어진다 (2026-02-28 LAND_SALE 429 사고 참조).
RateLimitError 예외를 raise하고, 호출측에서 catch하여 루프를 break한다.
해당 건은 mark_done()을 호출하지 않으며 PENDING 상태로 남긴다.

### 원칙 2: 데이터 없음 = 정상

해당 지역·기간에 거래 데이터가 없는 것은 에러가 아니다.
정상 빈 응답 코드를 확인한 뒤에만 status=OK, row_count=0으로 기록한다.

### 원칙 3: 키/서비스/파라미터 문제 → 전체 중단

인증키 무효, 서비스 폐기, 필수 파라미터 누락 등은 단건 재시도로 해결되지 않는다.
즉시 전체 중단하고 로그에 에러코드와 메시지를 기록한다.
ConfigError(또는 동등한 예외)를 raise한다.

### 원칙 4: 일시 장애 → 재시도 최대 3회

서버 오류, DB 오류, 타임아웃 등 일시적 장애는 지수 백오프로 재시도한다.
재시도 간격: 30초 → 60초 → 120초 (총 3회).
3회 실패 시 해당 건을 status=ERROR로 기록하고 다음 건으로 진행한다.

### 원칙 5: row_count=0은 정상코드일 때만 OK

이 원칙은 429 사고 재발 방지의 핵심이다.
row_count=0으로 OK를 기록하려면 반드시 원칙 2의 정상 빈 응답 판정을 통과해야 한다.
HTTP 에러, XML/JSON 에러코드, 예외 발생 시에는 row_count=0이더라도 절대 OK로 기록하지 않는다.

---

## 2. 판정 순서 (공통)

모든 소스에서 응답을 처리할 때 아래 순서를 따른다.

1단계: HTTP 상태코드 검사. 200이 아니면 HTTP 레벨 에러로 분기한다.
  - 429 → 원칙 1 (RateLimitError)
  - 401/403 → 원칙 3 (ConfigError)
  - 5xx → 원칙 4 (재시도)
  - 기타 4xx → 원칙 3

2단계: 응답 본문 유효성 검사. HTTP 200이더라도 본문이 비정상이면 에러로 분기한다.
  - 본문이 None (API 키 미설정, 네트워크 예외 등) → 원칙 3 또는 원칙 4 (원인에 따라)
  - 본문이 XML/JSON이 아님 (HTML 에러 페이지, 빈 응답 등) → 아래 §2.3 평문 응답 정책 참조
  - XML/JSON 파싱 실패 → 원칙 4 (재시도 1회 후 ERROR)
  - 이 단계에서 걸린 응답은 절대 OK로 기록하지 않는다 (원칙 5 적용).

3단계: 소스별 에러코드 검사. 응답 본문의 에러코드 체계에 따라 분기한다.
  - 정상 코드 (MOLIT 000, ECOS 정상, REB INFO-000 등) → 4단계로
  - 빈 응답 코드 (MOLIT 03, ECOS INFO-200, REB INFO-200 등) → 원칙 2 (OK, row_count=0)
  - 한도 초과 코드 → 원칙 1 (RateLimitError)
  - 키/서비스/파라미터 코드 → 원칙 3
  - 장애/타임아웃 코드 → 원칙 4
  - 빈 문자열("") 또는 미등록 코드 → ERROR로 기록, OK 금지 (§2.1 참조)

4단계: 정상 응답 판정. 데이터 존재 여부에 따라 OK+row_count 또는 OK+row_count=0을 기록한다.
  - row_count > 0 → OK
  - row_count = 0 + 3단계에서 빈 응답 코드 확인됨 → OK, row_count=0
  - row_count = 0 + 3단계에서 빈 응답 코드 미확인 → ERROR (원칙 5 위반 방지)

### 2.1 빈 문자열/미등록 에러코드 정책

resultCode가 빈 문자열("")이거나 §3 매핑 테이블에 없는 값일 경우, 정상으로 간주하지 않는다.
해당 건은 status=ERROR로 기록하고, error_msg에 실제 수신된 코드 값을 포함한다.
현재 코드(LandScanner)에서는 빈 문자열을 정상으로 허용하고 있으나, Landbrief ETL에서는 이 정책을 적용한다.

### 2.2 None/파싱실패 응답 정책

API 호출 함수가 None을 반환하는 경우는 다음과 같다.
  - API 키 미설정 → 원칙 3 (전체 중단)
  - 네트워크 예외 (ConnectionError, Timeout 등) → 원칙 4 (재시도)
  - HTTP 200이지만 본문이 XML/JSON이 아님 → §2.3 참조
  - XML/JSON 파싱 실패 → 원칙 4 (재시도 1회 후 ERROR)

None 반환 시 호출측에서 절대 mark_done(OK)을 호출하지 않는다.
현재 코드(LandScanner)에서는 None → 빈 리스트 → mark_done(OK, 0)으로 귀결되는 경로가 존재하며, 이는 Landbrief ETL 신규 개발 시 수정 대상이다.

### 2.3 평문 응답 정책 (에러 유도 테스트 실측 기반)

API가 XML/JSON이 아닌 평문 문자열을 반환하는 경우가 실측으로 확인되었다.
이 경우 평문 내용으로 에러 유형을 판별한다.

| 평문 내용 | 원칙 | 동작 |
|---|---|---|
| "Unauthorized" | 원칙 3 | ConfigError → 전체 중단 |
| "API token quota exceeded" | 원칙 1 | RateLimitError → 전체 중단 |
| 기타 평문 / HTML | 원칙 4 | 재시도 1회 후 ERROR |

이 평문 응답들은 API 서버가 아닌 게이트웨이(WAF/프록시)에서 반환된다.
HTTP 상태코드가 200이 아닐 수도 있고, 200이면서 평문일 수도 있으므로 본문 내용 검사가 필수이다.

---

## 3. 소스별 에러코드 매핑

### 3.1 MOLIT 실거래 13종 + MOIS 인구 (apis.data.go.kr)

에러코드 전달: HTTP 상태코드 + XML body의 resultCode.
MOIS 인구 API는 동일 게이트웨이(apis.data.go.kr)를 사용하므로 동일 체계를 적용한다 (기술문서 미확보, 추정 기반).

#### 기술문서 에러코드 vs 실측 결과

2026-02-28 에러 유도 테스트 (APT_SALE_DTL, APT_RENT, LAND_SALE, OFFI_SALE 4종 교차 확인) 결과, 기술문서에 정의된 XML resultCode 에러(03, 10, 11, 22, 30 등)는 현재 API에서 **직접 발생하지 않는다**. 게이트웨이가 API 서버 도달 전에 처리하거나, API 서버가 에러 대신 000+totalCount=0을 반환한다.

#### 실측 기반 응답 매핑 (정본)

| 응답 형태 | 설명 | 원칙 | 동작 |
|---|---|---|---|
| XML resultCode=000 + totalCount > 0 | 정상 데이터 | — | OK, row_count=N |
| XML resultCode=000 + totalCount=0 | 정상 빈 응답 | 원칙 2 | OK, row_count=0 |
| HTTP 429 + "Too Many Requests" | 한도 초과 (rate limit) | 원칙 1 | RateLimitError → 전체 중단 |
| 평문 "API token quota exceeded" | 한도 초과 (quota) | 원칙 1 | RateLimitError → 전체 중단 |
| 평문 "Unauthorized" | 인증 실패 | 원칙 3 | ConfigError → 전체 중단 |
| HTML "Request Blocked" | WAF 차단 (User-Agent 등) | 원칙 4 | 재시도 1회 후 ERROR |
| XML resultCode != 000 | 기술문서상 에러 (실측 미발생) | 아래 참조 | 아래 참조 |

#### 기술문서 에러코드 (방어적 유지)

실측에서 발생하지 않았으나, API 변경 시 발생할 수 있으므로 방어 코드로 유지한다.

| resultCode | 설명 | 원칙 | 동작 |
|---|---|---|---|
| 03 | No Data | 원칙 2 | OK, row_count=0 |
| 22 | 일일 한도 초과 | 원칙 1 | RateLimitError → 전체 중단 |
| 01, 02, 04, 05 | 제공기관 장애/타임아웃 | 원칙 4 | 재시도 3회 (30→60→120초) |
| 10, 11, 12, 20, 30, 31, 32 | 키/서비스/파라미터 문제 | 원칙 3 | 전체 중단 |
| "" (빈 문자열) | 코드 없음 | §2.1 | ERROR 기록, OK 금지 |
| 기타 미등록 값 | unknown | §2.1 | ERROR 기록, OK 금지 |

#### 현재 코드(LandScanner) 동작과의 차이

현재 extract_items()는 resultCode 03을 에러 로그 후 빈 리스트로 반환한다. 문서상 원칙 2(정상 빈 응답)와 동작이 불일치한다. 실제 데이터 누락 위험은 없으나(row_count=0으로 OK 기록됨), 불필요한 에러 로그가 발생한다.
현재 extract_items()는 resultCode 빈 문자열("")을 정상으로 허용한다. §2.1 정책과 불일치하며, Landbrief ETL에서 수정 대상이다.
resultCode별 세분화 분기(01~05 재시도, 10~32 중단)는 현재 미구현이다. 모든 비정상 코드를 에러 로그 후 빈 리스트로 처리한다.
"API token quota exceeded" 평문 감지는 현재 미구현이다. 이 응답을 받으면 비XML로 판정되어 None → mark_done(OK, 0)으로 귀결된다. Landbrief ETL 및 LandScanner 수정 대상이다.

#### 13종 엔드포인트 상세

개별 API URL, 응답 필드, 필드명 차이(단지명, 면적, camelCase 등)는 MOLIT_TRADE_API_SPEC.md를 참조한다.

#### curl 테스트 시 주의사항

curl로 MOLIT API를 호출할 때 User-Agent 헤더가 없으면 WAF가 HTTP 400 + HTML "Request Blocked"로 차단한다. `-A "Mozilla/5.0"` 옵션을 반드시 추가할 것. Python requests는 기본 User-Agent가 포함되므로 이 문제가 발생하지 않는다.

### 3.2 ECOS 3종 (ecos.bok.or.kr)

에러코드 전달: JSON 응답의 RESULT.CODE (INFO-xxx / ERROR-xxx 접두어).
주의: INFO-100(인증키 무효)과 ERROR-100(필수값 누락)은 숫자가 같지만 접두어가 다르다. 접두어 포함 비교 필수.

#### 실측 확인 결과

| RESULT.CODE | 유도 방법 | 실측 결과 |
|---|---|---|
| INFO-200 | 존재하지 않는 통계표코드 | **일치** |
| INFO-100 | 잘못된 인증키 | **일치** |
| ERROR-200 | 요청유형(json/xml) 누락 | **일치** |
| ERROR-101 | 월 주기에 년도 형식 날짜 | **일치** |
| ERROR-301 | 종료건수 빈값 | **일치** |
| ERROR-100 | 빈 경로 파라미터 | **불일치** — INFO-200 반환 |

ERROR-100(필수값 누락)은 빈 경로 파라미터로는 유도되지 않고 INFO-200이 반환되었다. ECOS가 빈 파라미터를 "데이터 없음"으로 처리하는 것으로 보인다. ERROR-100이 발생하는 실제 조건은 미확인이며, 방어 코드로 유지한다.

#### 에러코드 매핑

| RESULT.CODE | 설명 | 원칙 | 동작 |
|---|---|---|---|
| (정상 응답, 에러 키 없음) | 정상 데이터 | — | OK, row_count=N |
| INFO-200 | 데이터 없음 | 원칙 2 | OK, row_count=0 |
| ERROR-602 | 과도한 호출 이용 제한 | 원칙 1 | RateLimitError → 전체 중단 |
| ERROR-400, 500, 600, 601 | 타임아웃/서버/DB 오류 | 원칙 4 | 재시도 3회 (30→60→120초) |
| INFO-100 | 인증키 무효 | 원칙 3 | 전체 중단 |
| ERROR-100, 101, 200, 300, 301 | 파라미터/형식 오류 | 원칙 3 | 전체 중단 |

현재 구현 상태: LandScanner에 collectors/api_ecos.py가 존재하나, 이 문서의 원칙 1~5 및 예외 클래스 체계와 일치하지 않는다. Landbrief ETL 신규 개발 시 적용.

### 3.3 REB R-ONE 3종 (reb.or.kr)

에러코드 전달: XML/JSON 응답의 RESULT.CODE (INFO-xxx / ERROR-xxx 접두어).

#### 실측 확인 결과

| RESULT.CODE | 유도 방법 | 실측 결과 |
|---|---|---|
| INFO-200 | 존재하지 않는 통계표ID | **일치** |
| ERROR-290 | 잘못된 인증키 | **일치** |
| ERROR-300 | STATBL_ID 누락 | **일치** |
| ERROR-333 | pIndex에 문자열 입력 | **일치** |

REB는 기술문서와 실측이 완전히 일치한다.

#### 에러코드 매핑

| RESULT.CODE | 설명 | 원칙 | 동작 |
|---|---|---|---|
| INFO-000 | 정상 | — | OK, row_count=N |
| INFO-200 | 데이터 없음 | 원칙 2 | OK, row_count=0 |
| ERROR-337 | 일별 트래픽 제한 초과 | 원칙 1 | RateLimitError → 전체 중단 |
| ERROR-500, 600, 601 | 서버/DB 오류 | 원칙 4 | 재시도 3회 (30→60→120초) |
| INFO-300 | 관리자 인증키 사용 제한 | 원칙 3 | 전체 중단 |
| ERROR-290, 300, 310, 333, 336 | 인증키/파라미터/서비스 오류 | 원칙 3 | 전체 중단 |

현재 구현 상태: LandScanner에 collectors/api_reb.py, clients/rone_client.py가 존재하나, 이 문서의 원칙 1~5 및 예외 클래스 체계와 일치하지 않는다. Landbrief ETL 신규 개발 시 적용.

### 3.4 청약홈 10종 (api.odcloud.kr)

에러코드 전달: HTTP 상태코드 + JSON body의 자체 에러코드 체계.
기술문서에는 HTTP 상태코드(200/401/500)만 명시되어 있으나, 실측 결과 JSON body에 자체 code/msg 필드가 포함된다.

#### 실측 확인 결과

| 유도 방법 | HTTP 상태 | JSON body | 기술문서 | 판정 |
|---|---|---|---|---|
| 정상 호출 | 200 | currentCount > 0 | 200 | **일치** |
| page=99999 | 200 | currentCount=0, data=[] | 200+빈 응답 | **일치** |
| 잘못된 키 | **400** | {"code":-4, "msg":"등록되지 않은 인증키"} | 401 | **불일치** |
| 키 제거 | 401 | {"code":-401, "msg":"인증키는 필수 항목"} | 401 | **일치** (code 추가) |

#### 에러코드 매핑 (실측 기반)

| 응답 형태 | 설명 | 원칙 | 동작 |
|---|---|---|---|
| HTTP 200 + currentCount > 0 | 정상 데이터 | — | OK, row_count=N |
| HTTP 200 + currentCount = 0 | 정상 빈 응답 | 원칙 2 | OK, row_count=0 |
| HTTP 400 + code=-4 | 잘못된 인증키 | 원칙 3 | ConfigError → 전체 중단 |
| HTTP 401 + code=-401 | 인증키 누락 | 원칙 3 | ConfigError → 전체 중단 |
| HTTP 429 | 한도 초과 (기술문서 미명시, 발생 가능) | 원칙 1 | RateLimitError → 전체 중단 |
| HTTP 500 | 서버 오류 | 원칙 4 | 재시도 3회 (30→60→120초) |

현재 구현 상태: 미구현. 서비스키 #15098547 발급 완료 (odcloud 경유). 청약홈 전용 collector 및 config 키 변수(APPLYHOME_API_KEY 등)는 미생성. Landbrief ETL 신규 개발 시 생성 예정.

### 3.5 MOLIT_STAT 2종 (stat.molit.go.kr)

에러코드 전달: JSON 응답의 result_status.status_code (INFO-xxx / ERROR-xxx 접두어).
주의: 기술문서는 응답 키를 status_code로 기재하지만, 실측 결과 result_status 객체 하위의 status_code이다.

#### 실측 확인 결과

| status_code | 유도 방법 | 실측 결과 |
|---|---|---|
| INFO-200 | 미래 기간 (205001) | **일치** |
| INFO-200 | 정상 호출 (202501) | **주의** — 정상 기간에도 INFO-200. 데이터 미공개 가능성 |
| INFO-100 | 잘못된 인증키 | **일치** |
| ERROR-334 | 날짜 역전 (시작>종료) | **일치** |
| ERROR-301 | form_id 누락 | **불일치** — Spring 예외 문자열이 status_code에 그대로 삽입 |

ERROR-301은 파라미터 누락 시 발생하지 않고, Java/Spring의 예외 메시지가 status_code 필드에 직접 들어온다 (예: "Required request parameter 'form_id' for method parameter type Integer is not present"). 에러코드 파싱 시 INFO-/ERROR- 접두어가 없는 문자열도 에러로 처리해야 한다.

#### 에러코드 매핑 (실측 반영)

| status_code | 설명 | 원칙 | 동작 |
|---|---|---|---|
| INFO-000 | 정상 | — | OK, row_count=N |
| INFO-200 | 데이터 없음 | 원칙 2 | OK, row_count=0 |
| ERROR-500, 600 | 서버/DB 오류 | 원칙 4 | 재시도 3회 (30→60→120초) |
| INFO-100 | 인증키 무효 | 원칙 3 | 전체 중단 |
| INFO-300 | 서비스 개방 취소 | 원칙 3 | 전체 중단 |
| ERROR-301, 334, 335 | 파라미터/날짜/건수 오류 | 원칙 3 | 전체 중단 |
| Spring 예외 문자열 (INFO-/ERROR- 접두어 없음) | 서버 내부 오류 | 원칙 3 | 전체 중단, error_msg에 원문 기록 |
| (한도 초과) | 미명시 | 원칙 1 | 실테스트 후 확정 |

#### 응답 구조 주의사항

기술문서는 status_code로 기재하지만, 실제 JSON 구조는 다음과 같다.

```json
{
  "result_status": {
    "status_code": "INFO-200",
    "message": "해당하는 데이터가 없습니다."
  }
}
```

파싱 시 result_status.status_code 경로로 접근해야 한다.

현재 구현 상태: LandScanner에 collectors/api_molit.py가 존재하나, 이 문서의 원칙 1~5 및 예외 클래스 체계와 일치하지 않는다. Landbrief ETL 신규 개발 시 적용.

---

## 4. 예외 클래스 체계

### 4.1 현재 구현 (LandScanner)

| 예외 클래스 | 적용 원칙 | 동작 | 위치 |
|---|---|---|---|
| RateLimitError | 원칙 1 | 전체 중단, PENDING 유지 | utils/api_helpers.py |

LandScanner의 기존 collector(api_ecos.py, api_reb.py, api_molit.py, clients/rone_client.py)는 각자 독립적인 에러 처리를 구현하고 있으며, 이 문서의 원칙 1~5 및 예외 클래스 체계와 일치하지 않는다. LandScanner collector의 에러 처리 통합은 이 문서의 범위 밖이며, Landbrief ETL 신규 개발 시 처음부터 반영한다.

#### 즉시 수정 필요 (LandScanner)

"API token quota exceeded" 평문 응답이 현재 코드에서 감지되지 않는다. 이 응답은 비XML로 판정되어 None → 빈 리스트 → mark_done(OK, 0)으로 귀결되며, 429 사고와 동일한 데이터 누락을 유발한다. call_data_go_kr_api()에서 평문 내용 검사를 추가해야 한다.

### 4.2 Landbrief ETL 목표 (신규 개발 시 적용)

| 예외 클래스 | 적용 원칙 | 동작 |
|---|---|---|
| RateLimitError | 원칙 1 | 전체 중단, PENDING 유지 |
| ConfigError | 원칙 3 | 전체 중단, 로그 기록 |
| RetryableError | 원칙 4 | 재시도 3회 후 ERROR 기록 |

구현 우선순위: RateLimitError(완료) → "API token quota exceeded" 감지 추가(긴급) → RetryableError → ConfigError.

---

## 5. etl_trade_raw_log status 값 정의

| status | 의미 | 설정 조건 |
|---|---|---|
| OK | 정상 완료 | 정상 응답(§2 4단계) + row_count >= 0 (원칙 2, 5 충족 시에만) |
| PENDING | 미완료/대기 | 초기 상태, 또는 RateLimitError 발생 시 (mark_done 미호출) |
| ERROR | 에러 | 원칙 4 재시도 실패, 예상치 못한 예외, None/파싱실패(§2.2), unknown 코드(§2.1) |
| EMPTY | 빈 응답 | 현재 미사용. OK + row_count=0으로 대체 |

OK 기록 금지 경로 (원칙 5 강화):
  - HTTP 에러 응답 (4xx, 5xx)
  - XML/JSON 에러코드 (원칙 1, 3, 4 해당 코드)
  - API 호출 함수가 None 반환 (§2.2)
  - resultCode 빈 문자열 또는 미등록 값 (§2.1)
  - 평문 응답 ("Unauthorized", "API token quota exceeded", HTML 등) (§2.3)
  - 파싱 실패, 비정상 본문
  - 예외 발생 (RateLimitError 포함)

---

## 6. 429 사고 재발 방지 체크리스트

수집 스크립트 신규 개발 또는 수정 시 아래 항목을 반드시 확인한다.

6.1: HTTP 상태코드를 응답 본문 파싱보다 먼저 검사하는가?
6.2: HTTP 429 수신 시 RateLimitError를 raise하는가?
6.3: 소스별 한도 초과 에러코드(MOLIT 22, ECOS ERROR-602, REB ERROR-337) 수신 시 RateLimitError를 raise하는가?
6.4: RateLimitError 발생 시 mark_done()을 호출하지 않는가? (PENDING 유지)
6.5: RateLimitError catch 후 즉시 루프를 break하는가?
6.6: row_count=0을 OK로 기록하기 전에 정상 빈 응답 코드를 확인하는가?
6.7: API 호출 함수가 None을 반환했을 때 mark_done(OK)을 호출하지 않는가?
6.8: resultCode가 빈 문자열이거나 미등록 값일 때 OK로 기록하지 않는가?
6.9: HTTP 200이지만 본문이 XML/JSON이 아닐 때 OK로 기록하지 않는가?
6.10: "API token quota exceeded" 평문을 RateLimitError로 감지하는가?
6.11: "Unauthorized" 평문을 ConfigError(또는 전체 중단)로 감지하는가?

---

## 7. 소스 문서 참조

| 소스 | 기술문서 | 에러코드 위치 |
|---|---|---|
| MOLIT 실거래 | MOLIT_TRADE_API_SPEC.md §1.5 | XML resultCode (실측: 대부분 HTTP/평문 레벨) |
| ECOS | ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md §1.5 (ECOS) | JSON RESULT.CODE |
| REB R-ONE | ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md §1.4 (REB) | XML/JSON RESULT.CODE |
| 청약홈 | ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md §1.4 (청약홈) | HTTP 상태코드 + JSON code/msg |
| MOLIT_STAT | MOLIT_STAT_API_SPEC.md §1.6 | JSON result_status.status_code |
| MOIS | 기술문서 미확보 | MOLIT 체계 추정 |
| 건축HUB | ECOS_REB_APPLYHOME_ARCHHUB_API_SPEC.md §1.5 (건축HUB) | MOLIT 체계 추정 |

---

## 부록 A. 에러 유도 테스트 로그 (2026-02-28)

### 테스트 환경

서버: Ubuntu 24.04, ~/real_estate_report
도구: curl (User-Agent 필수), python3
키: .env 파일 로딩

### MOLIT 실거래 (4종 교차 확인: APT_SALE_DTL, APT_RENT, LAND_SALE, OFFI_SALE)

존재하지 않는 지역(99999) + 미래 월: 4종 모두 XML resultCode=000, totalCount=0. resultCode 03 미발생.
필수파라미터(LAWD_CD) 누락: APT_SALE_DTL, APT_RENT, OFFI_SALE → 000+totalCount=0. LAND_SALE → "API token quota exceeded" (한도 소진 상태).
잘못된 키: 4종 모두 "Unauthorized" 평문.
DEAL_YMD 형식 오류(5자리): 000+totalCount=0.
User-Agent 미포함 curl: HTTP 400 + HTML "Request Blocked".

### ECOS

INFO-200(존재하지 않는 통계표코드): 일치.
INFO-100(잘못된 키): 일치.
ERROR-200(요청유형 누락): 일치.
ERROR-101(날짜 형식 오류): 일치.
ERROR-301(조회건수 타입 오류): 일치.
ERROR-100(빈 경로 파라미터): INFO-200 반환 (불일치).

### REB

INFO-200(존재하지 않는 통계표ID): 일치.
ERROR-290(잘못된 키): 일치.
ERROR-300(STATBL_ID 누락): 일치.
ERROR-333(pIndex 문자열): 일치.

### 청약홈

HTTP 200 정상: 일치.
HTTP 200 + currentCount=0 (page=99999): 일치.
잘못된 키: HTTP 400 + code=-4 (기술문서는 401).
키 제거: HTTP 401 + code=-401.

### MOLIT_STAT

INFO-200(미래 기간): 일치.
INFO-200(정상 기간 202501): INFO-200 반환 (데이터 미공개 추정).
INFO-100(잘못된 키): 일치.
ERROR-334(날짜 역전): 일치.
ERROR-301(form_id 누락): Spring 예외 문자열 (불일치).
```

---

v1.2 전문입니다. 주요 변경점은 다음과 같습니다.

§2.3 신규 추가: 평문 응답 정책 ("Unauthorized", "API token quota exceeded", HTML)
§3.1 전면 개편: 기술문서 에러코드 vs 실측 결과 분리, 실측 기반 매핑을 정본으로
§3.4 수정: 청약홈 자체 에러코드 체계 (code=-4, code=-401) 추가
§3.5 수정: MOLIT_STAT 응답 구조(result_status.status_code), Spring 예외 문자열
§4.1 긴급 추가: "API token quota exceeded" 감지 미구현 경고
§6 추가: 체크리스트 6.10, 6.11
부록 A 신규: 전체 테스트 로그
