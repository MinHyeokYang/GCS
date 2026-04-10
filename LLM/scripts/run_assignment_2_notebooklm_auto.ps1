param(
  [string]$NotebookTitle = "GCS Day3 Auto Debate + Presentation",
  [string]$SourceDir = "artifacts/ai_debate_landing/pdf_text",
  [string]$ExtraSourceFile = "artifacts/ai_debate_landing/debate_data.json",
  [string]$OutputBaseDir = "artifacts/assignment_2",
  [string]$RunId = "",
  [string]$Language = "ko-KR"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-CliText {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][scriptblock]$Runner
  )
  $lines = & $Runner 2>&1
  $exitCodeVar = Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue
  $exitCode = if ($exitCodeVar) { [int]$exitCodeVar.Value } else { 0 }
  $text = ($lines -join [Environment]::NewLine).Trim()
  if ($exitCode -ne 0) {
    throw "$Name failed (exit=$exitCode): $text"
  }
  return $text
}

function Extract-NotebookId {
  param([string]$Text)
  $m = [regex]::Match($Text, "ID:\s*([A-Za-z0-9_-]+)")
  if (-not $m.Success) { throw "Failed to parse Notebook ID from: $Text" }
  return $m.Groups[1].Value
}

function Extract-AnswerBody {
  param([string]$Text)
  $m = [regex]::Match($Text, "(?s)Answer:\s*(.+?)(?:\r?\nConversation:.*)?$")
  if ($m.Success) { return $m.Groups[1].Value.Trim() }
  return $Text.Trim()
}

function Test-HasKorean {
  param(
    [string]$Text,
    [int]$MinHangulChars = 30
  )
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $count = [regex]::Matches($Text, "[가-힣]").Count
  return ($count -ge $MinHangulChars)
}

if (-not $RunId) {
  $RunId = Get-Date -Format "yyyyMMdd_HHmmss_notebooklm_auto"
}

$runDir = Join-Path $OutputBaseDir $RunId
$rawDir = Join-Path $runDir "raw"
New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

$sourceFiles = Get-ChildItem -File (Join-Path $SourceDir "*.txt") | Sort-Object Name
if ($sourceFiles.Count -eq 0) {
  throw "No source text files found in $SourceDir"
}

$createOutput = Invoke-CliText -Name "create-notebook" -Runner {
  notebooklm.cmd create "$NotebookTitle $RunId"
}
$createOutput | Set-Content -Path (Join-Path $rawDir "step_create_notebook.txt") -Encoding utf8
$notebookId = Extract-NotebookId $createOutput

foreach ($f in $sourceFiles) {
  $title = "src_" + $f.BaseName
  $out = Invoke-CliText -Name "add-text-$title" -Runner {
    notebooklm.cmd source add-text $notebookId $title -f $f.FullName
  }
  $out | Set-Content -Path (Join-Path $rawDir ("step_add_{0}.txt" -f $f.BaseName)) -Encoding utf8
}

if (Test-Path -LiteralPath $ExtraSourceFile) {
  $extraOut = Invoke-CliText -Name "add-text-extra" -Runner {
    notebooklm.cmd source add-text $notebookId "src_debate_json" -f $ExtraSourceFile
  }
  $extraOut | Set-Content -Path (Join-Path $rawDir "step_add_extra_source.txt") -Encoding utf8
}

$isKoreanTarget = $Language -like "ko*"

$debatePrompt = if ($isKoreanTarget) {
  "Create a 3-round debate transcript in Korean (ko-KR) with Participant 1 (pro), Participant 2 (con), and Moderator (summary). Sequence per round: moderator opening -> participant1 claim -> participant2 rebuttal -> moderator summary. Keep each turn 2-4 sentences. End with final moderator summary: 3 agreements, 3 disputes, 3 actions. Topic: applying AI Scientist/scAInce to agricultural challenges."
} else {
  "Generate a 3-round debate transcript with participant 1, participant 2, and a moderator."
}

$debateRaw = Invoke-CliText -Name "ask-debate" -Runner {
  notebooklm.cmd ask $notebookId $debatePrompt
}
$debateRawPath = Join-Path $rawDir "step_ask_debate.txt"
$debateRaw | Set-Content -Path $debateRawPath -Encoding utf8
$debateBody = Extract-AnswerBody $debateRaw
$debatePath = Join-Path $runDir "notebooklm_debate.md"
$debateBody | Set-Content -Path $debatePath -Encoding utf8

$presentationPrompt = if ($isKoreanTarget) {
  "Create the final presentation in Korean (ko-KR). Format: 10 slides. For each slide provide: one-line title, three key bullets, and two-sentence speaker note. Reflect the participant1-moderator-participant2 debate outcome. Slide 10 must be Q&A."
} else {
  "Create a 10-slide final presentation from the current notebook sources."
}

$presentationRaw = Invoke-CliText -Name "ask-presentation" -Runner {
  notebooklm.cmd ask $notebookId $presentationPrompt
}
$presentationRawPath = Join-Path $rawDir "step_ask_presentation.txt"
$presentationRaw | Set-Content -Path $presentationRawPath -Encoding utf8
$presentationBody = Extract-AnswerBody $presentationRaw

if ($isKoreanTarget -and -not (Test-HasKorean -Text $presentationBody -MinHangulChars 40)) {
  $forcePrompt = "Rewrite the previous response in Korean (ko-KR) as a 10-slide presentation. Keep structure per slide: title, 3 bullets, 2-sentence speaker note. Avoid full English sentences."
  $forceRaw = Invoke-CliText -Name "ask-presentation-force-korean" -Runner {
    notebooklm.cmd ask $notebookId $forcePrompt
  }
  $forceRawPath = Join-Path $rawDir "step_ask_presentation_force_korean.txt"
  $forceRaw | Set-Content -Path $forceRawPath -Encoding utf8
  $presentationBody = Extract-AnswerBody $forceRaw
}

$presentationPath = Join-Path $runDir "notebooklm_final_presentation.md"
$presentationBody | Set-Content -Path $presentationPath -Encoding utf8

$extraCount = if (Test-Path -LiteralPath $ExtraSourceFile) { 1 } else { 0 }
$runLog = @{
  run_id = $RunId
  notebook_id = $notebookId
  source_count = $sourceFiles.Count + $extraCount
  language = $Language
  output_files = @(
    $debatePath,
    $presentationPath
  )
  created_at = (Get-Date).ToString("o")
}

($runLog | ConvertTo-Json -Depth 10) | Set-Content -Path (Join-Path $runDir "run_log.json") -Encoding utf8

Write-Output "NotebookLM auto pipeline completed."
Write-Output "Run directory: $runDir"
Write-Output "Notebook ID: $notebookId"
Write-Output "Language: $Language"
Write-Output "Files:"
Write-Output " - $debatePath"
Write-Output " - $presentationPath"
Write-Output " - $(Join-Path $runDir "run_log.json")"

