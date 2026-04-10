# LLM_HW - GCS 몰입캠프 과제 제출

이 저장소는 아래 3개 과제 실행 결과를 담고 있습니다.

1. `1.1` GCS-PULSE를 MCP/CLI로 각각 연결해 토큰 사용량과 경험 비교
2. `1.2` GCS-PULSE CLI + GWS CLI로 회의실 예약/구글캘린더/초대메일 자동화 Skill 구현
3. `2` NotebookLM 기반 AI Agent 토론 + 최종 발표자료 자동 생성

---

## 한눈에 보는 실측 결과

### 1.1) MCP vs CLI (실측 수치)

- 기준 파일: [compare_report.md](artifacts/assignment_1_1/compare_report.md), [raw_results.json](artifacts/assignment_1_1/raw_results.json)
- 토큰 추정 방식: `ceil(characters / 4)`

| 구분 | CLI | MCP |
|---|---:|---:|
| 평균 입력 토큰(est) | 18 | 20 |
| 평균 출력 토큰(est) | 410.33 | 386 |
| 평균 총 토큰(est) | 428.33 | 406 |
| 평균 지연(ms) | 1338 | 735.33 |

케이스별 수치:

| Case | CLI Total Tokens(est) / ms | MCP Total Tokens(est) / ms |
|---|---:|---:|
| 회의실 목록 조회 | 1146 / 2947 | 1047 / 788 |
| 1번 회의실 당일 예약 조회 | 116 / 583 | 133 / 944 |
| 2번 회의실 당일 예약 조회 | 23 / 484 | 38 / 474 |

---

### 1.2) GCS-PULSE + GWS 통합 Skill (실행 결과)

- 기준 파일: [report.md](artifacts/assignment_1_2/report.md)
- 성공 로그(실사용): [real_run_after_auth.json](artifacts/assignment_1_2/real_run_after_auth.json)
- 최신 드라이런 로그: [dry_run_20260406.json](artifacts/assignment_1_2/dry_run_20260406.json)

실사용 성공 로그 핵심값:

| 항목 | 값 |
|---|---|
| 예약 성공 | `reserved: true` |
| 회의실 / 예약 ID | `N.MR1` / `150` |
| 캘린더 이벤트 ID | `vqbhtfuo8jk6u8fc2g982agtac` |
| 캘린더 링크 | https://www.google.com/calendar/event?eid=dnFiaHRmdW84ams2dThmYzJnOTgyYWd0YWMgbWluaHllb2swMzA2QGdhY2hvbi5hYy5rcg |
| 캘린더 상태 | `confirmed` |
| 초대 메일 ID | `19d4e750f0683b22` |
| 오류 | `[]` |

드라이런(2026-04-06) 결과:

| 항목 | 값 |
|---|---|
| dry_run | `true` |
| 오류 | `The remote name could not be resolved: 'api.1000.school'` |

---

### 2) NotebookLM 자동 토론 + 발표자료 (실행 결과)

- 자동 실행 로그: [run_log.json](artifacts/assignment_2/20260406_notebooklm_auto_demo/run_log.json)
- Notebook ID: `fd54842a-de55-4d44-9164-9c76810d30dc`
- NotebookLM 웹 링크(로그인 필요): https://notebooklm.google.com/notebook/fd54842a-de55-4d44-9164-9c76810d30dc

자동 실행 산출물:

- 토론문: [notebooklm_debate.md](artifacts/assignment_2/20260406_notebooklm_auto_demo/notebooklm_debate.md)
- 발표자료(자동 생성): [notebooklm_final_presentation.md](artifacts/assignment_2/20260406_notebooklm_auto_demo/notebooklm_final_presentation.md)
- 슬라이드 덱(영문 원본): [notebooklm_slide_deck-slides.md](artifacts/assignment_2/20260406_notebooklm_auto_demo/notebooklm_slide_deck-slides.md)
- 슬라이드 덱(한국어 번역본): [notebooklm_slide_deck-slides.ko.md](artifacts/assignment_2/20260406_notebooklm_auto_demo/notebooklm_slide_deck-slides.ko.md)
- 발표자료(한국어 정리본): [notebooklm_final_presentation.ko.md](artifacts/assignment_2/20260406_notebooklm_auto_demo/notebooklm_final_presentation.ko.md)

결과 요약:

| 항목 | 값 |
|---|---|
| 소스 수 | `8` |
| 토론 라운드 수 | `3` |
| 최종 발표 슬라이드 수 | `10` |

---

## 1.1) MCP vs CLI 비교

### 실행 스크립트

- `scripts/run_assignment_1_1_compare.ps1`

### 핵심 구성 파일

- `scripts/gcs_pulse_cli_snippet.ps1`
- `scripts/gcs_pulse_mcp_bridge.mjs`

### 산출물

- [artifacts/assignment_1_1/raw_results.json](artifacts/assignment_1_1/raw_results.json)
- [artifacts/assignment_1_1/compare_report.md](artifacts/assignment_1_1/compare_report.md)

---

## 1.2) GCS-PULSE + GWS 통합 Skill

### 실행 스크립트

- `scripts/gcs_pulse_gws_skill.ps1`

### Skill 문서

- [skills/Skill.md](skills/Skill.md)

### 산출물

- [artifacts/assignment_1_2/report.md](artifacts/assignment_1_2/report.md)
- [artifacts/assignment_1_2/real_run_after_auth.json](artifacts/assignment_1_2/real_run_after_auth.json)
- [artifacts/assignment_1_2/dry_run_20260406.json](artifacts/assignment_1_2/dry_run_20260406.json)

---

## 2) NotebookLM 자동 토론 + 발표자료

### 자동화 스크립트

- `scripts/run_assignment_2_notebooklm_auto.ps1`

### 입력/보조 파일

- `artifacts/ai_debate_landing/pdf_text/*.txt`
- `artifacts/ai_debate_landing/debate_data.json`

### 주요 산출물

- [artifacts/assignment_2/20260406_notebooklm_auto_demo/notebooklm_debate.md](artifacts/assignment_2/20260406_notebooklm_auto_demo/notebooklm_debate.md)
- [artifacts/assignment_2/20260406_notebooklm_auto_demo/notebooklm_final_presentation.md](artifacts/assignment_2/20260406_notebooklm_auto_demo/notebooklm_final_presentation.md)
- [artifacts/assignment_2/20260406_notebooklm_auto_demo/run_log.json](artifacts/assignment_2/20260406_notebooklm_auto_demo/run_log.json)

수동 생성본:

- `artifacts/assignment_2/20260406_notebooklm/`

---

## 최종 통합 보고서

- [artifacts/final_submission_20260406.md](artifacts/final_submission_20260406.md)

---

## 실행 예시 (PowerShell)

### 1.1 실행

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_assignment_1_1_compare.ps1
```

### 1.2 실행 (실사용)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/gcs_pulse_gws_skill.ps1 `
  -StartAt "2026-04-12T10:00:00+09:00" `
  -EndAt "2026-04-12T11:00:00+09:00" `
  -Title "Assignment 1.2 Real Run" `
  -Room "N.MR1" `
  -Attendees "your@email.com" `
  -Purpose "Assignment 1.2" `
  -SendInviteEmail
```

### 2번 자동 실행

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_assignment_2_notebooklm_auto.ps1
```
