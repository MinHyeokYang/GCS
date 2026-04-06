# GCS 몰입캠프 과제 실행 결과 (2026-04-06)

## 1.1) GCS-PULSE MCP vs CLI 비교

- 실행 방식: `scripts/run_assignment_1_1_compare.ps1`
- 산출물: `artifacts/assignment_1_1/raw_results.json`, `artifacts/assignment_1_1/compare_report.md`
- 비고: 현재 환경에서는 **내 계정(1팀 실행값)** 기준 실측 완료. 팀별 완전 비교는 팀별 토큰/계정으로 같은 스크립트를 반복 실행하면 됨.

### 측정 요약

| Path | Case | Input Tokens(est) | Output Tokens(est) | Total Tokens(est) | Duration(ms) |
|---|---|---:|---:|---:|---:|
| CLI | List meeting rooms | 10 | 1136 | 1146 | 2947 |
| MCP | List meeting rooms | 14 | 1033 | 1047 | 788 |
| CLI | List room #1 reservations today | 22 | 94 | 116 | 583 |
| MCP | List room #1 reservations today | 23 | 110 | 133 | 944 |
| CLI | List room #2 reservations today | 22 | 1 | 23 | 484 |
| MCP | List room #2 reservations today | 23 | 15 | 38 | 474 |

## Averages

| Path | Avg Input | Avg Output | Avg Total | Avg Duration(ms) |
|---|---:|---:|---:|---:|
| CLI | 18 | 410.33 | 428.33 | 1338 |
| MCP | 20 | 386 | 406 | 735.33 |

## 1.2) GCS-PULSE CLI + GWS CLI 통합 Skill

- 구현 파일: `scripts/gcs_pulse_gws_skill.ps1`, `skills/Skill.md`
- 목적: 회의실 예약 + 구글 캘린더 등록 + 참석자 초대 + 초대 메일 발송을 한 번에 처리

### 실 실행 증빙 (기존 성공 로그)

- reserved: True
- calendar_event.id: vqbhtfuo8jk6u8fc2g982agtac
- invite_email.id: 19d4e750f0683b22
- errors: 0

### 최신 드라이런 (2026-04-06)

- dry_run: True
- errors: The remote name could not be resolved: 'api.1000.school'

## 2) AI Agent 토론 + 최종 발표자료 자동 생성 (NotebookLM)

- 수동 실행 결과: `artifacts/assignment_2/20260406_notebooklm/`
- 완전 자동 스크립트: `scripts/run_assignment_2_notebooklm_auto.ps1`
- 자동 실행 결과: `artifacts/assignment_2/20260406_notebooklm_auto_demo/`
- 자동 실행 Notebook ID: fd54842a-de55-4d44-9164-9c76810d30dc

### 생성 파일

- `notebooklm_debate.md` (참가자1/참가자2/사회자 3라운드 토론문)
- `notebooklm_final_presentation.md` (10장 발표자료 + Q&A)
- `run_log.json` (실행 로그)

### 발표자료 미리보기 (앞부분)

```md
제공된 소스들을 바탕으로 'AI 과학자의 부상과 scAInce 패러다임'에 관한 최종 발표 자료를 작성하였습니다.

---

### **슬라이드 1: AI 과학자의 부상: 과학 연구의 새로운 패러다임**
*   **핵심 내용:**
    *   AI 에이전트 기반의 완전 자동화 연구 가능성 입증 [1, 2]
    *   'Co-pilot'에서 연구 전반을 주도하는 'Lab-pilot'으로의 전환 [3]
    *   지식 발견의 가속화를 통한 과학 연구의 민주화 예고 [4, 5]
*   **발표자 노트:** 오늘은 Sakana AI의 'The AI Scientist' 사례를 통해 AI가 과학 연구를 어떻게 혁신하고 있는지 살펴보겠습니다. 특히 AI가 연구의 보조자를 넘어 핵심 파트너로 진화하는 'scAInce' 패러다임의 등장을 집중 조명하겠습니다.

### **슬라이드 2: scAInce: AI와 과학의 융합 패러다임**
*   **핵심 내용:**
    *   AI를 단순한 도구가 아닌 핵심 연구 파트너로 활용하는 방법론 [1, 6]
    *   아이디어 생성부터 가설 검증까지의 전 과정 자동화 및 가속화 [7, 8]
    *   방대한 데이터를 기반으로 한 자율적 탐구와 새로운 지식 발견 [9, 10]
*   **발표자 노트:** scAInce는 AI 기술을 과학적 발견의 핵심 동력으로 삼는 새로운 연구 패러다임을 의미합니다. 이는 단순한 업무 자동화를 넘어 AI가 독립적으로 가설을 세우고 실험을 설계하여 연구의 속도를 비약적으로 높이는 시대를 의미합니다.

### **슬라이드 3: 'The AI Scientist' 프레임워크의 혁신**
*   **핵심 내용:**
```

