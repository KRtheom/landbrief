```markdown

# Landbrief Handover v001 (2026-02-25) — 압축본

**블록 1: HANDOVER_v001 (기반 문서)**

## 인수인계서 관리 기준

### 구조
- 블록1 (HANDOVER): 프로젝트 기반 정보. 고정.
- 블록2 (CHANGELOG): 세션별 변경분. 매 세션 교체.

### 파일 관리
- 단일 파일: HANDOVER_v001.md
- 세션 종료 시 블록2(CHANGELOG) 항목을 파일 하단에 누적 추가.
- 블록1 변경 시 → 새 파일(v002) 생성, 블록2 리셋.

### 새 채팅 시작
- 최신 파일에서 블록1 복사 + 직전 세션 블록2 항목 선택 붙여넣기.

### 세션 종료
- 어시스턴트가 CHANGELOG 신규 항목 작성.
- 사용자가 다음 세션용 블록2로 보관.

### 블록1 갱신 조건
- G단위 태스크 완료 (G2, G5 등)
- 서버 환경 변경 (하드 확장, 경로 변경 등)
- 지표/스키마 확정 사항 변경
- 갱신 시 CHANGELOG 반영분 흡수 → CHANGELOG 리셋

### 금지
- 블록1에 실행 결과 원문 붙여넣기 (요약만)
- 세션 중간에 블록1 수정 (세션 종료 시 일괄 반영)

## 프로젝트
PF 사업성 평가 보고서 자동화. Phase1: 3페이지 검증 리포트. 1인 파일럿.

## 서버
Ubuntu 24.04.4 LTS, i7-10700, 32GB, SSH: ssh -p 2222 deploy@122.45.64.200, UFW 2222/tcp, KST, Python 3.12 venv.

## 경로
- LandScanner: ~/real_estate_report (서버, SSH로만 접근)
- Landbrief: ~/landbrief (하드 확장 후 생성 예정)
- DB: ~/real_estate_report/data/real_estate.db (SQLite)
- 빈 파일 주의: ~/real_estate_report/db/real_estate.db (사용 안 함)

## Git
- LandScanner: https://github.com/KRtheom/real-estate-report.git (private), 서버 G23(fa15c5c), G24(d8a62d5) 미반영
- Landbrief: 저장소 미생성, 첫 커밋 cf3d336 (G1 DECISIONS.md)

## 확정 12종 지표
1 APT_SALE_DTL (DATA_GO_KR) | 2 APT_RENT (DATA_GO_KR) | 3 REB_SALE_PRICE_INDEX (REB) | 4 REB_TRADE_VOLUME (REB) | 5 REB_RENT_PRICE_INDEX (REB) | 6 UNSOLD_UNITS_SIGUNGU (MOLIT_STAT) | 7 UNSOLD_UNITS_COMPLETED (MOLIT_STAT) | 8 MACRO_BASE_RATE (ECOS) | 9 HF_PIR (HUG) | 10 DEMO_POPULATION (KOSIS) | 11 DEMO_HOUSEHOLD (KOSIS) | 12 SUPPLY_INCOMING (DATA_GO_KR, odcloud, 반기갱신, 697건, perPage=700 1회호출)

# .env 키 목록 (8종)

| 변수명 | 길이 | 형식 | 실제 사용처 |
|---|---|---|---|
| DATA_GO_KR_API_KEY | 64 | 문자열 | 실거래 OpenAPI + odcloud(SUPPLY_INCOMING) |
| REB_API_KEY | 32 | 문자열 | R-ONE 지표 3종 |
| ECOS_API_KEY | 20 | 문자열 | 한국은행 기준금리/CPI/CSI/ESI |
| KOSIS_API_KEY | 44 | Base64 | 통계청 인구/세대 |
| HUG_API_KEY | 36 | UUID | 코드에서 미사용 (odcloud 경로는 DATA_GO_KR 사용) |
| MOLIT_STAT_API_KEY | 32 | 문자열 | 통계누리 미분양/착공 |
| HOUSTAT_API_KEY | 32 | 문자열 | PIR/LIR/KHAI (실제 HF_PIR 수집에 사용) |
| VWORLD_API_KEY | — | 문자열 | 공간정보 (현재 미활용, 잔존) |

⚠️ HUG_API_KEY는 코드에서 실제로 사용되지 않음. HF_PIR/HF_LIR은 HOUSTAT_API_KEY를 사용.
⚠️ Sprint 2에서 HUG↔MOLIT_STAT 뒤바뀜 사건 이력. 수정 시 datasets.yml 대조 필수.

## DB 실제 스키마 (문서와 다름!)
- sigungu_code → sgg_cd | deal_ymd → yyyymm | apt_name → bldg_nm | exclusive_area → exclu_use_ar
- fact_trade_raw: ~5.72M행, 58컬럼, 12종, dedup: uix_ftr_dedup(12컬럼 COALESCE UNIQUE)
- fact_indicator_month: 283행, 10컬럼, SUCCESS 17종
- dim_region: 269행 | etl_trade_raw_log: ~28K행

## LandScanner prefetch
PID 436797, 12종×268시군구×36개월=115,776건, ~24%완료, ~1.3초/건, 예상완료 2/27~28, resume 지원.
로그: ~/real_estate_report/logs/prefetch_all.log

## 이관 정책
fact_trade_raw 12종 → Landbrief 이관 | KB 지표 → 삭제 | 미수집 API전용 → 폐기 | LandScanner DB → 콜드보관(Synology)

## 설계 원칙
DB=UTC, 출력=KST, BOM없음, Mart기반리포트, PDF자동삭제, 금칙어필터, 원자적ETL swap, 입력검증(분양가5~80M, 기간1~60월), 파이프라인확장=datasets.yml+수집함수1개

## 작업 프로세스
지시서 → 실행 → diff 리뷰 → push → 서버 pull → 동적 검증. DECISIONS.md 인라인 준수. 불가 시 BLOCKED:[사유].

## 미결/블로커
- busy_timeout 미설정(P0) | serviceKey 로그 평문(P1) | dim_region 자동적재 미구현(P2)
- API 한도 10k→1k 축소 (2026-03-05 전후)
- 착공실적 시군구 불가 → 보류

## 태스크 현황
G1 DECISIONS.md ✅ | G2 DDL ⏳(품질점검 후) | G3~G10 대기
```

---

**블록 2: CHANGELOG**

```markdown
# CHANGELOG

## 2026-02-25 #001
- HANDOVER_v001 작성
- 12종 지표 확정 (11 기존 + SUPPLY_INCOMING)
- SUPPLY_INCOMING API 테스트 완료 (697건, odcloud)
- STAT_MOLIT 착공실적 테스트 완료 (360건, 시도만 → 보류)
- DB 실제 스키마 확인 (data/real_estate.db, 컬럼명 차이 발견)
- 데이터 품질 점검 스크립트 준비 완료, 실행 대기
- prefetch 재시작 PID 436797 (~24%)
- 인수인계서 2파일 체계 확정 (HANDOVER + CHANGELOG)
- 로컬=Landbrief 개발, 서버SSH=LandScanner 모니터링으로 분리
- 하드 확장 내일 → landbrief 폴더 생성 예정
- **다음: 서버SSH 접속 → 품질점검 스크립트 실행 → 결과 보고 → CHANGELOG #002 → G2 DDL 착수**

## 2026-02-25 #002
- 데이터 품질점검 실행 완료
  - APT 2종 핵심 컬럼 NULL 0건, 쓰레기 행 0건, ETL 실패 0건
  - 0 rows 발생: APT 2종 0건 (INDU_SALE/PRESALE 등 희소 유형만 589건, 정상)
  - 중복 키 조합: APT_SALE_DTL 4,477건, APT_RENT 56,810건 → G2 DDL에서 dedup 전략 정의 예정
  - 월수 부족 시군구 확인 (47940 등 거래 희소 지역, 데이터 누락 아닌 실제 무거래)
- 구 prefetch PID 232708 kill (PID 436797과 중복 실행 상태였음)
- 수집 기간 78개월(201909~) → 74개월(202001~202602)로 확정 (연 단위 정리)
- APT 2종 74개월 확장 수집 시작: PID 466111 (잔여 20,311건, ~7.3시간)
- 나머지 10종 74개월 확장 수집 시작: PID 468336 (잔여 186,097건, ~67시간)
- generate_month_list(74) = 202001~202602 확인 완료
- DB 용량: 2.5GB, 디스크 421GB 여유 → 제약 없음
- 서버 = 개인 PC (VPS 아님), 파일럿 후 정식 VPS 구축 예정
- 3/5 DATA_GO_KR 일일 한도 축소 (10,000→1,000) 대비: 수집 완료 예상 2/28 (3/5 전 여유)
- 한도 적용 범위(유형별 vs 키 전체) 미확인 → 추후 확인 필요
- fact_indicator_month 확정 10종 수집 상태 미확인 → 다음 세션에서 확인
- **다음: Landbrief 프로젝트 구조 설계 → G2 DDL 착수 / 수집 완료 후 무결성 재검증**

## 2026-02-25 #003
- 행안부 인구이동 API 시뮬레이션 완료
  - 10자리 행정기관코드, 양쪽 필수, 쌍 단위 호출, 3개월 제한
  - 성공 패턴: lv=1(시도간), lv=2(시군구간), lv=4(시도내부)
  - Phase 1 미사용 확정, 향후 검토
- INTENT.md v0.2 작성
  - 거래량 우선순위, 결측 표현, 캐시 무효화, Phase 2 매칭 기준 추가
  - 기술 스택 후보, 갱신 주기 매트릭스, 용어 사전 추가
- 다음: 품질 점검 스크립트 실행 → 결과 분석 → G2 DDL 착수

## 2026-02-25 #004
- HANDOVER_v001 작성
- 12종 지표 확정 (11 기존 + SUPPLY_INCOMING)
- SUPPLY_INCOMING API 테스트 완료 (697건, odcloud)
- STAT_MOLIT 착공실적 테스트 완료 (360건, 시도만 → 보류)
- DB 실제 스키마 확인 (data/real_estate.db, 컬럼명 차이 발견)
- 데이터 품질 점검 스크립트 준비 완료, 실행 대기
- prefetch 재시작 PID 436797 (~24%)
- 인수인계서 2파일 체계 확정 (HANDOVER + CHANGELOG)
- 하드 확장 내일 → landbrief 폴더 생성 예정
```

---

