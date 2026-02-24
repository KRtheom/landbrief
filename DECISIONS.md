# DECISIONS.md — Landbrief
확정: 2026-02-24

## 파일 규칙
- D0-1: UTF-8 BOM 없음, LF, 4 spaces

## 환경 분리
- D1-1: ENV=prod → /docs /redoc /openapi.json 전체 차단

## 금지어
- D2-1: 금지어 목록은 app/filters/banned_words.py 단일 관리

## ETL 적재
- D3-1: atomic 적재 — staging → 검증 → rename swap, 단일 트랜잭션
- D3-2: swap 실패 시 원본 보존, meta_load_log에 FAIL 기록
- D3-3: 파일락 — etl/utils/lock.py, cron 중복 실행 방지

## 토큰
- D4-1: meta_download_token — UUID v4, 24시간 유효, 1회 사용 후 만료

## 스키마
- D5-1: db/migrations/ 순번 단조 증가, meta_schema_version 기록

## PDF
- D6-1: PDF 파일 서버 저장 금지, 스트림 직접 전송

## 코덱스 규칙
- D9-1: 이 문서 항목 단독 변경 금지
- D9-2: 충돌 시 건너뛰지 말고 BLOCKED: [사유] 명시