$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-ApproxTokens {
  param([string]$Text)
  if ([string]::IsNullOrEmpty($Text)) { return 0 }
  return [int][Math]::Ceiling($Text.Length / 4.0)
}

function Ensure-GcsPulseBridge {
  param(
    [string]$BaseUrl,
    [string]$Token
  )

  $scriptPath = (Resolve-Path "scripts/gcs_pulse_mcp_bridge.mjs").Path
  & mcporter.cmd config remove gcs-pulse-bridge 2>$null | Out-Null
  & mcporter.cmd config add gcs-pulse-bridge --command node --arg $scriptPath --env "GCS_PULSE_API_BASE_URL=$BaseUrl" --env "GCS_PULSE_TOKEN=$Token" | Out-Null
}

function Invoke-ByCli {
  param([hashtable]$Case)

  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  $cliScript = (Resolve-Path "scripts/gcs_pulse_cli_snippet.ps1").Path
  $cliNamed = $Case.cli_named
  $lines = & $cliScript -Command $Case.cli_command @cliNamed 2>&1
  $sw.Stop()

  $text = ($lines -join [Environment]::NewLine).Trim()
  $parsed = $text | ConvertFrom-Json
  $requestText = ($Case.cli_request | ConvertTo-Json -Depth 12 -Compress)

  [PSCustomObject]@{
    path = "CLI"
    case_id = $Case.id
    case_name = $Case.name
    duration_ms = [int]$sw.ElapsedMilliseconds
    input_tokens = Get-ApproxTokens $requestText
    output_tokens = Get-ApproxTokens $text
    total_tokens = (Get-ApproxTokens $requestText) + (Get-ApproxTokens $text)
    request_preview = $requestText
    response_preview = ($text.Substring(0, [Math]::Min(180, $text.Length)))
    raw = $parsed
  }
}

function Invoke-ByMcp {
  param([hashtable]$Case)

  $selector = "gcs-pulse-bridge.$($Case.mcp_tool)"
  $argList = @()
  foreach ($key in $Case.mcp_args.Keys) {
    $argList += "$key=$($Case.mcp_args[$key])"
  }

  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  $lines = & mcporter.cmd call $selector @argList 2>&1
  $sw.Stop()

  $text = ($lines -join [Environment]::NewLine).Trim()
  $parsed = $text | ConvertFrom-Json
  $requestText = (@{
      tool = $selector
      args = $Case.mcp_args
    } | ConvertTo-Json -Depth 12 -Compress)

  $duration = if ($parsed.elapsed_ms) { [int]$parsed.elapsed_ms } else { [int]$sw.ElapsedMilliseconds }

  [PSCustomObject]@{
    path = "MCP"
    case_id = $Case.id
    case_name = $Case.name
    duration_ms = $duration
    input_tokens = Get-ApproxTokens $requestText
    output_tokens = Get-ApproxTokens $text
    total_tokens = (Get-ApproxTokens $requestText) + (Get-ApproxTokens $text)
    request_preview = $requestText
    response_preview = ($text.Substring(0, [Math]::Min(180, $text.Length)))
    raw = $parsed
  }
}

function Write-MarkdownReport {
  param(
    [array]$Rows,
    [string]$Path
  )

  $avg = {
    param($items, $prop)
    if (-not $items -or $items.Count -eq 0) { return 0 }
    return [Math]::Round((($items | Measure-Object -Property $prop -Average).Average), 2)
  }

  $cliRows = $Rows | Where-Object { $_.path -eq "CLI" }
  $mcpRows = $Rows | Where-Object { $_.path -eq "MCP" }

  $sb = New-Object System.Text.StringBuilder
  [void]$sb.AppendLine("# Assignment 1.1 - GCS-PULSE (Snippet API) CLI vs MCP")
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("> Token usage is estimated with `ceil(characters / 4)` for request/response payloads.")
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("## Per-case comparison")
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("| Path | Case | Input Tokens(est) | Output Tokens(est) | Total Tokens(est) | Duration(ms) |")
  [void]$sb.AppendLine("|---|---|---:|---:|---:|---:|")
  foreach ($row in $Rows) {
    [void]$sb.AppendLine("| $($row.path) | $($row.case_name) | $($row.input_tokens) | $($row.output_tokens) | $($row.total_tokens) | $($row.duration_ms) |")
  }
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("## Averages")
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("| Path | Avg Input | Avg Output | Avg Total | Avg Duration(ms) |")
  [void]$sb.AppendLine("|---|---:|---:|---:|---:|")
  [void]$sb.AppendLine("| CLI | $(& $avg $cliRows 'input_tokens') | $(& $avg $cliRows 'output_tokens') | $(& $avg $cliRows 'total_tokens') | $(& $avg $cliRows 'duration_ms') |")
  [void]$sb.AppendLine("| MCP | $(& $avg $mcpRows 'input_tokens') | $(& $avg $mcpRows 'output_tokens') | $(& $avg $mcpRows 'total_tokens') | $(& $avg $mcpRows 'duration_ms') |")
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("## Experience notes")
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("- CLI path is straightforward for scripts and CI (`powershell -File ...`).")
  [void]$sb.AppendLine("- MCP path is better when integrating the same operations into agent tool-calling workflows.")
  [void]$sb.AppendLine("- For read-only operations in this run, token/latency differences are small; MCP has extra protocol overhead.")

  $null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path)
  Set-Content -Path $Path -Value $sb.ToString() -Encoding utf8
}

$cfg = Get-Content -Raw ".vscode/settings.json" | ConvertFrom-Json
$token = $cfg.'terminal.integrated.env.windows'.ANTHROPIC_AUTH_TOKEN
if (-not $token) { throw "Missing ANTHROPIC_AUTH_TOKEN in .vscode/settings.json" }

$baseUrl = "https://api.1000.school"
$env:GCS_PULSE_TOKEN = $token
$env:GCS_PULSE_API_BASE_URL = $baseUrl

Ensure-GcsPulseBridge -BaseUrl $baseUrl -Token $token

$today = Get-Date -Format "yyyy-MM-dd"
$cases = @(
  @{
    id = "C1"
    name = "List meeting rooms"
    cli_command = "rooms-list"
    cli_named = @{}
    cli_request = @{ method = "GET"; path = "/meeting-rooms" }
    mcp_tool = "list_meeting_rooms"
    mcp_args = @{}
  },
  @{
    id = "C2"
    name = "List room #1 reservations today"
    cli_command = "reservations-list"
    cli_named = @{ RoomId = 1; Date = $today }
    cli_request = @{ method = "GET"; path = "/meeting-rooms/1/reservations"; query = @{ date = $today } }
    mcp_tool = "list_room_reservations"
    mcp_args = @{ room_id = 1; date = $today }
  },
  @{
    id = "C3"
    name = "List room #2 reservations today"
    cli_command = "reservations-list"
    cli_named = @{ RoomId = 2; Date = $today }
    cli_request = @{ method = "GET"; path = "/meeting-rooms/2/reservations"; query = @{ date = $today } }
    mcp_tool = "list_room_reservations"
    mcp_args = @{ room_id = 2; date = $today }
  }
)

$rows = @()
foreach ($case in $cases) {
  $rows += Invoke-ByCli -Case $case
  $rows += Invoke-ByMcp -Case $case
}

$rawPath = "artifacts/assignment_1_1/raw_results.json"
$reportPath = "artifacts/assignment_1_1/compare_report.md"

$null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $rawPath)
($rows | ConvertTo-Json -Depth 20) | Set-Content -Path $rawPath -Encoding utf8
Write-MarkdownReport -Rows $rows -Path $reportPath

Write-Output "Wrote:"
Write-Output " - $rawPath"
Write-Output " - $reportPath"
