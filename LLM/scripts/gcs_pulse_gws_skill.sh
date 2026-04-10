#!/usr/bin/env bash
set -euo pipefail

# GCS-PULSE + GWS Skill runner
# Usage: gcs_pulse_gws_skill.sh --mode [mcp|cli] --start START --end END --title TITLE --attendees "a,b" --room ROOM [--dry-run]

MODE="mcp"
DRY_RUN=false
START=""
END=""
TITLE=""
ATTENDEES=""
ROOM=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="$2"; shift 2;;
    --dry-run) DRY_RUN=true; shift;;
    --start) START="$2"; shift 2;;
    --end) END="$2"; shift 2;;
    --title) TITLE="$2"; shift 2;;
    --attendees) ATTENDEES="$2"; shift 2;;
    --room) ROOM="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

if [[ -z "$START" || -z "$END" || -z "$TITLE" ]]; then
  echo "start, end, and title are required" >&2
  exit 2
fi

echo "Mode=$MODE, DryRun=$DRY_RUN, Start=$START, End=$END, Title=$TITLE, Attendees=$ATTENDEES, Room=$ROOM"

# Helper: call GCS-PULSE MCP API
call_mcp_reserve() {
  local start="$1"; local end="$2"; local room="$3"
  local payload
  payload=$(jq -n --arg s "$start" --arg e "$end" --arg r "$room" '{start:$s,end:$e,room:$r}')
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY_RUN: MCP reserve payload: $payload"
    return 0
  fi
  curl -sS -X POST "${GCS_PULSE_MCP_URL:-}" \
    -H "Authorization: Bearer ${GCS_PULSE_TOKEN:-}" \
    -H 'Content-Type: application/json' \
    -d "$payload"
}

# Helper: call GCS-PULSE CLI
call_cli_reserve() {
  local start="$1"; local end="$2"; local room="$3"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY_RUN: CLI reserve --start $start --end $end --room $room"
    return 0
  fi
  if command -v gcs-pulse >/dev/null 2>&1; then
    gcs-pulse reserve --start "$start" --end "$end" --room "$room"
  else
    echo "gcs-pulse CLI not found" >&2
    return 2
  fi
}

# Helper: create Google Calendar event via python helper
create_gcal_event() {
  local start="$1"; local end="$2"; local title="$3"; local attendees="$4"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY_RUN: create_gcal_event $start $end $title $attendees"
    return 0
  fi
  python3 scripts/gcs_pulse_create_event.py --start "$start" --end "$end" --title "$title" --attendees "$attendees"
}

# Retry wrapper
retry() {
  local attempts=3
  local wait=2
  local i=0
  while true; do
    if "$@"; then return 0; fi
    i=$((i+1))
    if [[ $i -ge $attempts ]]; then echo "Failed after $attempts attempts" >&2; return 1; fi
    sleep $((wait**i))
  done
}

# Flow
if [[ "$MODE" == "mcp" ]]; then
  echo "Using MCP path"
  if ! retry call_mcp_reserve "$START" "$END" "$ROOM"; then
    echo "MCP reserve failed; suggesting alternatives"
    # Suggest +30 and +60
    alt1_start=$(date -d "$START +30 minutes" --iso-8601=minutes)
    alt1_end=$(date -d "$END +30 minutes" --iso-8601=minutes)
    alt2_start=$(date -d "$START +60 minutes" --iso-8601=minutes)
    alt2_end=$(date -d "$END +60 minutes" --iso-8601=minutes)
    echo "Alternatives: $alt1_start - $alt1_end, $alt2_start - $alt2_end"
    # Try alternatives
    if retry call_mcp_reserve "$alt1_start" "$alt1_end" "$ROOM"; then
      START="$alt1_start"; END="$alt1_end"
    elif retry call_mcp_reserve "$alt2_start" "$alt2_end" "$ROOM"; then
      START="$alt2_start"; END="$alt2_end"
    else
      echo "All attempts failed"; exit 1
    fi
  fi
elif [[ "$MODE" == "cli" ]]; then
  echo "Using CLI path"
  if ! retry call_cli_reserve "$START" "$END" "$ROOM"; then
    echo "CLI reserve failed; suggesting alternatives"
    alt1_start=$(date -d "$START +30 minutes" --iso-8601=minutes)
    alt1_end=$(date -d "$END +30 minutes" --iso-8601=minutes)
    alt2_start=$(date -d "$START +60 minutes" --iso-8601=minutes)
    alt2_end=$(date -d "$END +60 minutes" --iso-8601=minutes)
    echo "Alternatives: $alt1_start - $alt1_end, $alt2_start - $alt2_end"
    if retry call_cli_reserve "$alt1_start" "$alt1_end" "$ROOM"; then
      START="$alt1_start"; END="$alt1_end"
    elif retry call_cli_reserve "$alt2_start" "$alt2_end" "$ROOM"; then
      START="$alt2_start"; END="$alt2_end"
    else
      echo "All attempts failed"; exit 1
    fi
  fi
else
  echo "Unknown mode: $MODE"; exit 2
fi

# Create calendar event
if ! retry create_gcal_event "$START" "$END" "$TITLE" "$ATTENDEES"; then
  echo "Failed to create calendar event"; exit 1
fi

echo "Success: reserved room and created calendar event"
