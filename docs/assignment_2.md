# Assignment 2 Automation Guide

## Goal
Automate the full flow for assignment 2 using:
- Claude CLI
- NotebookLM CLI

Pipeline:
1. Collect research inputs
2. Run research in NotebookLM
3. Generate AI-agent debate transcript
4. Generate final report and slide deck
5. Save reproducible outputs and logs

## Required Setup
1. Claude CLI is installed and authenticated.
2. NotebookLM CLI is installed:
   - `notebooklm.cmd --version`
3. NotebookLM login is completed:
   - `notebooklm.cmd login`
   - Important: when NotebookLM home opens in browser, return to terminal and press `Enter`.
4. Prepare input config:
   - `config/assignment_2.input.json`

## Run
```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_assignment_2.ps1
```

Optional:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_assignment_2.ps1 -ConfigPath config/assignment_2.input.json
```

## Outputs
Each run writes to:
- `artifacts/assignment_2/<timestamp>/`

Expected files:
- `research.md`
- `debate.md`
- `final_report.md`
- `final_slide_deck*.png` and `final_slide_deck-slides.md` (from NotebookLM slide deck download)
- `final_presentation.md`
- `references.md`
- `run_log.json`
