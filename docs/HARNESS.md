# HARNESS 운영 가이드

업데이트: 2026-04-10

## 1. 목적
작업을 `계획 -> 구현 -> 검증` 흐름으로 고정해 품질과 일관성을 유지한다.

## 2. 기본 흐름
1. Planner
- `docs/PRD.md` 기준으로 범위를 확정
- `docs/sprint_current.md`에 스프린트 계약 작성

2. Generator
- 계약 범위 안에서 코드/테스트 구현
- 모델/스키마/라우터/CLI/문서를 함께 갱신

3. Evaluator
- `pytest` 실행
- 체크리스트 충족 여부 확인
- `PASS`/`FAIL` 기록

## 3. 스프린트 규칙
- 계약 없는 구현 금지
- 스프린트 단위 완료 후 결과 기록
- 실패 시 원인과 다음 조치 명시

## 4. 품질 규칙
- Ruff, mypy, pytest를 기본 게이트로 사용
- E2E는 `pytest -m integration`으로 별도 검증
