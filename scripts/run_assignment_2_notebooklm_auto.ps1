param(
  [string]$NotebookTitle = "GCS Day3 Auto Debate + Presentation",
  [string]$SourceDir = "artifacts/ai_debate_landing/pdf_text",
  [string]$ExtraSourceFile = "artifacts/ai_debate_landing/debate_data.json",
  [string]$OutputBaseDir = "artifacts/assignment_2",
  [string]$RunId = ""
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

$debatePrompt = "너는 사회자 중심 토론 생성기다. 참가자 1(공격적 찬성), 참가자 2(신중 반대), 사회자(중재와 요약)로 3라운드 토론문을 한국어로 작성해라. 순서: 사회자 오프닝 -> 참가자1 주장 -> 참가자2 반박 -> 사회자 라운드 요약. 각 발언 2~4문장. 마지막에 사회자 최종정리(합의점 3개, 쟁점 3개, 실행액션 3개). 주제: AI Scientist/scAInce를 농업 도전문제 해결에 적용."
$debateRaw = Invoke-CliText -Name "ask-debate" -Runner {
  notebooklm.cmd ask $notebookId $debatePrompt
}
$debateRawPath = Join-Path $rawDir "step_ask_debate.txt"
$debateRaw | Set-Content -Path $debateRawPath -Encoding utf8
$debateBody = Extract-AnswerBody $debateRaw
$debatePath = Join-Path $runDir "notebooklm_debate.md"
$debateBody | Set-Content -Path $debatePath -Encoding utf8

$presentationPrompt = "방금 소스들을 기반으로 최종 발표자료를 한국어로 만들어라. 형식: 10장 슬라이드 구성. 각 슬라이드마다 제목 1줄, 핵심 불릿 3개, 발표자 노트 2문장. 반드시 참가자1-사회자-참가자2 토론 결과를 반영하고, 마지막 10번은 Q&A 슬라이드로 작성."
$presentationRaw = Invoke-CliText -Name "ask-presentation" -Runner {
  notebooklm.cmd ask $notebookId $presentationPrompt
}
$presentationRawPath = Join-Path $rawDir "step_ask_presentation.txt"
$presentationRaw | Set-Content -Path $presentationRawPath -Encoding utf8
$presentationBody = Extract-AnswerBody $presentationRaw
$presentationPath = Join-Path $runDir "notebooklm_final_presentation.md"
$presentationBody | Set-Content -Path $presentationPath -Encoding utf8

$extraCount = if (Test-Path -LiteralPath $ExtraSourceFile) { 1 } else { 0 }
$runLog = @{
  run_id = $RunId
  notebook_id = $notebookId
  source_count = $sourceFiles.Count + $extraCount
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
Write-Output "Files:"
Write-Output " - $debatePath"
Write-Output " - $presentationPath"
Write-Output " - $(Join-Path $runDir "run_log.json")"
