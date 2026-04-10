# Assignment 1.2 Execution Report

Date: 2026-04-02

## Scope
Implemented and validated a single workflow that can:
1. Reserve a GCS-PULSE room (snippet API).
2. Create a Google Calendar event.
3. Add attendees.
4. Optionally send an extra Gmail invite message.

## Implemented Files
- `scripts/gcs_pulse_gws_skill.ps1`
- `scripts/gcs_pulse_cli_snippet.ps1`
- `skills/Skill.md`

## Validation Results

### 1) Dry-run success
Command executed with `-DryRun`:
- Output file: `artifacts/assignment_1_2/dry_run_result.json`
- Result highlights:
  - `reserved: true` (simulated reservation payload generated)
  - `calendar_event: dry_run true`
  - `invite_email: dry_run true`
  - `errors: []`

### 2) Real-run preflight check
Command executed without `-DryRun`:
- Output file: `artifacts/assignment_1_2/real_run_result.json`
- Result highlights:
  - `reserved: false`
  - Error: `GWS auth is not configured...`
  - No reservation side effect occurred (auth fails before reserve step).

### 3) GWS auth status evidence
- Output file: `artifacts/assignment_1_2/gws_auth_status.json`
- Current status:
  - `auth_method: none`
  - `client_secret.json` not found
  - no stored credentials/token

### 4) GWS setup precheck
- Command: `gws auth setup --dry-run`
- Result:
  - `gcloud CLI not found`
  - Google Cloud SDK installation is required for automated setup path.

### 5) Final real-run success (after auth + API enable)
- Output file: `artifacts/assignment_1_2/real_run_after_auth.json`
- Result highlights:
  - `reserved: true`
  - `calendar_event: created` (Google Calendar event ID present)
  - `invite_email: sent` (Gmail message ID present)
  - `errors: []`

## Notes
- The assignment 1.2 workflow is implemented and executable.
- Real execution was completed after:
  - Google OAuth client setup,
  - `gws auth login`,
  - enabling `calendar-json.googleapis.com` and `gmail.googleapis.com`.
