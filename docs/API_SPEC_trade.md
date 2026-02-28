**Part 1 (에러코드 공통 + API 엔드포인트 총괄 + 매매 7종)** / **Part 2 (전월세 4종 + 분양권 + 토지)** 로 나눕니다.

---

## Part 1

```markdown
# 국토교통부 실거래가 API 기술문서 정리

> 원본: 공공데이터포털 기술문서 PDF 13종 (2024.07.17 기준)
> 정리일: 2026-02-28
> 목적: Landbrief 수집 스크립트 개발 및 ERROR_CODE_HANDLING.md 작성 기반

---

## 1. 공통 사항

### 1.1 게이트웨이

모든 API는 `apis.data.go.kr` 경유이며, 기관코드 `1613000`(국토교통부) 하위에 위치한다.
운영 주체는 한국부동산원(053-663-8642)이고 데이터 갱신주기는 일 1회이다.

### 1.2 인터페이스 공통

| 항목 | 값 |
|---|---|
| 프로토콜 | REST (GET) |
| 응답 포맷 | XML only (JSON 미지원) |
| 인증 | serviceKey (URL Encode 필수) |
| 암호화 | 없음 (SSL 미적용, 단 AptTrade·AptTradeDev·SilvTrade는 https) |
| 초당 최대 트랜잭션 | 30 tps (전 API 동일) |
| 평균 응답 시간 | 500 ms |
| 최대 메시지 사이즈 | 1,000 bytes (헤더 기준, 바디는 별도) |

### 1.3 요청 파라미터 (전 API 공통)

| 파라미터 | 필수 | 크기 | 설명 |
|---|---|---|---|
| serviceKey | 1 | 100 | 공공데이터포털 발급 인증키 (URL Encode) |
| LAWD_CD | 1 | 5 | 법정동코드 앞 5자리 (시군구) |
| DEAL_YMD | 1 | 6 | 계약년월 (YYYYMM) |
| pageNo | 0 | 4 | 페이지 번호 (기본 1) |
| numOfRows | 0 | 4 | 한 페이지 결과 수 (기본 10) |

### 1.4 응답 공통 헤더

```xml
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items><item>...</item></items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>49</totalCount>
  </body>
</response>
```

정상 응답 시 resultCode="000", resultMsg="OK"이다.
데이터가 없는 정상 케이스는 resultCode="000" + totalCount=0 **또는** resultCode="003"(No Data)으로 온다.
두 가지 모두 정상(데이터 없음)으로 처리해야 한다.

### 1.5 에러코드 (13종 전 API 동일)

| resultCode | 코드값 | 설명 | 처리 분류 |
|---|---|---|---|
| 000 | OK | 정상 | OK |
| 01 | APPLICATION_ERROR | 제공기관 서비스 장애 | RETRY (원칙 4) |
| 02 | DB_ERROR | 제공기관 DB 장애 | RETRY (원칙 4) |
| 03 | NO_DATA | 데이터 없음 | OK — 정상 빈 응답 (원칙 2) |
| 04 | HTTP_ERROR | 제공기관 HTTP 장애 | RETRY (원칙 4) |
| 05 | SERVICE_TIMEOUT | 제공기관 타임아웃 | RETRY (원칙 4) |
| 10 | INVALID_PARAM | serviceKey 파라미터 누락 | ABORT — 키/설정 문제 (원칙 3) |
| 11 | MISSING_REQUIRED_PARAM | 필수 파라미터 누락 | ABORT — 코드 버그 (원칙 3) |
| 12 | SERVICE_NOT_FOUND | 잘못된 URL 또는 폐기된 서비스 | ABORT (원칙 3) |
| 20 | ACCESS_DENIED | 활용 승인 미완료 | ABORT (원칙 3) |
| 22 | RATE_LIMIT_EXCEEDED | 일일 트래픽 한도 초과 | ABORT — 전체 중단 (원칙 1) |
| 30 | UNREGISTERED_KEY | 잘못된 서비스키 또는 URL 인코딩 누락 | ABORT (원칙 3) |
| 31 | EXPIRED_KEY | 서비스키 기간 만료 | ABORT (원칙 3) |
| 32 | UNREGISTERED_DOMAIN_OR_IP | 등록되지 않은 IP/도메인 | ABORT (원칙 3) |

#### 에러코드 vs HTTP 상태코드 관계 (중요)

기술문서상 에러코드는 XML body의 resultCode로만 전달된다. 그러나 실제 운영 환경에서 HTTP 429가 XML 응답 없이 반환되는 경우가 확인되었다(#010 세션 429 사고). 따라서 수집 스크립트는 반드시 HTTP 상태코드를 먼저 검사한 뒤 XML resultCode를 파싱해야 한다.

```
판정 순서:
1) HTTP status != 200 → HTTP 레벨 에러 (429=RATE_LIMIT, 5xx=RETRY, 4xx=ABORT)
2) HTTP 200 + resultCode != "000" → XML 레벨 에러 (위 테이블 참조)
3) HTTP 200 + resultCode == "000" + totalCount == 0 → 정상 빈 응답
4) HTTP 200 + resultCode == "000" + totalCount > 0 → 정상 데이터
```

#### 통합 처리 원칙 매핑 (HANDOVER 원칙 1~5)

| 원칙 | 적용 코드 | 동작 |
|---|---|---|
| 원칙 1: 한도 초과 즉시 전체 중단 | HTTP 429, resultCode 22 | 수집 전체 STOP |
| 원칙 2: 데이터 없음 = 정상 | resultCode 03, totalCount=0 | status=OK, row_count=0 |
| 원칙 3: 키/서비스 문제 = 전체 중단 | resultCode 10,11,12,20,30,31,32 | 수집 전체 STOP, 알림 |
| 원칙 4: 일시 장애 = 재시도 최대 3회 | resultCode 01,02,04,05, HTTP 5xx | 30→60→120초 백오프 |
| 원칙 5: row_count=0은 정상코드일 때만 OK | 원칙 2 해당 시에만 | 429 사고 재발 방지 핵심 |

---

## 2. API 엔드포인트 총괄

| # | trade_type (DB) | API명 (국문) | 서비스명 | 엔드포인트 함수 | 거래 구분 |
|---|---|---|---|---|---|
| 1 | APT_SALE | 아파트 매매 실거래가 자료 | RTMSDataSvcAptTrade | getRTMSDataSvcAptTrade | 매매 |
| 2 | APT_SALE_DTL | 아파트 매매 실거래가 상세 자료 | RTMSDataSvcAptTradeDev | getRTMSDataSvcAptTradeDev | 매매 |
| 3 | APT_RENT | 아파트 전월세 실거래가 자료 | RTMSDataSvcAptRent | getRTMSDataSvcAptRent | 전월세 |
| 4 | APT_RIGHT | 아파트 분양권전매 실거래가 자료 | RTMSDataSvcSilvTrade | getRTMSDataSvcSilvTrade | 매매 |
| 5 | RH_SALE | 연립다세대 매매 실거래가 자료 | RTMSDataSvcRHTrade | getRTMSDataSvcRHTrade | 매매 |
| 6 | RH_RENT | 연립다세대 전월세 실거래가 자료 | RTMSDataSvcRHRent | getRTMSDataSvcRHRent | 전월세 |
| 7 | SH_SALE | 단독/다가구 매매 실거래가 자료 | RTMSDataSvcSHTrade | getRTMSDataSvcShTrade | 매매 |
| 8 | SH_RENT | 단독/다가구 전월세 실거래가 자료 | RTMSDataSvcSHRent | getRTMSDataSvcSHRent | 전월세 |
| 9 | OFFI_SALE | 오피스텔 매매 실거래가 자료 | RTMSDataSvcOffiTrade | getRTMSDataSvcOffiTrade | 매매 |
| 10 | OFFI_RENT | 오피스텔 전월세 실거래가 자료 | RTMSDataSvcOffiRent | getRTMSDataSvcOffiRent | 전월세 |
| 11 | NRG_SALE | 상업업무용 부동산 매매 실거래가 자료 | RTMSDataSvcNrgTrade | getRTMSDataSvcNrgTrade | 매매 |
| 12 | INDU_SALE | 공장/창고 등 매매 실거래가 자료 | RTMSDataSvcInduTrade | getRTMSDataSvcInduTrade | 매매 |
| 13 | LAND_SALE | 토지 매매 실거래가 자료 | RTMSDataSvcLandTrade | getRTMSDataSvcLandTrade | 매매 |

### 2.1 URL 패턴

```
https://apis.data.go.kr/1613000/{서비스명}/{엔드포인트함수}
  ?serviceKey={키}&LAWD_CD={5자리}&DEAL_YMD={YYYYMM}
  &pageNo=1&numOfRows=1000
```

### 2.2 주의: 함수명 대소문자 불일치

기술문서 내 엔드포인트 함수명에 대소문자가 일부 불일치하는 경우가 있다.
단독/다가구 매매의 경우 기술문서상 `getRTMSDataSvcShTrade`('S' 대문자, 'h' 소문자)로 표기되어 있으나, 상세기능 목록에서는 `getRTMSDataSvcSHTrade`로 표기되어 있다. 실제 호출 시 어떤 형태가 유효한지 테스트가 필요하다.

또한 연립다세대 매매(RTMSDataSvcRHTrade)와 오피스텔 매매(RTMSDataSvcOffiTrade)의 상세기능 목록에서 엔드포인트 함수가 `getRTMSDataSvcAptRent`로 잘못 기재되어 있다. 이는 기술문서 오류이며 실제 Call Back URL을 기준으로 해야 한다.

---

## 3. 매매 API 응답 필드 상세 (7종)

### 3.1 아파트 매매 (APT_SALE) — RTMSDataSvcAptTrade

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| umdNm | 법정동 | 1 | 60 | |
| aptNm | 단지명 | 1 | 100 | |
| jibun | 지번 | 0 | 20 | |
| excluUseAr | 전용면적 | 0 | 22 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| dealAmount | 거래금액(만원) | 1 | 40 | 쉼표 포함 문자열 |
| floor | 층 | 0 | 10 | |
| buildYear | 건축년도 | 0 | 4 | |
| cdealType | 해제여부 | 0 | 1 | |
| cdealDay | 해제사유발생일 | 0 | 8 | |
| dealingGbn | 거래유형 | 0 | 10 | 중개거래/직거래 |
| estateAgentSggNm | 중개사소재지 | 0 | 3000 | 시군구단위 |
| rgstDate | 등기일자 | 0 | 8 | |
| aptDong | 아파트 동명 | 0 | 400 | |
| slerGbn | 매도자 | 0 | 100 | 개인/법인/공공기관/기타 |
| buyerGbn | 매수자 | 0 | 100 | 개인/법인/공공기관/기타 |
| landLeaseholdGbn | 토지임대부 아파트 여부 | 0 | 1 | Y/N |

### 3.2 아파트 매매 상세 (APT_SALE_DTL) — RTMSDataSvcAptTradeDev

APT_SALE 필드 전체를 포함하며, 아래 필드가 추가된다.

| 추가 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| umdCd | 법정동읍면동코드 | 1 | 5 | |
| landCd | 법정동지번코드 | 0 | 1 | |
| bonbun | 법정동본번코드 | 0 | 4 | |
| bubun | 법정동부번코드 | 0 | 4 | |
| roadNm | 도로명 | 0 | 100 | |
| roadNmSggCd | 도로명시군구코드 | 0 | 5 | |
| roadNmCd | 도로명코드 | 0 | 7 | |
| roadNmSeq | 도로명일련번호코드 | 0 | 2 | |
| roadNmbCd | 도로명지상지하코드 | 0 | 1 | |
| roadNmBonbun | 도로명건물본번호코드 | 0 | 5 | |
| roadNmBubun | 도로명건물부번호코드 | 0 | 5 | |
| aptSeq | 단지 일련번호 | 1 | 20 | 예: 11110-2339 |

### 3.3 연립다세대 매매 (RH_SALE) — RTMSDataSvcRHTrade

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| umdNm | 법정동 | 1 | 60 | |
| mhouseNm | 단지명 | 1 | 100 | ※ aptNm 아님 |
| jibun | 지번 | 0 | 20 | |
| buildYear | 건축년도 | 0 | 4 | |
| excluUseAr | 전용면적 | 0 | 22 | |
| landAr | 대지권면적 | 0 | 22 | ※ 이 API만 존재 |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| dealAmount | 거래금액(만원) | 1 | 40 | |
| floor | 층 | 0 | 10 | |
| cdealType | 해제여부 | 0 | 1 | |
| cdealDay | 해제사유발생일 | 0 | 8 | |
| dealingGbn | 거래유형 | 0 | 10 | |
| estateAgentSggNm | 중개사소재지 | 0 | 3000 | |
| rgstDate | 등기일자 | 0 | 8 | |
| slerGbn | 매도자 | 0 | 100 | |
| buyerGbn | 매수자 | 0 | 100 | |
| houseType | 주택유형구분 | 0 | 10 | 연립/다세대 |

### 3.4 단독/다가구 매매 (SH_SALE) — RTMSDataSvcSHTrade

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| umdNm | 법정동 | 1 | 60 | |
| houseType | 주택유형 | 0 | 6 | 단독/다가구 |
| jibun | 지번 | 0 | 20 | |
| totalFloorAr | 연면적 | 0 | 22 | ※ excluUseAr 아님 |
| plottageAr | 대지면적 | 0 | 22 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| dealAmount | 거래금액(만원) | 1 | 40 | |
| buildYear | 건축년도 | 0 | 40 | ※ 크기 40 (문서 원문) |
| cdealType | 해제여부 | 0 | 1 | |
| cdealDay | 해제사유발생일 | 0 | 8 | |
| dealingGbn | 거래유형 | 0 | 10 | |
| estateAgentSggNm | 중개사소재지 | 0 | 3000 | |
| slerGbn | 매도자 | 0 | 100 | |
| buyerGbn | 매수자 | 0 | 100 | |

### 3.5 오피스텔 매매 (OFFI_SALE) — RTMSDataSvcOffiTrade

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| sggNm | 시군구 | 1 | 30 | |
| umdNm | 법정동 | 1 | 60 | |
| jibun | 지번 | 0 | 20 | |
| offiNm | 단지명 | 1 | 100 | ※ aptNm, mhouseNm 아님 |
| excluUseAr | 전용면적 | 0 | 22 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| dealAmount | 거래금액(만원) | 1 | 40 | |
| floor | 층 | 0 | 10 | |
| buildYear | 건축년도 | 0 | 4 | |
| cdealType | 해제여부 | 0 | 1 | |
| cdealDay | 해제사유발생일 | 0 | 8 | |
| dealingGbn | 거래유형 | 0 | 10 | |
| estateAgentSggNm | 중개사소재지 | 0 | 3000 | |
| slerGbn | 매도자 | 0 | 100 | |
| buyerGbn | 매수자 | 0 | 100 | |

### 3.6 상업업무용 매매 (NRG_SALE) — RTMSDataSvcNrgTrade

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| sggNm | 시군구 | 1 | 30 | |
| umdNm | 법정동 | 1 | 60 | |
| buildingType | 건물유형 | 0 | 4 | 일반/집합 |
| jibun | 지번 | 0 | 20 | |
| buildingUse | 건물주용도 | 0 | 20 | |
| landUse | 용도지역 | 0 | 20 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| floor | 층 | 0 | 10 | |
| buildYear | 건축년도 | 0 | 4 | |
| dealAmount | 거래금액(만원) | 1 | 40 | |
| shareDealingType | 지분거래구분 | 0 | 4 | |
| plottageAr | 대지면적 | 0 | 22 | |
| buildingAr | 건물면적 | 0 | 22 | |
| cdealtype | 해제여부 | 0 | 1 | ※ camelCase 불일치 (cdealtype vs cdealType) |
| cdealDay | 해제사유발생일 | 0 | 8 | |
| dealingGbn | 거래유형 | 0 | 10 | |
| estateAgentSggNm | 중개사소재지 | 0 | 3000 | |
| slerGbn | 매도자 | 0 | 100 | |
| buyerGbn | 매수자 | 0 | 100 | |

### 3.7 공장/창고 매매 (INDU_SALE) — RTMSDataSvcInduTrade

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| sggNm | 시군구 | 1 | 30 | |
| umdNm | 법정동 | 1 | 60 | |
| buildingType | 건물유형 | 0 | 4 | 일반/집합 |
| jibun | 지번 | 0 | 20 | |
| buildingUse | 건물주용도 | 0 | 20 | |
| landUse | 용도지역 | 0 | 20 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| floor | 층 | 0 | 10 | |
| buildYear | 건축년도 | 0 | 4 | |
| dealAmount | 거래금액(만원) | 1 | 40 | |
| shareDealingType | 지분거래구분 | 0 | 4 | |
| plottageAr | 대지면적 | 0 | 22 | |
| buildingAr | 건물면적 | 0 | 22 | |
| cdealType | 해제여부 | 0 | 1 | |
| cdealDay | 해제사유발생일 | 0 | 8 | |
| dealingGbn | 거래유형 | 0 | 10 | |
| estateAgentSggNm | 중개사소재지 | 0 | 3000 | |
| slerGbn | 매도자 | 0 | 100 | |
| buyerGbn | 매수자 | 0 | 100 | |

NRG_SALE과 INDU_SALE의 응답 구조는 사실상 동일하다. 유일한 차이는 NRG_SALE의 해제여부 필드가 `cdealtype`(소문자 t)으로 기재되어 있는 점이다.
```

---

Part 1 여기까지입니다. Part 2 바로 이어서 출력합니다.

---

## Part 2

```markdown
## 4. 전월세 API 응답 필드 상세 (4종)

전월세 API들은 매매 API와 달리 보증금/월세/계약기간/갱신요구권 관련 필드를 가지며,
해제여부(cdealType/cdealDay), 거래유형(dealingGbn), 중개사소재지, 매도·매수자 정보가 없다.

### 4.1 아파트 전월세 (APT_RENT) — RTMSDataSvcAptRent

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| umdNm | 법정동 | 1 | 30 | |
| aptNm | 아파트명 | 1 | 100 | |
| jibun | 지번 | 0 | 20 | |
| excluUseAr | 전용면적 | 0 | 22 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| deposit | 보증금액(만원) | 1 | 40 | |
| monthlyRent | 월세금액(만원) | 1 | 40 | 전세이면 0 |
| floor | 층 | 0 | 10 | |
| buildYear | 건축년도 | 0 | 4 | |
| contractTerm | 계약기간 | 0 | 12 | 예: 24.09~26.09 |
| contractType | 계약구분 | 0 | 4 | 신규/갱신 |
| useRRRight | 갱신요구권사용 | 0 | 4 | |
| preDeposit | 종전계약보증금 | 0 | 40 | |
| preMonthlyRent | 종전계약월세 | 0 | 40 | |
| roadnm | 도로명 | 0 | 100 | ※ camelCase 아님 (소문자) |
| roadnmsggcd | 도로명시군구코드 | 0 | 5 | ※ 소문자 |
| roadnmcd | 도로명코드 | 0 | 7 | ※ 소문자 |
| roadnmseq | 도로명일련번호코드 | 0 | 2 | ※ 소문자 |
| roadnmbcd | 도로명지상지하코드 | 0 | 1 | ※ 소문자 |
| roadnmbonbun | 도로명건물본번호코드 | 0 | 5 | ※ 소문자 |
| roadnmbubun | 도로명건물부번호코드 | 0 | 5 | ※ 소문자 |
| aptSeq | 단지 일련번호 | 0 | 20 | |

**주의**: 아파트 전월세의 도로명 관련 필드는 camelCase가 아닌 전체 소문자로 내려온다.
아파트 매매 상세(AptTradeDev)에서는 `roadNm`, `roadNmSggCd` 등 camelCase인 반면,
아파트 전월세에서는 `roadnm`, `roadnmsggcd` 등 소문자이다. 파싱 시 주의 필요.

### 4.2 연립다세대 전월세 (RH_RENT) — RTMSDataSvcRHRent

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| umdNm | 법정동 | 1 | 30 | |
| houseType | 주택유형 | 0 | 6 | 연립/다세대 |
| mhouseNm | 연립다세대명 | 0 | 100 | |
| jibun | 지번 | 0 | 20 | |
| buildYear | 건축년도 | 0 | 4 | |
| excluUseAr | 전용면적 | 0 | 22 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| deposit | 보증금액(만원) | 1 | 40 | |
| monthlyRent | 월세금액(만원) | 1 | 40 | |
| floor | 층 | 0 | 10 | |
| contractTerm | 계약기간 | 0 | 12 | |
| contractType | 계약구분 | 0 | 4 | |
| useRRRight | 갱신요구권사용 | 0 | 4 | |
| preDeposit | 종전계약보증금 | 0 | 40 | |
| preMonthlyRent | 종전계약월세 | 0 | 40 | |

### 4.3 단독/다가구 전월세 (SH_RENT) — RTMSDataSvcSHRent

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| houseType | 주택유형 | 0 | 6 | 단독/다가구 |
| umdNm | 법정동 | 1 | 30 | |
| totalFloorAr | 연면적 | 0 | 22 | ※ excluUseAr 아님 |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| deposit | 보증금액(만원) | 1 | 40 | |
| monthlyRent | 월세금액(만원) | 1 | 40 | |
| buildYear | 건축년도 | 0 | 4 | |
| contractTerm | 계약기간 | 0 | 12 | |
| contractType | 계약구분 | 0 | 4 | |
| useRRRight | 갱신요구권사용 | 0 | 4 | |
| preDeposit | 종전계약보증금 | 0 | 40 | |
| preMonthlyRent | 종전계약월세 | 0 | 40 | |

**주의**: 단독/다가구 전월세에는 단지명(aptNm/mhouseNm/offiNm) 필드가 없다.

### 4.4 오피스텔 전월세 (OFFI_RENT) — RTMSDataSvcOffiRent

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| sggNm | 시군구 | 1 | 30 | |
| umdNm | 법정동 | 1 | 60 | |
| jibun | 지번 | 0 | 20 | |
| offiNm | 단지명 | 0 | 100 | |
| excluUseAr | 전용면적 | 0 | 22 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| deposit | 보증금액(만원) | 1 | 40 | |
| monthlyRent | 월세금액(만원) | 1 | 40 | |
| floor | 층 | 0 | 10 | |
| buildYear | 건축년도 | 0 | 4 | |
| contractTerm | 계약기간 | 0 | 12 | |
| contractType | 계약구분 | 0 | 4 | |
| useRRRight | 갱신요구권사용 | 0 | 4 | |
| preDeposit | 종전계약보증금 | 0 | 40 | |
| preMonthlyRent | 종전계약월세 | 0 | 40 | |

---

## 5. 분양권·토지 API 응답 필드 상세 (2종)

### 5.1 아파트 분양권전매 (APT_RIGHT) — RTMSDataSvcSilvTrade

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| sggNm | 시군구 | 1 | 30 | |
| umdNm | 법정동 | 1 | 60 | |
| aptNm | 단지 | 0 | 100 | |
| jibun | 지번 | 0 | 20 | |
| excluUseAr | 전용면적 | 0 | 22 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| dealAmount | 거래금액(만원) | 1 | 40 | |
| ownershipGbn | 구분 | 0 | 2 | 입주권일 경우 '입' |
| floor | 층 | 0 | 10 | |
| cdealType | 해제여부 | 0 | 1 | |
| cdealDay | 해제사유발생일 | 0 | 8 | |
| dealingGbn | 거래유형 | 0 | 10 | |
| estateAgentSggNm | 중개사소재지 | 0 | 3000 | |
| slerGbn | 매도자 | 0 | 100 | |
| buyerGbn | 매수자 | 0 | 100 | |

**특이사항**: buildYear(건축년도) 필드가 없다. 분양권 특성상 미건축 상태이기 때문이다.

### 5.2 토지 매매 (LAND_SALE) — RTMSDataSvcLandTrade

| 필드명 | 국문 | 필수 | 크기 | 비고 |
|---|---|---|---|---|
| sggCd | 지역코드 | 1 | 5 | |
| sggNm | 시군구 | 1 | 30 | |
| umdNm | 법정동 | 1 | 60 | |
| jibun | 지번 | 0 | 20 | |
| jimok | 지목 | 0 | 20 | ※ 토지만 존재 |
| landUse | 용도지역 | 0 | 20 | |
| dealYear | 계약년도 | 1 | 4 | |
| dealMonth | 계약월 | 1 | 2 | |
| dealDay | 계약일 | 1 | 2 | |
| dealArea | 거래면적 | 0 | 22 | ※ excluUseAr 아님 |
| dealAmount | 거래금액(만원) | 1 | 40 | |
| shareDealingType | 지분거래구분 | 0 | 4 | |
| cdealType | 해제여부 | 0 | 1 | |
| cdealDay | 해제사유발생일 | 0 | 8 | |
| dealingGbn | 거래유형 | 0 | 10 | |
| estateAgentSggNm | 중개사소재지 | 0 | 3000 | |

**특이사항**: 매도자(slerGbn), 매수자(buyerGbn), 건축년도(buildYear), 층(floor) 필드가 없다. 토지 거래 특성상 건물 관련 필드가 불필요하기 때문이다.

---

## 6. API별 단지명 필드명 차이 요약

| API 유형 | 필드명 | 비고 |
|---|---|---|
| 아파트 매매/매매상세/전월세/분양권 | aptNm | |
| 연립다세대 매매/전월세 | mhouseNm | |
| 오피스텔 매매/전월세 | offiNm | |
| 단독/다가구 매매/전월세 | (없음) | 단지명 개념 없음 |
| 상업업무용/공장창고/토지 | (없음) | 단지명 개념 없음 |

---

## 7. API별 면적 필드명 차이 요약

| API 유형 | 필드명 | 의미 |
|---|---|---|
| 아파트 계열, 연립다세대, 오피스텔 | excluUseAr | 전용면적 |
| 단독/다가구 | totalFloorAr | 연면적 |
| 상업업무용, 공장/창고 | buildingAr + plottageAr | 건물면적 + 대지면적 |
| 연립다세대 매매 | excluUseAr + landAr | 전용면적 + 대지권면적 |
| 토지 | dealArea | 거래면적 |

---

## 8. 서비스 URL 프로토콜 차이

기술문서 기준으로 http/https가 혼재되어 있다.

| API | 서비스 URL 프로토콜 | Call Back URL 프로토콜 |
|---|---|---|
| AptTrade | https | https |
| AptTradeDev | http | http |
| AptRent | http | http |
| SilvTrade | http | https |
| RHTrade | http | https |
| RHRent | http | http |
| SHTrade | http | http |
| SHRent | http | https |
| OffiTrade | http | http |
| OffiRent | http | https |
| NrgTrade | http | https |
| InduTrade | http | https |
| LandTrade | http | https |

실제로는 `https://apis.data.go.kr` 로 통일해서 호출하면 전부 동작한다.
수집 스크립트에서는 https로 통일할 것.

---

## 9. 기술문서 오류/주의사항 정리

| # | API | 항목 | 내용 |
|---|---|---|---|
| 1 | RHTrade | 상세기능 함수명 | `getRTMSDataSvcAptRent`로 오기재. 실제는 `getRTMSDataSvcRHTrade` |
| 2 | OffiTrade | 상세기능 함수명 | `getRTMSDataSvcAptRent`로 오기재. 실제는 `getRTMSDataSvcOffiTrade` |
| 3 | SHTrade | 상세기능 함수명 | 목록에서 `getRTMSDataSvcShTrade` (h 소문자), Call Back URL은 `getRTMSDataSvcSHTrade`. 테스트 필요 |
| 4 | NrgTrade | cdealtype | 응답 명세에서 `cdealtype` (소문자 t). 다른 API는 `cdealType`. 실제 응답 확인 필요 |
| 5 | AptRent | 도로명 필드 | camelCase 미적용 (`roadnm`, `roadnmsggcd` 등). AptTradeDev는 camelCase |
| 6 | OffiRent | WADL URL | `ggetRTMSDataSvcOffiRent` (g 중복 오타). 실제 호출 URL은 정상 |
| 7 | 전체 | HTTP 429 | 기술문서에 HTTP 429 관련 기술 없음. resultCode 22만 명시. 실제로는 XML 없이 HTTP 429가 올 수 있음 |
| 8 | 전체 | resultCode 000 + totalCount 0 | 기술문서에 명시 안 됨. 실제로 No Data 시 03 대신 000+totalCount=0으로 오는 케이스 존재 |

---

## 10. 신구 API 컬럼명 변경 요약 (공통 패턴)

구 API에서 신규 API로 전환하면서 공통적으로 적용된 변경 패턴은 다음과 같다.

전체 소문자에서 camelCase로 변경되었다 (예: `dealyear` → `dealYear`, `umdnm` → `umdNm`).
거래유형 필드명이 `reqgbn`에서 `dealingGbn`으로 변경되었다.
중개사소재지가 `rdealerlawdnm`에서 `estateAgentSggNm`으로 변경되었다.
매도자/매수자가 `slergbn`/`buyergbn`에서 `slerGbn`/`buyerGbn`으로 변경되었다.
지분거래구분이 `pdealingtype`/`partDealingType`에서 `shareDealingType`으로 통일되었다.
갱신요구권이 `urrcontractright`에서 `useRRRight`으로 변경되었다.

현재 수집 스크립트는 신규 API만 사용하므로 구 API 컬럼명은 참고용으로만 보관한다.
```

---

Part 1 + Part 2 완료입니다. 파일명은 `MOLIT_TRADE_API_SPEC.md`로 저장하면 됩니다.

정리하면서 발견한 **코드 작업에 영향 줄 핵심 발견 3가지**:

1. **기술문서 함수명 오기재 3건** — RHTrade, OffiTrade는 `getRTMSDataSvcAptRent`로, SHTrade는 대소문자 불일치. 현재 수집 스크립트의 URL이 실제로 어떤 값을 쓰고 있는지 확인 필요합니다.

2. **NrgTrade의 `cdealtype` 소문자 t** — 파싱 코드에서 `cdealType`으로 통일하고 있다면 상업업무용 데이터에서 해제여부를 놓칠 수 있습니다.

3. **AptRent 도로명 필드가 소문자** — `roadnm` vs `roadNm` 차이. fact_trade_raw에 VARCHAR로 넣을 때 컬럼 매핑이 맞는지 확인 필요합니다.