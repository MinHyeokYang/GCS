# GCS-PULSE + GWS Skill (Assignment 1.2)

## Goal
Run one command that performs all of these steps:
1. Reserve a room with GCS-PULSE (snippet API backend).
2. Create a Google Calendar event.
3. Add attendees to the event.
4. Optionally send an extra Gmail invite message.

## Files
- `scripts/gcs_pulse_cli_snippet.ps1`
  GCS-PULSE CLI wrapper (uses `https://api.1000.school`).
- `scripts/gcs_pulse_gws_skill.ps1`
  End-to-end orchestration script for assignment 1.2.

## Prerequisites
- `gws` CLI is installed (`gws.cmd --help`).
- GCS-PULSE token is available:
  - `GCS_PULSE_TOKEN`, or
  - `ANTHROPIC_AUTH_TOKEN` (fallback).
- For real Google execution (not dry-run), GWS OAuth must be configured:
  - `gws auth setup --login`
  - or set `GOOGLE_WORKSPACE_CLI_CLIENT_ID` + `GOOGLE_WORKSPACE_CLI_CLIENT_SECRET`, then run `gws auth login`.

## Usage
Dry-run (safe preview):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/gcs_pulse_gws_skill.ps1 `
  -DryRun `
  -StartAt "2026-04-03T10:00:00+09:00" `
  -EndAt "2026-04-03T11:00:00+09:00" `
  -Title "GCS Pulse Automation Demo" `
  -Room "N.MR1" `
  -Attendees "dev1@example.com,dev2@example.com" `
  -Purpose "Assignment 1.2 dry-run" `
  -SendInviteEmail
```

Real run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/gcs_pulse_gws_skill.ps1 `
  -StartAt "2026-04-03T10:00:00+09:00" `
  -EndAt "2026-04-03T11:00:00+09:00" `
  -Title "GCS Pulse Automation Demo" `
  -Room "N.MR1" `
  -Attendees "dev1@example.com,dev2@example.com" `
  -Purpose "Assignment 1.2 real run" `
  -SendInviteEmail
```

## Behavior
- If the first reservation slot fails, fallback slots (`+30m`, `+60m`) are attempted.
- Calendar creation uses `sendUpdates=all` for attendee notifications.
- If Google steps fail after reservation, the script attempts reservation rollback.
- Script output is a single JSON summary with:
  - reservation result,
  - calendar result,
  - gmail result,
  - rollback status,
  - errors.
