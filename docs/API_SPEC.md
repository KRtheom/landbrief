---

```markdown
# ECOS (한국은행) API 기술문서 정리

> 원본: ECOS API개발명세서 PDF 3종
> 정리일: 2026-02-28
> 목적: Landbrief 수집 스크립트 개발 및 ERROR_CODE_HANDLING.md 작성 기반

---

## 1. 공통 사항

### 1.1 게이트웨이

모든 API는 `ecos.bok.or.kr/api/` 하위에 위치한다.
운영 주체는 한국은행이며, 인증키는 한국은행 ECOS 사이트에서 발급받는다.

### 1.2 인터페이스 공통

| 항목 | 값 |
|---|---|
| 프로토콜 | REST (GET) |
| 응답 포맷 | XML, JSON 모두 지원 |
| 인증 | URL 경로에 인증키 삽입 (sample 위치) |
| 암호화 | https |

### 1.3 URL 패턴

ECOS는 일반적인 쿼리파라미터 방식이 아니라 **경로(path) 기반**으로 파라미터를 전달한다.

```
https://ecos.bok.or.kr/api/{서비스명}/{인증키}/{요청유형}/{언어}/{시작건수}/{종료건수}/{이하 서비스별 파라미터}
```

### 1.4 공통 경로 파라미터

| 순서 | 파라미터 | 필수 | 설명 |
|---|---|---|---|
| 1 | 서비스명 | Y | StatisticTableList / StatisticMeta / StatisticSearch |
| 2 | 인증키 | Y | 한국은행 발급 키 (sample = 테스트) |
| 3 | 요청유형 | Y | xml / json |
| 4 | 언어구분 | Y | kr(국문) / en(영문) |
| 5 | 요청시작건수 | Y | 정수 (1부터) |
| 6 | 요청종료건수 | Y | 정수 |

### 1.5 에러코드 (3종 전 API 동일)

ECOS 에러코드는 JSON 응답의 `RESULT.CODE` 또는 XML의 `<RESULT><CODE>` 로 전달된다.
코드 체계는 타입(정보/에러) + 숫자코드 형태이다.

| 타입 | 코드 | 설명 | 처리 분류 |
|---|---|---|---|
| 정보 | 100 | 인증키 유효하지 않음 (키 미발급 시 신청 안내) | ABORT (원칙 3) |
| 정보 | 200 | 해당하는 데이터가 없음 | OK — 정상 빈 응답 (원칙 2) |
| 에러 | 100 | 필수 값 누락 | ABORT (원칙 3) |
| 에러 | 101 | 주기와 다른 형식의 날짜 | ABORT (원칙 3) |
| 에러 | 200 | 파일타입 값 누락 또는 유효하지 않음 | ABORT (원칙 3) |
| 에러 | 300 | 조회건수 값 누락 | ABORT (원칙 3) |
| 에러 | 301 | 조회건수 값 타입 오류 (정수 아님) | ABORT (원칙 3) |
| 에러 | 400 | 검색범위 초과 60초 TIMEOUT | RETRY (원칙 4) |
| 에러 | 500 | 서버 오류 | RETRY (원칙 4) |
| 에러 | 600 | DB Connection 오류 | RETRY (원칙 4) |
| 에러 | 601 | SQL 오류 | RETRY (원칙 4) |
| 에러 | 602 | 과도한 호출로 이용 제한 | ABORT — 전체 중단 (원칙 1) |

#### 주의사항

ECOS의 정보코드 100과 에러코드 100은 숫자가 같지만 타입이 다르다. JSON 응답 시 `RESULT.CODE`에 `"INFO-100"` 또는 `"ERROR-100"` 형태로 구분된다. 파싱 시 타입 접두어를 반드시 포함해서 비교해야 한다.

#### 통합 처리 원칙 매핑

| 원칙 | 적용 코드 | 동작 |
|---|---|---|
| 원칙 1: 한도 초과 즉시 전체 중단 | ERROR-602 | 수집 전체 STOP |
| 원칙 2: 데이터 없음 = 정상 | INFO-200 | status=OK, row_count=0 |
| 원칙 3: 키/서비스 문제 = 전체 중단 | INFO-100, ERROR-100,101,200,300,301 | 수집 전체 STOP |
| 원칙 4: 일시 장애 = 재시도 최대 3회 | ERROR-400,500,600,601 | 30→60→120초 백오프 |
| 원칙 5: row_count=0은 정상코드일 때만 OK | INFO-200일 때만 | 429 사고 재발 방지 |

---

## 2. API 엔드포인트 상세

### 2.1 서비스 통계 목록 — StatisticTableList

통계표 목록을 조회한다. 특정 통계표코드의 메타정보(통계명, 주기, 출처 등)를 확인하는 데 사용한다.

#### 추가 경로 파라미터

| 순서 | 파라미터 | 필수 | 설명 |
|---|---|---|---|
| 7 | 통계표코드 | N | 예: 102Y004 |

#### 응답 필드

| 필드명 | 국문 | 크기 | 설명 |
|---|---|---|---|
| P_STAT_CODE | 상위통계표코드 | 8 | |
| STAT_CODE | 통계표코드 | 8 | |
| STAT_NAME | 통계명 | 200 | |
| CYCLE | 주기 | 2 | 년/분기/월 등 |
| SRCH_YN | 검색가능여부 | 1 | |
| ORG_NAME | 출처 | 50 | |

#### 테스트 URL

```
https://ecos.bok.or.kr/api/StatisticTableList/{인증키}/xml/kr/1/10/102Y004
```

### 2.2 통계메타DB — StatisticMeta

특정 통계의 메타데이터(작성연도, 방법론 등)를 조회한다.

#### 추가 경로 파라미터

| 순서 | 파라미터 | 필수 | 설명 |
|---|---|---|---|
| 7 | 데이터명 | Y | 예: 경제심리지수 (한글 URL 인코딩 필요) |

#### 응답 필드

| 필드명 | 국문 | 크기 | 설명 |
|---|---|---|---|
| LVL | 레벨 | 2 | 계층 구조 레벨 |
| P_CONT_CODE | 상위통계항목코드 | 8 | |
| CONT_CODE | 통계항목코드 | 8 | |
| CONT_NAME | 통계항목명 | 200 | |
| META_DATA | 메타데이터 | 200 | |

#### 테스트 URL

```
https://ecos.bok.or.kr/api/StatisticMeta/{인증키}/xml/kr/1/10/경제심리지수
```

### 2.3 통계 조회 조건 — StatisticSearch

실제 통계 데이터를 조회하는 핵심 API이다. Landbrief 수집 스크립트에서 주로 사용하는 엔드포인트이다.

#### 추가 경로 파라미터

| 순서 | 파라미터 | 필수 | 설명 |
|---|---|---|---|
| 7 | 통계표코드 | Y | 예: 200Y001 |
| 8 | 주기 | Y | A(년), S(반년), Q(분기), M(월), SM(반월), D(일) |
| 9 | 검색시작일자 | Y | 주기에 따라 형식 상이 (2015, 2015Q1, 201501, 20150101 등) |
| 10 | 검색종료일자 | Y | 위와 동일 |
| 11 | 통계항목코드1 | N | ?로 전체 조회 |
| 12 | 통계항목코드2 | N | ?로 전체 조회 |
| 13 | 통계항목코드3 | N | ?로 전체 조회 |
| 14 | 통계항목코드4 | N | ?로 전체 조회 |

#### 응답 필드

| 필드명 | 국문 | 크기 | 설명 |
|---|---|---|---|
| STAT_CODE | 통계표코드 | 8 | |
| STAT_NAME | 통계명 | 200 | |
| ITEM_CODE1 | 통계항목코드1 | 20 | |
| ITEM_NAME1 | 통계항목명1 | 200 | |
| ITEM_CODE2 | 통계항목코드2 | 20 | |
| ITEM_NAME2 | 통계항목명2 | 200 | |
| ITEM_CODE3 | 통계항목코드3 | 20 | |
| ITEM_NAME3 | 통계항목명3 | 200 | |
| ITEM_CODE4 | 통계항목코드4 | 20 | |
| ITEM_NAME4 | 통계항목명4 | 200 | |
| UNIT_NAME | 단위 | 200 | |
| WGT | 가중치 | 22 | |
| TIME | 시점 | 8 | |
| DATA_VALUE | 값 | 23 | |

#### 테스트 URL

```
https://ecos.bok.or.kr/api/StatisticSearch/{인증키}/xml/kr/1/10/200Y001/A/2015/2021/10101/?/?/?
```

---

## 3. Landbrief 수집 대상 통계표코드

현재 ECOS에서 수집 완료된 지표 (HANDOVER 기준):

| 지표 | 통계표코드 | 주기 | 비고 |
|---|---|---|---|
| 기준금리 (MACRO_BASE_RATE) | 확인 필요 | M/D | |
| CPI (소비자물가지수) | 확인 필요 | M | |
| CSI (소비자심리지수) | 확인 필요 | M | |
| ESI (경제심리지수) | 확인 필요 | M | |

통계표코드는 수집 스크립트 코드에서 확인 필요. 기술문서에서는 통계표코드 목록을 제공하지 않으며, StatisticTableList API로 조회하거나 ECOS 웹사이트에서 검색해야 한다.

---

# REB (한국부동산원 R-ONE) API 기술문서 정리

> 원본: 부동산통계 Open API 활용가이드 PDF, 서비스 통계목록 명세서, 통계 세부항목 목록 명세서
> 정리일: 2026-02-28
> 목적: Landbrief 수집 스크립트 개발 및 ERROR_CODE_HANDLING.md 작성 기반

---

## 1. 공통 사항

### 1.1 게이트웨이

모든 API는 `www.reb.or.kr/r-one/openapi/` 하위에 위치한다.
운영 주체는 한국부동산원이며, R-ONE 사이트에서 인증키를 발급받는다.
서비스 오픈일은 2024-08-27이다.

### 1.2 인터페이스 공통

| 항목 | 값 |
|---|---|
| 프로토콜 | REST (GET) |
| 응답 포맷 | XML, JSON 모두 지원 |
| 인증 | KEY 파라미터 (쿼리스트링) |
| 암호화 | 없음 (SSL 미적용, 기술문서 기준) |
| 요청제한횟수 | 제한없음 (단, 일별 트래픽 제한 존재 — 에러 337) |
| 페이지당 최대 건수 | 1,000건 |

### 1.3 기본인자 (전 API 공통)

| 파라미터 | 필수 | 설명 |
|---|---|---|
| KEY | Y | 인증키 (기본값: sample key) |
| Type | Y | 호출 문서 형식 (xml / json, 기본값: xml) |
| pIndex | Y | 페이지 위치 (기본값: 1, sample key는 1 고정) |
| pSize | Y | 페이지당 요청 숫자 (기본값: 100, sample key는 5 고정) |

### 1.4 에러코드 (3종 전 API 동일)

REB 에러코드는 XML의 `<RESULT><CODE>` 또는 JSON의 `RESULT.CODE`로 전달된다.
코드 체계는 구분(INFO/ERROR) + 숫자코드 형태이다.

| 구분 | 코드 | 설명 | 처리 분류 |
|---|---|---|---|
| INFO | 000 | 정상 처리 | OK |
| INFO | 200 | 해당하는 데이터가 없음 | OK — 정상 빈 응답 (원칙 2) |
| INFO | 300 | 관리자에 의해 인증키 사용 제한 | ABORT (원칙 3) |
| ERROR | 290 | 인증키 유효하지 않음 | ABORT (원칙 3) |
| ERROR | 300 | 필수 값 누락 | ABORT (원칙 3) |
| ERROR | 310 | 해당 서비스를 찾을 수 없음 | ABORT (원칙 3) |
| ERROR | 333 | 요청위치 값 타입 오류 (정수 아님) | ABORT (원칙 3) |
| ERROR | 336 | 데이터 요청 한번에 최대 1,000건 초과 | ABORT (원칙 3) |
| ERROR | 337 | 일별 트래픽 제한 초과 | ABORT — 전체 중단 (원칙 1) |
| ERROR | 500 | 서버 오류 | RETRY (원칙 4) |
| ERROR | 600 | DB Connection 오류 | RETRY (원칙 4) |
| ERROR | 601 | SQL 오류 | RETRY (원칙 4) |

#### 통합 처리 원칙 매핑

| 원칙 | 적용 코드 | 동작 |
|---|---|---|
| 원칙 1: 한도 초과 즉시 전체 중단 | ERROR-337 | 수집 전체 STOP |
| 원칙 2: 데이터 없음 = 정상 | INFO-200 | status=OK, row_count=0 |
| 원칙 3: 키/서비스 문제 = 전체 중단 | INFO-300, ERROR-290,300,310,333,336 | 수집 전체 STOP |
| 원칙 4: 일시 장애 = 재시도 최대 3회 | ERROR-500,600,601 | 30→60→120초 백오프 |
| 원칙 5: row_count=0은 정상코드일 때만 OK | INFO-200일 때만 | 429 사고 재발 방지 |

---

## 2. API 엔드포인트 상세

### 2.1 서비스 통계목록 — SttsApiTbl

OpenAPI 대상 통계목록을 조회한다. 통계표ID, 통계표명, 주기, 제공기관 등 메타정보를 확인한다.

#### URL

```
https://www.reb.or.kr/r-one/openapi/SttsApiTbl.do?KEY={인증키}&STATBL_ID={통계표ID}
```

#### 요청인자

| 파라미터 | 필수 | 크기 | 설명 |
|---|---|---|---|
| STATBL_ID | N | 50 | 통계표 ID (예: A_2024_00900) |

#### 응답 필드

| 필드명 | 국문 | 크기 | 설명 |
|---|---|---|---|
| STATBL_ID | 통계표 ID | 50 | |
| STATBL_NM | 통계표명 | 300 | |
| DTACYCLE_CD | 주기코드 | 11 | YY/HY/QY/MM/WK |
| DTACYCLE_NM | 주기명 | 15 | 매년/반기/분기/매월/매주 |
| STAT_ID | 통계메타 ID | 50 | |
| TOP_ORG_NM | 제공기관 | 500 | |
| OPEN_STATE | 공개여부 | 1 | Y/N |
| DATA_START_YY | 통계자료 시작년도 | 4 | |
| DATA_END_YY | 통계자료 종료년도 | 4 | |
| STATBL_IDTFR | 통계표주석 식별자 | 10 | |
| STATBL_CMMT | 통계표 주석 | 4000 | |
| V_ORDER | 출력순서 | 10 | |
| RPSTUI_NM | 기준시점 | 300 | 예: 기준시점 : 2023.12.=100.0 |

### 2.2 통계 세부항목 목록 — SttsApiTblItm

특정 통계표의 세부 항목(그룹/분류/항목)을 조회한다. 지역코드나 항목코드를 확인하는 데 사용한다.

#### URL

```
https://www.reb.or.kr/r-one/openapi/SttsApiTblItm.do?KEY={인증키}&STATBL_ID={통계표ID}&ITM_TAG={항목정보}
```

#### 요청인자

| 파라미터 | 필수 | 크기 | 설명 |
|---|---|---|---|
| STATBL_ID | Y | 50 | 통계표 ID |
| ITM_TAG | N | 5 | 항목정보 (그룹 / 분류 / 항목) |

#### 응답 필드

| 필드명 | 국문 | 크기 | 설명 |
|---|---|---|---|
| STATBL_ID | 통계표 ID | 50 | |
| ITM_TAG | 항목정보 | 5 | 그룹/분류/항목 |
| ITM_ID | 항목 ID | 8 | |
| PAR_ITM_ID | 상위항목 ID | 8 | |
| ITM_NM | 항목명 | 100 | |
| ITM_FULLNM | 항목전체명 | 500 | |
| UI_NM | 단위명 | 100 | |
| ITM_CMMT_IDTFR | 항목 주석 식별자 | 10 | |
| ITM_CMMT_CONT | 항목 주석 | 2000 | |
| V_ORDER | 출력순서 | 8 | |

### 2.3 통계 조회 조건 설정 — SttsApiTblData

실제 통계 데이터를 조회하는 핵심 API이다. Landbrief 수집 스크립트에서 주로 사용하는 엔드포인트이다.

#### URL

```
https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do?KEY={인증키}&STATBL_ID={통계표ID}&DTACYCLE_CD={주기코드}&CLS_ID={분류ID}&START_WRTTIME={시작}&END_WRTTIME={종료}
```

#### 요청인자

| 파라미터 | 필수 | 크기 | 설명 |
|---|---|---|---|
| STATBL_ID | Y | 50 | 통계표 ID |
| DTACYCLE_CD | Y | 50 | 주기코드 (YY/HY/QY/MM/WK) |
| WRTTIME_IDTFR_ID | N | 8 | 자료작성 시점 (= 조건) |
| GRP_ID | N | 8 | 그룹 ID |
| CLS_ID | N | 8 | 분류 ID (지역 등) |
| ITM_ID | N | 8 | 항목 ID |
| START_WRTTIME | N | 8 | 자료작성 시점 시작일 |
| END_WRTTIME | N | 8 | 자료작성 시점 종료일 |

#### 자료작성 시점 형식 (주기코드별)

| 주기코드 | 예시 | 설명 |
|---|---|---|
| YY (년) | 2022, 2023 | |
| HY (반기) | 202301, 202302 | 상반기/하반기 |
| QY (분기) | 202301~202304 | 1분기~4분기 |
| MM (월) | 202301~202312 | 1월~12월 |
| WK (주) | 202301~202353 | 1주~53주 |

#### 응답 필드

| 필드명 | 국문 | 크기 | 설명 |
|---|---|---|---|
| STATBL_ID | 통계표 ID | 50 | |
| DTACYCLE_CD | 주기코드 | 50 | |
| WRTTIME_IDTFR_ID | 자료작성 시점 | 8 | |
| GRP_ID | 그룹 ID | 8 | |
| GRP_NM | 그룹명 | 300 | |
| CLS_ID | 분류 ID | 8 | |
| CLS_NM | 분류명 | 300 | |
| ITM_ID | 항목 ID | 8 | |
| ITM_NM | 항목명 | 300 | |
| DTA_VAL | 통계 자료값 | 22 | |
| UI_NM | 단위명 | 100 | |
| GRP_FULLNM | 그룹전체명 | 1000 | |
| CLS_FULLNM | 분류전체명 | 1000 | 예: 서울>종로구 |
| ITM_FULLNM | 항목전체명 | 1000 | |
| WRTTIME_DESC | 자료시점설명 | 100 | 예: 2022 년 |

---

## 3. Landbrief 수집 대상 통계표 (확정 12종 중 REB 해당분)

| 지표 | 통계표ID | 주기 | 비고 |
|---|---|---|---|
| REB_SALE_PRICE_INDEX (매매가격지수) | 확인 필요 | MM/WK | |
| REB_TRADE_VOLUME (거래량) | 확인 필요 | MM | |
| REB_RENT_PRICE_INDEX (전세가격지수) | 확인 필요 | MM/WK | |

통계표ID는 R-ONE 통계코드 검색 페이지 또는 SttsApiTbl API로 확인 필요.
https://www.reb.or.kr/r-one/portal/openapi/openApiGuideCdPage.do

---

## 4. 기술문서 주의사항

| # | 항목 | 내용 |
|---|---|---|
| 1 | SSL 미적용 | 기술문서에 SSL 없음으로 표기. 실제로 https 접속 가능 여부 테스트 필요 |
| 2 | sample key 제한 | pIndex=1 고정, pSize=5 고정. 테스트 시 실데이터 확인 불가 |
| 3 | 페이지당 최대 1,000건 | ERROR-336. 페이징 필수 |
| 4 | 일별 트래픽 제한 | ERROR-337. 구체적 건수 미공개 |
| 5 | 구 API 전환 | 2024-08-27 서비스 오픈. 이전 R-ONE API와 체계가 다를 수 있음 |

---

# 청약홈 분양정보 조회 서비스 API 기술문서 정리

> 원본: 청약홈 분양정보 조회 서비스 Open API 활용가이드 (2026-01-29)
> 정리일: 2026-02-28
> 목적: Landbrief 수집 스크립트 개발 및 ERROR_CODE_HANDLING.md 작성 기반

---

## 1. 공통 사항

### 1.1 게이트웨이

모든 API는 `api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/` 하위에 위치한다.
서비스키는 국가데이터포털(data.go.kr)에서 발급받으며, odcloud 경유로 호출한다.
운영 주체는 한국부동산원 ICT센터이며, 데이터 갱신주기는 매일이다.
서비스키 번호: #15098547 (HANDOVER 기준)

### 1.2 인터페이스 공통

| 항목 | 값 |
|---|---|
| 프로토콜 | REST (GET) |
| 응답 포맷 | XML, JSON 모두 지원 |
| 인증 | serviceKey (쿼리파라미터) |
| 암호화 | 없음 (SSL 미적용, 기술문서 기준) |
| 페이징 | page, perPage 파라미터 |
| 필터 조건 | cond[필드명::연산자]=값 (URL 인코딩 필수) |

### 1.3 필터 연산자

| 연산자 | 의미 | URL 인코딩 형태 |
|---|---|---|
| EQ | Equal (=) | %3A%3AEQ |
| LIKE | 포함 | %3A%3ALIKE |
| LT | Less Than (<) | %3A%3ALT |
| LTE | Less Than or Equal (<=) | %3A%3ALTE |
| GT | Greater Than (>) | %3A%3AGT |
| GTE | Greater Than or Equal (>=) | %3A%3AGTE |

### 1.4 에러코드

청약홈 API는 MOLIT/ECOS/REB와 달리 **HTTP 상태코드만** 사용한다. 별도의 XML/JSON 에러코드 체계가 없다.

| HTTP 상태코드 | 설명 | 처리 분류 |
|---|---|---|
| 200 | 성공 | OK |
| 401 | 인증 정보 부정확 | ABORT (원칙 3) |
| 429 | (기술문서 미명시, 실제 발생 가능) | ABORT — 전체 중단 (원칙 1) |
| 500 | API 서버 오류 | RETRY (원칙 4) |

#### 정상 빈 응답 판정 (원칙 2)

HTTP 200 + `currentCount=0` 일 때 데이터 없음으로 판정한다. 별도 에러코드 없음.

#### 통합 처리 원칙 매핑

| 원칙 | 적용 코드 | 동작 |
|---|---|---|
| 원칙 1: 한도 초과 즉시 전체 중단 | HTTP 429 | 수집 전체 STOP |
| 원칙 2: 데이터 없음 = 정상 | HTTP 200 + currentCount=0 | status=OK, row_count=0 |
| 원칙 3: 키/서비스 문제 = 전체 중단 | HTTP 401 | 수집 전체 STOP |
| 원칙 4: 일시 장애 = 재시도 최대 3회 | HTTP 500 | 30→60→120초 백오프 |
| 원칙 5: row_count=0은 정상코드일 때만 OK | HTTP 200일 때만 | 429 사고 재발 방지 |

---

## 2. API 엔드포인트 총괄 (10종)

| # | 엔드포인트 함수 | 국문 | 유형 |
|---|---|---|---|
| 1 | getAPTLttotPblancDetail | APT 분양정보 상세조회 | 분양정보 상세 |
| 2 | getUrbtyOfctlLttotPblancDetail | 오피스텔/도시형/민간임대/생활숙박시설 분양정보 상세조회 | 분양정보 상세 |
| 3 | getRemndrLttotPblancDetail | APT 잔여세대 분양정보 상세조회 | 분양정보 상세 |
| 4 | getPblPvtRentLttotPblancDetail | 공공지원 민간임대 분양정보 상세조회 | 분양정보 상세 |
| 5 | getOPTLttotPblancDetail | 임의공급 분양정보 상세조회 | 분양정보 상세 |
| 6 | getAPTLttotPblancMdl | APT 분양정보 주택형별 상세조회 | 주택형별 상세 |
| 7 | getUrbtyOfctlLttotPblancMdl | 오피스텔/도시형/민간임대/생활숙박시설 주택형별 상세조회 | 주택형별 상세 |
| 8 | getRemndrLttotPblancMdl | APT 잔여세대 주택형별 상세조회 | 주택형별 상세 |
| 9 | getPblPvtRentLttotPblancMdl | 공공지원 민간임대 주택형별 상세조회 | 주택형별 상세 |
| 10 | getOPTLttotPblancMdl | 임의공급 주택형별 상세조회 | 주택형별 상세 |

### 2.1 URL 패턴

```
https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/{엔드포인트함수}?page=1&perPage=10&serviceKey={키}
```

필터 조건 추가 시:
```
&cond[HOUSE_MANAGE_NO::EQ]=2022000248&cond[RCRIT_PBLANC_DE::GTE]=2022-01-01
```

---

## 3. 분양정보 상세 API 응답 필드 (5종)

### 3.1 APT 분양정보 상세 — getAPTLttotPblancDetail

가장 필드가 많은 API이다. 다른 상세 API는 이 API의 부분집합이다.

#### 주요 응답 필드

| 필드명 | 국문 | 크기 | 필수 | 비고 |
|---|---|---|---|---|
| HOUSE_MANAGE_NO | 주택관리번호 | 40 | 1 | PK |
| PBLANC_NO | 공고번호 | 40 | 1 | PK |
| HOUSE_NM | 주택명 | 200 | 0 | |
| HOUSE_SECD | 주택구분코드 | 2 | 0 | 01=APT, 09=민간사전청약, 10=신혼희망타운 |
| HOUSE_SECD_NM | 주택구분코드명 | 4000 | 0 | |
| HOUSE_DTL_SECD | 주택상세구분코드 | 2 | 0 | 01=민영, 03=국민 |
| HOUSE_DTL_SECD_NM | 주택상세구분코드명 | 4000 | 0 | |
| RENT_SECD | 분양구분코드 | 1 | 0 | 0=분양주택, 1=분양전환가능임대 |
| SUBSCRPT_AREA_CODE | 공급지역코드 | 3 | 0 | 코드표 참조 |
| SUBSCRPT_AREA_CODE_NM | 공급지역명 | 500 | 0 | |
| HSSPLY_ZIP | 공급위치 우편번호 | 6 | 0 | |
| HSSPLY_ADRES | 공급위치 | 256 | 0 | |
| TOT_SUPLY_HSHLDCO | 공급규모 | 10 | 0 | 세대수 |
| RCRIT_PBLANC_DE | 모집공고일 | 10 | 0 | YYYY-MM-DD |
| RCEPT_BGNDE | 청약접수시작일 | 10 | 0 | |
| RCEPT_ENDDE | 청약접수종료일 | 10 | 0 | |
| SPSPLY_RCEPT_BGNDE | 특별공급접수시작일 | 10 | 0 | |
| SPSPLY_RCEPT_ENDDE | 특별공급접수종료일 | 10 | 0 | |
| GNRL_RNK1_CRSPAREA_RCPTDE | 1순위 해당지역 접수시작일 | 21 | 0 | |
| GNRL_RNK1_CRSPAREA_ENDDE | 1순위 해당지역 접수종료일 | 21 | 0 | |
| GNRL_RNK1_ETC_GG_RCPTDE | 1순위 경기지역 접수시작일 | 21 | 0 | |
| GNRL_RNK1_ETC_GG_ENDDE | 1순위 경기지역 접수종료일 | 21 | 0 | |
| GNRL_RNK1_ETC_AREA_RCPTDE | 1순위 기타지역 접수시작일 | 21 | 0 | |
| GNRL_RNK1_ETC_AREA_ENDDE | 1순위 기타지역 접수종료일 | 21 | 0 | |
| GNRL_RNK2_CRSPAREA_RCPTDE | 2순위 해당지역 접수시작일 | 21 | 0 | |
| GNRL_RNK2_CRSPAREA_ENDDE | 2순위 해당지역 접수종료일 | 21 | 0 | |
| GNRL_RNK2_ETC_GG_RCPTDE | 2순위 경기지역 접수시작일 | 21 | 0 | |
| GNRL_RNK2_ETC_GG_ENDDE | 2순위 경기지역 접수종료일 | 21 | 0 | |
| GNRL_RNK2_ETC_AREA_RCPTDE | 2순위 기타지역 접수시작일 | 21 | 0 | |
| GNRL_RNK2_ETC_AREA_ENDDE | 2순위 기타지역 접수종료일 | 21 | 0 | |
| PRZWNER_PRESNATN_DE | 당첨자발표일 | 10 | 0 | |
| CNTRCT_CNCLS_BGNDE | 계약시작일 | 10 | 0 | |
| CNTRCT_CNCLS_ENDDE | 계약종료일 | 10 | 0 | |
| HMPG_ADRES | 홈페이지주소 | 256 | 0 | |
| CNSTRCT_ENTRPS_NM | 건설업체명(시공사) | 200 | 0 | |
| MDHS_TELNO | 문의처 | 30 | 0 | |
| BSNS_MBY_NM | 사업주체명(시행사) | 200 | 0 | |
| MVN_PREARNGE_YM | 입주예정월 | 6 | 0 | YYYYMM |
| SPECLT_RDN_EARTH_AT | 투기과열지구 | 1 | 0 | Y/N |
| MDAT_TRGET_AREA_SECD | 조정대상지역 | 1 | 0 | Y/N |
| PARCPRC_ULS_AT | 분양가상한제 | 1 | 0 | Y/N |
| IMPRMN_BSNS_AT | 정비사업 | 1 | 0 | Y/N |
| PUBLIC_HOUSE_EARTH_AT | 공공주택지구 | 1 | 0 | Y/N |
| LRSCL_BLDLND_AT | 대규모 택지개발지구 | 1 | 0 | Y/N |
| NPLN_PRVOPR_PUBLIC_HOUSE_AT | 수도권 내 민영 공공주택지구 | 1 | 0 | Y/N |
| PUBLIC_HOUSE_SPCLM_APPLC_APT | 공공주택 특별법 적용 여부 | 1 | 0 | Y/N |
| PBLANC_URL | 모집공고 상세 URL | 300 | 0 | |
| NSPRC_NM | 신문사 | 200 | 0 | |

### 3.2 오피스텔/도시형/민간임대/생활숙박시설 — getUrbtyOfctlLttotPblancDetail

APT 상세 대비 주요 차이점: 1순위/2순위 해당지역·경기·기타 필드 없음. 대신 SUBSCRPT_RCEPT_BGNDE/ENDDE로 단순화. SEARCH_HOUSE_SECD 필드 추가 (0201=도시형, 0202=오피스텔, 0203=민간임대, 0204=생활형숙박시설). CNSTRCT_ENTRPS_NM(시공사) 필드 없음.

### 3.3 APT 잔여세대 — getRemndrLttotPblancDetail

APT 상세 대비 주요 차이점: 1순위/2순위 세분화 필드 없음. GNRL_RCEPT_BGNDE/ENDDE(일반공급), SPSPLY_RCEPT_BGNDE/ENDDE(특별공급)으로 단순화. 투기과열지구·조정대상지역 등 규제 관련 필드 없음.

### 3.4 공공지원 민간임대 — getPblPvtRentLttotPblancDetail

APT 상세 대비 주요 차이점: HOUSE_DETAIL_SECD 필드명 사용 (APT는 HOUSE_DTL_SECD). 날짜 형식이 YYYYMMDD (APT는 YYYY-MM-DD). 1순위/2순위 세분화 없음.

### 3.5 임의공급 — getOPTLttotPblancDetail

APT 상세 대비 주요 차이점: 날짜 형식이 YYYYMMDD. GNRL_RCEPT_BGNDE/ENDDE(일반공급) 필드 존재. 규제 관련 필드 없음. 모집공고일(RCRIT_PBLANC_DE) 크기가 8 (다른 API는 10).

---

## 4. 주택형별 상세 API 응답 필드 (5종)

### 4.1 APT 주택형별 — getAPTLttotPblancMdl

| 필드명 | 국문 | 크기 | 필수 | 비고 |
|---|---|---|---|---|
| HOUSE_MANAGE_NO | 주택관리번호 | 40 | 1 | PK |
| PBLANC_NO | 공고번호 | 40 | 1 | PK |
| MODEL_NO | 모델번호 | 2 | 0 | |
| HOUSE_TY | 주택형 | 17 | 0 | 예: 058.8500A |
| SUPLY_AR | 공급면적 | 17 | 0 | |
| SUPLY_HSHLDCO | 일반공급세대수 | 10 | 0 | |
| SPSPLY_HSHLDCO | 특별공급세대수 | 10 | 0 | |
| MNYCH_HSHLDCO | 특별공급-다자녀가구 세대수 | 10 | 0 | |
| NWWDS_HSHLDCO | 특별공급-신혼부부 세대수 | 10 | 0 | |
| LFE_FRST_HSHLDCO | 특별공급-생애최초 세대수 | 10 | 0 | |
| OLD_PARNTS_SUPORT_HSHLDCO | 특별공급-노부모부양 세대수 | 10 | 0 | |
| INSTT_RECOMEND_HSHLDCO | 특별공급-기관추천 세대수 | 10 | 0 | |
| ETC_HSHLDCO | 특별공급-기타 세대수 | 10 | 0 | |
| TRANSR_INSTT_ENFSN_HSHLDCO | 특별공급-이전기관 세대수 | 10 | 0 | |
| YGMN_HSHLDCO | 특별공급-청년 세대수 | 10 | 0 | 공공주택만 해당 |
| NWBB_HSHLDCO | 특별공급-신생아 세대수 | 10 | 0 | 공공주택만 해당 |
| LTTOT_TOP_AMOUNT | 공급금액(분양최고금액) | 20 | 0 | 단위: 만원 |

### 4.2 오피스텔/도시형/민간임대 주택형별 — getUrbtyOfctlLttotPblancMdl

| 필드명 | 국문 | 크기 | 필수 | 비고 |
|---|---|---|---|---|
| HOUSE_MANAGE_NO | 주택관리번호 | 40 | 1 | PK |
| PBLANC_NO | 공고번호 | 40 | 1 | PK |
| MODEL_NO | 모델번호 | 4 | 0 | |
| GP | 군 | 30 | 0 | |
| TP | 타입 | 10 | 0 | |
| EXCLUSE_AR | 전용면적 | 17 | 0 | |
| SUPLY_HSHLDCO | 공급세대수 | 10 | 1 | |
| SUPLY_AMOUNT | 공급금액(분양최고금액) | 20 | 0 | 단위: 만원, 쉼표 포함 |
| SUBSCRPT_REQST_AMOUNT | 청약신청금 | 20 | 0 | 단위: 만원 |

### 4.3 APT 잔여세대 주택형별 — getRemndrLttotPblancMdl

| 필드명 | 국문 | 크기 | 필수 | 비고 |
|---|---|---|---|---|
| HOUSE_MANAGE_NO | 주택관리번호 | 40 | 0 | |
| PBLANC_NO | 공고번호 | 40 | 0 | |
| MODEL_NO | 모델번호 | 2 | 0 | |
| HOUSE_TY | 모델타입 | 17 | 0 | |
| SUPLY_AR | 공급면적 | 17 | 0 | |
| SUPLY_HSHLDCO | 일반공급세대수 | 10 | 0 | |
| SPSPLY_HSHLDCO | 특별공급세대수 | 10 | 0 | |
| LTTOT_TOP_AMOUNT | 공급금액(분양최고금액) | 20 | 0 | 단위: 만원, 쉼표 포함 |

### 4.4 공공지원 민간임대 주택형별 — getPblPvtRentLttotPblancMdl

| 필드명 | 국문 | 크기 | 필수 | 비고 |
|---|---|---|---|---|
| HOUSE_MANAGE_NO | 주택관리번호 | 40 | 0 | |
| PBLANC_NO | 공고번호 | 40 | 0 | |
| MODEL_NO | 모델번호 | 4 | 0 | |
| GP | 군 | 30 | 0 | |
| TP | 타입 | 10 | 0 | |
| EXCLUSE_AR | 전용면적 | 17 | 0 | |
| SUPPLY_AR | 공급면적 | 17 | 0 | ※ SUPLY_AR 아님, SUPPLY_AR (Y 추가) |
| CNTRCT_AR | 계약면적 | 17 | 0 | ※ 이 API만 존재 |
| SUPLY_HSHLDCO | 공급세대수 | 10 | 0 | |
| GNSPLY_HSHLDCO | 일반공급 세대수 | 10 | 0 | |
| SPSPLY_YGMN_HSHLDCO | 특별공급 청년 세대수 | 10 | 0 | |
| SPSPLY_NEW_MRRG_HSHLDCO | 특별공급 신혼 세대수 | 10 | 0 | |
| SPSPLY_AGED_HSHLDCO | 특별공급 고령자 세대수 | 10 | 0 | |
| SUPLY_AMOUNT | 공급금액(분양최고금액) | 20 | 0 | 단위: 만원 |
| SUBSCRPT_REQST_AMOUNT | 청약신청금 | 20 | 0 | 단위: 만원 |

### 4.5 임의공급 주택형별 — getOPTLttotPblancMdl

| 필드명 | 국문 | 크기 | 필수 | 비고 |
|---|---|---|---|---|
| HOUSE_MANAGE_NO | 주택관리번호 | 40 | 0 | |
| PBLANC_NO | 공고번호 | 40 | 0 | |
| MODEL_NO | 모델번호 | 2 | 0 | |
| HOUSE_TY | 주택형 | 17 | 0 | |
| SUPLY_HSHLDCO | 일반공급세대수 | 10 | 0 | |
| LTTOT_TOP_AMOUNT | 공급금액(분양최고금액) | 20 | 0 | 단위: 만원, 쉼표 포함 |

---

## 5. 코드 명세

### 5.1 공급지역 코드 (SUBSCRPT_AREA_CODE)

| 코드 | 지역 |
|---|---|
| 100 | 서울 |
| 200 | 강원 |
| 300 | 대전 |
| 312 | 충남 |
| 338 | 세종 |
| 360 | 충북 |
| 400 | 인천 |
| 410 | 경기 |
| 500 | 광주 |
| 513 | 전남 |
| 560 | 전북 |
| 600 | 부산 |
| 621 | 경남 |
| 680 | 울산 |
| 690 | 제주 |
| 700 | 대구 |
| 712 | 경북 |

전국 또는 광역권(서울+경기+인천 등)인 경우 지역코드 값이 존재하지 않는다.

### 5.2 주택구분 코드

| 코드 | 구분 | 적용 API |
|---|---|---|
| 01 | APT | APT 상세 |
| 09 | 민간사전청약 | APT 상세 |
| 10 | 신혼희망타운 | APT 상세 |
| 02 | 도시형/오피스텔/민간임대 | 오피스텔 상세 |
| 03 | 공공지원민간임대 | 공공지원 상세 |
| 04 | 무순위 | 잔여세대 상세 |
| 06 | 불법행위 재공급 | 잔여세대 상세 |
| 11 | 임의공급 | 임의공급 상세 |

### 5.3 주택상세구분 코드 (오피스텔 등)

| 코드 | 구분 |
|---|---|
| 0201 | 도시형생활주택 |
| 0202 | 오피스텔 |
| 0203 | 민간임대 |
| 0204 | 생활형숙박시설 |

---

## 6. 기술문서 주의사항

| # | 항목 | 내용 |
|---|---|---|
| 1 | 날짜 형식 불일치 | APT 상세는 YYYY-MM-DD, 공공지원/임의공급은 YYYYMMDD. 파싱 시 API별 분기 필요 |
| 2 | 필드명 불일치 | APT: HOUSE_DTL_SECD / 공공지원: HOUSE_DETAIL_SECD. 공급면적: SUPLY_AR / 공공지원: SUPPLY_AR |
| 3 | 금액 필드 쉼표 | LTTOT_TOP_AMOUNT, SUPLY_AMOUNT 등에 쉼표 포함 문자열 (예: "80,720"). 숫자 변환 시 쉼표 제거 필요 |
| 4 | 전국 조회 | 시군구별 반복 불필요. 전국 건별 페이징 조회 (HANDOVER 기존 분석과 일치) |
| 5 | PK 구조 | HOUSE_MANAGE_NO + PBLANC_NO 조합이 사실상 PK |
| 6 | HTTP 429 미명시 | 기술문서에 429 관련 기술 없음 (200/401/500만 명시). 실제 odcloud 플랫폼에서 429 발생 가능 |
| 7 | totalCount 의미 | 응답의 totalCount는 해당 API 전체 건수 (필터 무관). matchCount가 필터 적용 후 건수 |

---

# 건축HUB 건축인허가정보 서비스 API 기술문서 정리

> 원본: 건축HUB 건축인허가 1.0 OpenAPI 활용가이드 (2024.10), 기존 건축데이터 PK전환 규칙 안내
> 정리일: 2026-02-28
> 목적: Landbrief 향후 확장 시 참고용

---

## 1. 공통 사항

### 1.1 게이트웨이

모든 API는 `apis.data.go.kr/1613000/ArchPmsHubService/` 하위에 위치한다.
기관코드 1613000(국토교통부) 하위이며, MOLIT 실거래가 API와 동일한 게이트웨이를 사용한다.
서비스키는 공공데이터포털(data.go.kr)에서 발급받는다.

### 1.2 인터페이스 공통

| 항목 | 값 |
|---|---|
| 프로토콜 | REST (GET, POST, PUT, DELETE) |
| 응답 포맷 | XML, JSON 모두 지원 |
| 인증 | serviceKey (쿼리파라미터) |
| 평균 응답 시간 | 500 ms |
| 초당 최대 트랜잭션 | 30 tps |
| 1회 최대 목록 수 | 100건 (numOfRows 최대 100) |

### 1.3 공통 요청 파라미터

| 파라미터 | 필수 | 설명 |
|---|---|---|
| sigunguCd | Y | 시군구코드 (행정표준코드) |
| bjdongCd | Y | 법정동코드 (행정표준코드) |
| platGbCd | N | 대지구분코드 (0:대지, 1:산, 2:블록) |
| bun | N | 번 |
| ji | N | 지 |
| startDate | N | 검색시작일 (YYYYMMDD) |
| endDate | N | 검색종료일 (YYYYMMDD) |
| numOfRows | N | 페이지당 목록 수 (최대 100) |
| pageNo | N | 페이지 번호 |

### 1.4 응답 구조

MOLIT 실거래가 API와 동일한 구조이다.

```xml
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE.</resultMsg>
  </header>
  <body>
    <items><item>...</item></items>
    <numOfRows>2</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>20</totalCount>
  </body>
</response>
```

정상 응답 시 resultCode="00", resultMsg="NORMAL SERVICE."이다.

### 1.5 에러코드

기술문서에 별도 에러코드 목록이 명시되어 있지 않다. MOLIT 실거래가와 동일한 게이트웨이(apis.data.go.kr)를 사용하므로 동일한 에러코드 체계(resultCode 01~32, HTTP 429 등)가 적용될 것으로 추정한다. 실제 테스트로 확인 필요.

---

## 2. API 엔드포인트 총괄 (17종)

| # | 오퍼레이션 함수 | 국문 |
|---|---|---|
| 1 | getApBasisOulnInfo | 건축인허가 기본개요 조회 |
| 2 | getApDongOulnInfo | 건축인허가 동별개요 조회 |
| 3 | getApFlrOulnInfo | 건축인허가 층별개요 조회 |
| 4 | getApHoOulnInfo | 건축인허가 호별개요 조회 |
| 5 | getApImprprInfo | 건축인허가 대수선 조회 |
| 6 | getApHdcrMgmRgstInfo | 건축인허가 공작물관리대장 조회 |
| 7 | getApDemolExtngMgmRgstInfo | 건축인허가 철거멸실관리대장 조회 |
| 8 | getApTmpBldInfo | 건축인허가 가설건축물 조회 |
| 9 | getApWclfInfo | 건축인허가 오수정화시설 조회 |
| 10 | getApPklotInfo | 건축인허가 주차장 조회 |
| 11 | getApAtchPklotInfo | 건축인허가 부설주차장 조회 |
| 12 | getApExposPubuseAreaInfo | 건축인허가 전유공용면적 조회 |
| 13 | getApHoExposPubuseAreaInfo | 건축인허가 호별전유공용면적 조회 |
| 14 | getApJijiguInfo | 건축인허가 지역지구구역 조회 |
| 15 | getApRoadRgstInfo | 건축인허가 도로명대장 조회 |
| 16 | getApPlatPlcInfo | 건축인허가 대지위치 조회 |
| 17 | getApHsTpInfo | 건축인허가 주택유형 조회 |

### 2.1 URL 패턴

```
http://apis.data.go.kr/1613000/ArchPmsHubService/{오퍼레이션함수}?sigunguCd={시군구코드}&bjdongCd={법정동코드}&serviceKey={키}
```

---

## 3. 주요 오퍼레이션 응답 필드 (Landbrief 확장 시 유용한 3종)

### 3.1 기본개요 — getApBasisOulnInfo

건축인허가의 핵심 정보. 대지면적, 건축면적, 건폐율, 연면적, 용적율, 세대수, 호수, 주용도, 건축허가일, 사용승인일 등을 포함한다.

| 주요 필드명 | 국문 | 비고 |
|---|---|---|
| mgmPmsrgstPk | 관리허가대장PK | PK |
| platPlc | 대지위치 | |
| platArea | 대지면적(㎡) | |
| archArea | 건축면적(㎡) | |
| bcRat | 건폐율(%) | |
| totArea | 연면적(㎡) | |
| vlRat | 용적률(%) | |
| mainBldCnt | 주건축물수 | |
| mainPurpsCd | 주용도코드 | |
| mainPurpsCdNm | 주용도코드명 | |
| hhldCnt | 세대수(세대) | |
| hoCnt | 호수(호) | |
| totPkngCnt | 총주차수 | |
| archPmsDay | 건축허가일 | YYYYMMDD |
| useAprDay | 사용승인일 | YYYYMMDD |
| archGbCd | 건축구분코드 | |
| archGbCdNm | 건축구분코드명 | 신축/증축/용도변경 등 |

### 3.2 동별개요 — getApDongOulnInfo

건축물의 동별 정보. 주용도, 구조, 지붕, 건축면적, 연면적, 승강기 수 등.

| 주요 필드명 | 국문 | 비고 |
|---|---|---|
| mgmDongOulnPk | 관리동별개요PK | PK |
| mgmPmsrgstPk | 관리허가대장PK | FK |
| mainAtchGbCd | 주부속구분코드 | 0:주건축물 |
| mainPurpsCd | 주용도코드 | |
| strctCd | 구조코드 | |
| strctCdNm | 구조코드명 | 철근콘크리트 등 |
| roofCd | 지붕코드 | |
| archArea | 건축면적(㎡) | |
| totArea | 연면적(㎡) | |
| rideUseElvtCnt | 승용승강기수 | |
| emgenUseElvtCnt | 비상용승강기수 | |

### 3.3 주택유형 — getApHsTpInfo

건축물의 주택유형별 세대수 및 면적. 오피스텔/다세대/연립 등 구분.

| 주요 필드명 | 국문 | 비고 |
|---|---|---|
| mgmPmsrgstPk | 관리허가대장PK | FK |
| hstpGbCd | 주택유형구분코드 | |
| hstpGbCdNm | 주택유형구분코드명 | 준주택(오피스텔) 등 |
| silHoHhldCnt | 실호세대수(세대) | |
| silHoHhldArea | 실호세대수면적(㎡) | |

---

## 4. PK 전환 규칙 (기존 건축데이터 → 건축HUB)

건축데이터 민간개방 시스템(open.eais.go.kr)에서 건축HUB 시스템으로 전환됨에 따라 PK 형태가 변경되었다.

### 4.1 기존 PK 유형

- 유형 1: 시도·시군구코드 + '-' + 일련번호(22자리). 예: 11000-1000000000000001047965
- 유형 2: 시도·시군구코드 + '-' + 일련번호(22자리 미만). 예: 11000-100225790

### 4.2 전환 규칙

유형 1의 경우 시도·시군구코드와 '-'를 제거하면 신규 PK와 동일하다.

유형 2의 경우 통합분류코드(4자리)를 접두어로 추가해야 한다.
- 건축물대장: 통합분류코드(4자리) + 대장구분(1자리, 0:폐말소/1:실대장) + 일련번호
- 그 외: 통합분류코드(4자리) + 일련번호
- 비자치구는 상위 자치구의 통합분류코드를 사용 (천안시 동남구/서북구는 예외로 비자치구코드 사용)

통합분류코드 매핑은 별도 시트 참조 필요.

---

## 5. 기술문서 주의사항

| # | 항목 | 내용 |
|---|---|---|
| 1 | numOfRows 최대 100건 | MOLIT 실거래가(최대 1000)와 다름. 대량 조회 시 페이징 횟수 10배 |
| 2 | 에러코드 미명시 | resultCode "00" = 정상만 확인. 나머지는 MOLIT 체계 준용 추정 |
| 3 | PK 전환 | 기존 데이터와 연동 시 PK 변환 로직 필요 |
| 4 | http URL | 기술문서에 http로 표기. 실제 https 동작 여부 테스트 필요 |
| 5 | 법정동코드 | 행정표준코드관리시스템(code.go.kr) 기준. dim_region과 매핑 필요 |
| 6 | 현재 스코프 | Landbrief 확정 12종 지표 및 source CHECK 8종에 미포함. 향후 확장용 |
```

---

여기까지가 ECOS + REB + 청약홈 + 건축HUB 4개 소스 전체 정리

찾았다. MOLIT_STAT API 명세를 완전히 확인했다. 정리해줄게.

---

- **form_id=2082**: 시·군·구별 미분양현황 → HANDOVER의 `UNSOLD_UNITS_SIGUNGU`
- **form_id=5328**: 공사완료후 미분양현황 → HANDOVER의 `UNSOLD_UNITS_COMPLETED`

둘 다 같은 MOLIT_STAT API 체계(stat.molit.go.kr)를 쓰고, form_id만 다르다. 기술문서 내용을 확인했으니 정리한다.

```markdown
# MOLIT_STAT (국토교통 통계누리) API 기술문서 정리

> 원본: stat.molit.go.kr/portal/api/apiList.do (웹 확인)
> 정리일: 2026-02-28
> 목적: Landbrief 수집 스크립트 개발 및 ERROR_CODE_HANDLING.md 작성 기반

---

## 1. 공통 사항

### 1.1 게이트웨이

모든 API는 `stat.molit.go.kr/portal/openapi/service/rest/` 하위에 위치한다.
운영 주체는 국토교통부이며, 인증키는 국토교통 통계누리 사이트에서 발급받는다 (HANDOVER의 MOLIT_STAT_API_KEY).
별도 기술문서 PDF는 존재하지 않으며, stat.molit.go.kr 웹에서만 명세를 제공한다.

### 1.2 인터페이스 공통

| 항목 | 값 |
|---|---|
| 프로토콜 | REST (GET) |
| 응답 포맷 | JSON |
| 인증 | key 파라미터 (쿼리스트링) |
| URL 프로토콜 | http (기술문서 기준, https 동작 여부 테스트 필요) |
| 페이지당 최대 건수 | 1,000건 (ERROR-335) |

### 1.3 요청 URL 패턴

```
http://stat.molit.go.kr/portal/openapi/service/rest/getList.do?key={인증키}&form_id={통계표ID}&style_num={양식구분}&start_dt={시작일자}&end_dt={종료일자}
```

### 1.4 요청 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| key | String | Y | OpenAPI에서 발급된 인증키 |
| form_id | Integer | Y | 통계표ID |
| style_num | Integer | Y | 양식구분 |
| start_dt | Integer | Y | 시작일자 (YYYYMM) |
| end_dt | Integer | Y | 종료일자 (YYYYMM) |

### 1.5 응답 필드 (공통)

| 필드명 | 설명 |
|---|---|
| status_code | 처리결과 코드 |
| message | 처리결과 메시지 |
| unitName | 단위 |
| formName | 통계표명 |
| date | 시계열 데이터 |

### 1.6 에러코드

| 코드 | 설명 | 처리 분류 |
|---|---|---|
| INFO-000 | 정상 처리 | OK |
| INFO-100 | 인증키 유효하지 않음 | ABORT (원칙 3) |
| INFO-200 | 해당하는 데이터가 없음 | OK — 정상 빈 응답 (원칙 2) |
| INFO-300 | 해당 서비스는 개방 취소된 서비스 | ABORT (원칙 3) |
| ERROR-301 | 파라미터 값 누락 혹은 유효하지 않음 | ABORT (원칙 3) |
| ERROR-334 | 종료일자보다 시작일자가 더 큼 | ABORT (원칙 3) |
| ERROR-335 | 데이터 요청 한번에 최대 1,000건 초과 | ABORT (원칙 3) |
| ERROR-500 | 서버 오류 | RETRY (원칙 4) |
| ERROR-600 | DB 연결 오류 | RETRY (원칙 4) |

#### 통합 처리 원칙 매핑

| 원칙 | 적용 코드 | 동작 |
|---|---|---|
| 원칙 1: 한도 초과 즉시 전체 중단 | (명시된 한도 초과 코드 없음 — 이용제한 안내만 존재) | 이용제한 발생 시 STOP |
| 원칙 2: 데이터 없음 = 정상 | INFO-200 | status=OK, row_count=0 |
| 원칙 3: 키/서비스 문제 = 전체 중단 | INFO-100, INFO-300, ERROR-301, ERROR-334, ERROR-335 | 수집 전체 STOP |
| 원칙 4: 일시 장애 = 재시도 최대 3회 | ERROR-500, ERROR-600 | 30→60→120초 백오프 |
| 원칙 5: row_count=0은 정상코드일 때만 OK | INFO-200일 때만 | 429 사고 재발 방지 |

#### 주의사항: 한도 초과 코드 미명시

기술문서에 일별 트래픽 한도 초과에 대한 에러코드가 없다. "지나치게 잦은 API 호출 시 이용에 제한이 발생할 수 있다"는 안내만 존재한다. 실제 제한 발생 시 어떤 응답이 오는지 테스트 필요.

---

## 2. Landbrief 수집 대상

| 지표 | form_id | style_num | 통계표명 | 데이터 범위 |
|---|---|---|---|---|
| UNSOLD_UNITS_SIGUNGU | 2082 | 1 | 시·군·구별 미분양현황 | 200012~ |
| UNSOLD_UNITS_COMPLETED | 5328 | 1 | 공사완료후 미분양현황 | 200701~ |

### 2.1 호출 예시

시·군·구별 미분양현황 (2025년 1월):
```
http://stat.molit.go.kr/portal/openapi/service/rest/getList.do?key={인증키}&form_id=2082&style_num=1&start_dt=202501&end_dt=202501
```

공사완료후 미분양현황 (2025년 1월):
```
http://stat.molit.go.kr/portal/openapi/service/rest/getList.do?key={인증키}&form_id=5328&style_num=1&start_dt=202501&end_dt=202501
```

---

## 3. 기술문서 주의사항

| # | 항목 | 내용 |
|---|---|---|
| 1 | http URL | 요청주소가 http로 표기. https 동작 여부 테스트 필요 |
| 2 | 한도 초과 코드 없음 | 다른 소스(MOLIT 22, ECOS 602, REB 337)와 달리 명시된 코드 없음. 실테스트 필요 |
| 3 | 양식구분(style_num) | 통계표마다 시계열별로 양식이 다를 수 있음. 통계 조회 화면에서 확인 필요 |
| 4 | 최대 1,000건 | ERROR-335. 장기 시계열 수집 시 기간 분할 필요 |
| 5 | 에러코드 체계 | INFO-/ERROR- 접두어 방식. ECOS, REB와 유사하나 코드 번호는 다름 |
| 6 | 별도 키 필요 | HANDOVER의 MOLIT_STAT_API_KEY. MOLIT 실거래 키와 다른 별도 키 |
```

---

이걸로 **기술문서 미확보였던 MOLIT_STAT도 완료**다.

최종 현황:

| 소스 | 상태 |
|---|---|
| MOLIT 실거래 13종 | 정리 완료 |
| ECOS 3종 | 정리 완료 |
| REB R-ONE 3종 | 정리 완료 |
| 청약홈 10종 | 정리 완료 |
| 건축HUB 17종 | 정리 완료 (향후 확장용) |
| MOLIT_STAT 2종 | **정리 완료** |
| MOIS | 팩트 미확인 → **패스** |
| HF | **드랍** |
| KB | PublicDataReader 경유 → 별도 경로 |