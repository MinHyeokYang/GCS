param(
  [string]$ConfigPath = "config/assignment_2.input.json",
  [switch]$SkipNotebookAuthCheck
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Remove-Ansi {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
  return [regex]::Replace($Text, "\x1B\[[0-9;]*[A-Za-z]", "")
}

function Invoke-CliCapture {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][scriptblock]$Runner,
    [string]$CapturePath = "",
    [switch]$AllowFailure
  )

  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  $prevErrorAction = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $lines = & $Runner 2>&1
  } finally {
    $ErrorActionPreference = $prevErrorAction
  }
  $sw.Stop()

  $exitCodeVar = Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue
  $exitCode = if ($exitCodeVar) { [int]$exitCodeVar.Value } else { 0 }
  $rawText = ($lines -join [Environment]::NewLine).Trim()
  $cleanText = Remove-Ansi $rawText

  if ($CapturePath) {
    $parent = Split-Path -Parent $CapturePath
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Set-Content -Path $CapturePath -Value $cleanText -Encoding utf8
  }

  if (-not $AllowFailure -and $exitCode -ne 0) {
    throw "$Name failed (exit=$exitCode): $cleanText"
  }

  return [PSCustomObject]@{
    name = $Name
    exit_code = $exitCode
    elapsed_ms = [int]$sw.ElapsedMilliseconds
    output = $cleanText
  }
}

function Get-RegexValue {
  param(
    [Parameter(Mandatory = $true)][string]$Text,
    [Parameter(Mandatory = $true)][string]$Pattern,
    [Parameter(Mandatory = $true)][string]$Label
  )

  $match = [regex]::Match($Text, $Pattern)
  if (-not $match.Success) {
    throw "Failed to parse $Label. Pattern: $Pattern. Output: $Text"
  }
  return $match.Groups[1].Value
}

function Extract-NotebookLmAnswer {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
  $clean = Remove-Ansi $Text
  $match = [regex]::Match($clean, "(?s)Answer:\s*(.+?)(?:\r?\nConversation:.*)?$")
  if ($match.Success) {
    return $match.Groups[1].Value.Trim()
  }
  return $clean.Trim()
}

function Extract-ResearchSummary {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
  $clean = Remove-Ansi $Text
  $match = [regex]::Match($clean, "(?s)Research complete\s*(.+)$")
  if ($match.Success) {
    return ("Research complete`n`n" + $match.Groups[1].Value.Trim())
  }
  return $clean.Trim()
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

function Add-RunStep {
  param(
    [hashtable]$RunLog,
    [string]$Step,
    [string]$Status,
    [int]$DurationMs = 0,
    [string]$OutputFile = "",
    [string]$Message = ""
  )

  $RunLog.steps += [PSCustomObject]@{
    step = $Step
    status = $Status
    duration_ms = $DurationMs
    output_file = $OutputFile
    message = $Message
    at = (Get-Date).ToString("o")
  }
}

function Resolve-SourcePath {
  param(
    [Parameter(Mandatory = $true)][string]$PathLike,
    [Parameter(Mandatory = $true)][string]$ConfigDir
  )

  if (Test-Path -LiteralPath $PathLike) {
    return (Resolve-Path -LiteralPath $PathLike).Path
  }

  $fromConfig = Join-Path $ConfigDir $PathLike
  if (Test-Path -LiteralPath $fromConfig) {
    return (Resolve-Path -LiteralPath $fromConfig).Path
  }

  throw "Source file not found: $PathLike"
}

function Set-ClaudeEnvFromSettings {
  if (-not (Test-Path ".vscode/settings.json")) { return }
  try {
    $cfg = Get-Content -Raw ".vscode/settings.json" | ConvertFrom-Json
    $termEnv = $cfg.'terminal.integrated.env.windows'
    if ($termEnv.ANTHROPIC_BASE_URL) { $env:ANTHROPIC_BASE_URL = $termEnv.ANTHROPIC_BASE_URL }
    if ($termEnv.ANTHROPIC_AUTH_TOKEN) { $env:ANTHROPIC_AUTH_TOKEN = $termEnv.ANTHROPIC_AUTH_TOKEN }
  } catch {
    # best effort only
  }
}

if (-not (Test-Path $ConfigPath)) {
  throw "Config not found: $ConfigPath"
}

$configFullPath = (Resolve-Path $ConfigPath).Path
$configDir = Split-Path -Parent $configFullPath
$config = Get-Content -Raw $configFullPath | ConvertFrom-Json

$topic = if ($config.topic) { [string]$config.topic } else { "The AI OOO" }
$targetLanguage = if ($config.language) { [string]$config.language } else { "ko-KR" }
$isKoreanTarget = $targetLanguage -like "ko*"
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path "artifacts/assignment_2" $runId
$rawDir = Join-Path $runDir "raw"
New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

$runLog = @{
  run_id = $runId
  started_at = (Get-Date).ToString("o")
  config_path = $configFullPath
  topic = $topic
  notebook_id = $null
  status = "running"
  steps = @()
}

$runLogPath = Join-Path $runDir "run_log.json"

try {
  $claudeCmd = Get-Command claude.cmd -ErrorAction SilentlyContinue
  $notebookCmd = Get-Command notebooklm.cmd -ErrorAction SilentlyContinue
  if (-not $claudeCmd) { throw "claude.cmd not found in PATH." }
  if (-not $notebookCmd) { throw "notebooklm.cmd not found in PATH." }
  Add-RunStep -RunLog $runLog -Step "prereq_tools" -Status "ok" -Message "claude.cmd + notebooklm.cmd detected"

  if (-not $SkipNotebookAuthCheck) {
    $authPath = Join-Path $rawDir "step_auth_probe.txt"
    $authProbe = Invoke-CliCapture -Name "NotebookLM auth probe" -AllowFailure -CapturePath $authPath -Runner {
      notebooklm.cmd list
    }
    if ($authProbe.exit_code -ne 0 -and $authProbe.output -match "Not authenticated") {
      throw "NotebookLM is not authenticated. Run: notebooklm.cmd login, then press Enter in terminal after NotebookLM home page appears."
    }
    Add-RunStep -RunLog $runLog -Step "auth_probe" -Status "ok" -DurationMs $authProbe.elapsed_ms -OutputFile $authPath
  }

  Set-ClaudeEnvFromSettings

  $notebookTitle = if ($config.notebook_title) { [string]$config.notebook_title } else { "Task2 - $topic" }
  $createPath = Join-Path $rawDir "step_create_notebook.txt"
  $createResult = Invoke-CliCapture -Name "Create notebook" -CapturePath $createPath -Runner {
    notebooklm.cmd create $notebookTitle
  }
  $notebookId = Get-RegexValue -Text $createResult.output -Pattern "ID:\s*([A-Za-z0-9_-]+)" -Label "notebook id"
  $runLog.notebook_id = $notebookId
  Add-RunStep -RunLog $runLog -Step "create_notebook" -Status "ok" -DurationMs $createResult.elapsed_ms -OutputFile $createPath -Message $notebookId

  $addedSources = @()
  $sourceUrls = @($config.sources.urls)
  $sourceFiles = @($config.sources.files)

  $urlIndex = 0
  foreach ($url in $sourceUrls) {
    if ([string]::IsNullOrWhiteSpace([string]$url)) { continue }
    $urlIndex += 1
    $outputPath = Join-Path $rawDir ("step_add_url_{0:D2}.txt" -f $urlIndex)
    $sourceResult = Invoke-CliCapture -Name "Add URL source $urlIndex" -CapturePath $outputPath -Runner {
      notebooklm.cmd source add -w $notebookId $url
    }
    Add-RunStep -RunLog $runLog -Step ("add_url_{0:D2}" -f $urlIndex) -Status "ok" -DurationMs $sourceResult.elapsed_ms -OutputFile $outputPath -Message $url
    $addedSources += [PSCustomObject]@{ type = "url"; value = $url }
  }

  $fileIndex = 0
  foreach ($filePath in $sourceFiles) {
    if ([string]::IsNullOrWhiteSpace([string]$filePath)) { continue }
    $fileIndex += 1
    $resolvedFile = Resolve-SourcePath -PathLike $filePath -ConfigDir $configDir
    $outputPath = Join-Path $rawDir ("step_add_file_{0:D2}.txt" -f $fileIndex)
    $sourceResult = Invoke-CliCapture -Name "Add file source $fileIndex" -CapturePath $outputPath -Runner {
      notebooklm.cmd source add-file -w $notebookId $resolvedFile
    }
    Add-RunStep -RunLog $runLog -Step ("add_file_{0:D2}" -f $fileIndex) -Status "ok" -DurationMs $sourceResult.elapsed_ms -OutputFile $outputPath -Message $resolvedFile
    $addedSources += [PSCustomObject]@{ type = "file"; value = $resolvedFile }
  }

  $researchMode = if ($config.research.mode) { [string]$config.research.mode } else { "fast" }
  $autoImport = [bool]$config.research.auto_import
  $timeoutMs = if ($config.research.timeout_ms) { [int]$config.research.timeout_ms } else { 180000 }
  $researchQueries = @($config.research.queries)

  $researchOutputs = @()
  $qIndex = 0
  foreach ($query in $researchQueries) {
    if ([string]::IsNullOrWhiteSpace([string]$query)) { continue }
    $qIndex += 1
    $outputPath = Join-Path $rawDir ("step_research_{0:D2}.txt" -f $qIndex)

    $researchCmdArgs = @("research", "web", "-m", $researchMode)
    if ($autoImport) { $researchCmdArgs += "-i" }
    if ($timeoutMs -gt 0) { $researchCmdArgs += @("-t", [string]$timeoutMs) }
    $researchCmdArgs += @($notebookId, [string]$query)

    $researchResult = Invoke-CliCapture -Name "Research query $qIndex" -CapturePath $outputPath -Runner {
      & notebooklm.cmd @researchCmdArgs
    }

    Add-RunStep -RunLog $runLog -Step ("research_{0:D2}" -f $qIndex) -Status "ok" -DurationMs $researchResult.elapsed_ms -OutputFile $outputPath -Message $query
    $researchOutputs += [PSCustomObject]@{
      query = $query
      output_file = $outputPath
      output = (Extract-ResearchSummary -Text $researchResult.output)
    }
  }

  $researchMdPath = Join-Path $runDir "research.md"
  $researchSb = New-Object System.Text.StringBuilder
  [void]$researchSb.AppendLine("# Research")
  [void]$researchSb.AppendLine("")
  [void]$researchSb.AppendLine("- Topic: $topic")
  [void]$researchSb.AppendLine("- Notebook ID: $notebookId")
  [void]$researchSb.AppendLine("- Generated At: $(Get-Date -Format o)")
  [void]$researchSb.AppendLine("")
  [void]$researchSb.AppendLine("## Input Sources")
  foreach ($src in $addedSources) {
    [void]$researchSb.AppendLine("- [$($src.type)] $($src.value)")
  }
  [void]$researchSb.AppendLine("")
  [void]$researchSb.AppendLine("## Research Runs")
  foreach ($item in $researchOutputs) {
    [void]$researchSb.AppendLine("")
    [void]$researchSb.AppendLine("### Query")
    [void]$researchSb.AppendLine("")
    [void]$researchSb.AppendLine("$($item.query)")
    [void]$researchSb.AppendLine("")
    [void]$researchSb.AppendLine('```text')
    [void]$researchSb.AppendLine($item.output)
    [void]$researchSb.AppendLine('```')
  }
  Set-Content -Path $researchMdPath -Value $researchSb.ToString() -Encoding utf8
  Add-RunStep -RunLog $runLog -Step "write_research_md" -Status "ok" -OutputFile $researchMdPath

  $personaLines = @()
  foreach ($persona in @($config.debate.personas)) {
    $pName = [string]$persona.name
    $pRole = [string]$persona.role
    $pFocus = [string]$persona.focus
    if (-not [string]::IsNullOrWhiteSpace($pName)) {
      $personaLines += "- $pName | role: $pRole | focus: $pFocus"
    }
  }
  if ($personaLines.Count -eq 0) {
    $personaLines = @(
      "- Agent-A | role: Advocate | focus: Growth and upside",
      "- Agent-B | role: Skeptic | focus: Risk and constraints",
      "- Agent-C | role: Moderator | focus: Evidence and decision"
    )
  }
  $rounds = if ($config.debate.rounds) { [int]$config.debate.rounds } else { 3 }

  $researchText = Get-Content -Raw $researchMdPath
  $researchSnippet = if ($researchText.Length -gt 12000) { $researchText.Substring(0, 12000) } else { $researchText }
  $personasText = ($personaLines -join [Environment]::NewLine)
  $debatePrompt = @"
You are generating a multi-agent debate transcript for a presentation prep.

Topic: $topic
Rounds: $rounds
Personas:
$personasText

Rules:
1) Produce exactly $rounds rounds.
2) In each round, every persona must speak once.
3) Every claim should reference evidence from the provided research excerpt.
4) End with a "Decision" section and "Action Items" section.
5) Write in Korean.

Research excerpt:
$researchSnippet
"@

  $debatePromptPath = Join-Path $rawDir "prompt_claude_debate.txt"
  Set-Content -Path $debatePromptPath -Value $debatePrompt -Encoding utf8
  $debateRawPath = Join-Path $rawDir "step_claude_debate.txt"
  $debateResult = Invoke-CliCapture -Name "Claude debate generation" -CapturePath $debateRawPath -Runner {
    (Get-Content -Raw $debatePromptPath) | claude.cmd -p --output-format text --permission-mode bypassPermissions
  }
  $debateMdPath = Join-Path $runDir "debate.md"
  Set-Content -Path $debateMdPath -Value $debateResult.output -Encoding utf8
  Add-RunStep -RunLog $runLog -Step "generate_debate_md" -Status "ok" -DurationMs $debateResult.elapsed_ms -OutputFile $debateMdPath

  $reportFormat = if ($config.presentation.report_format) { [string]$config.presentation.report_format } else { "briefing" }
  $slideFormat = if ($config.presentation.slide_format) { [string]$config.presentation.slide_format } else { "presenter" }
  $slideLength = if ($config.presentation.slide_length) { [string]$config.presentation.slide_length } else { "default" }

  $reportPrompt = if ($isKoreanTarget) {
    "Write the report in Korean (ko-KR) for topic '$topic'. Format: 1) Background 2) Five key insights 3) Three risks 4) Action recommendations 5) Evidence summary."
  } else {
    "Create a concise report for topic '$topic'. Include problem framing, evidence-backed analysis, and practical recommendations."
  }
  $reportMdPath = Join-Path $runDir "final_report.md"
  $reportRawPath = Join-Path $rawDir "step_generate_report.txt"
  $reportGen = Invoke-CliCapture -Name "Generate report" -AllowFailure -CapturePath $reportRawPath -Runner {
    notebooklm.cmd generate report -w -f $reportFormat -p $reportPrompt $notebookId
  }
  $reportMatch = [regex]::Match($reportGen.output, "Artifact ID:\s*([A-Za-z0-9_-]+)")
  $reportArtifactId = if ($reportMatch.Success) { $reportMatch.Groups[1].Value } else { "" }
  if ($reportGen.exit_code -eq 0 -and -not [string]::IsNullOrWhiteSpace($reportArtifactId)) {
    $reportDownloadRawPath = Join-Path $rawDir "step_download_report.txt"
    $reportDownload = Invoke-CliCapture -Name "Download report" -CapturePath $reportDownloadRawPath -Runner {
      notebooklm.cmd generate download $notebookId $reportArtifactId $reportMdPath
    }
    Add-RunStep -RunLog $runLog -Step "generate_report" -Status "ok" -DurationMs ($reportGen.elapsed_ms + $reportDownload.elapsed_ms) -OutputFile $reportMdPath -Message $reportArtifactId
  } else {
    $reportFallbackRawPath = Join-Path $rawDir "step_report_fallback_ask.txt"
    $reportFallbackPrompt = if ($isKoreanTarget) {
      "Write a Korean (ko-KR) briefing report for topic '$topic'. Format: 1) Background 2) Five key insights 3) Three risks 4) Action recommendations 5) Evidence summary."
    } else {
      "Create a concise report for topic '$topic'. Include problem framing, evidence-backed analysis, and practical recommendations."
    }
    $reportFallback = Invoke-CliCapture -Name "NotebookLM report fallback" -CapturePath $reportFallbackRawPath -Runner {
      notebooklm.cmd ask $notebookId $reportFallbackPrompt
    }
    $reportBody = Extract-NotebookLmAnswer -Text $reportFallback.output
    Set-Content -Path $reportMdPath -Value $reportBody -Encoding utf8
    Add-RunStep -RunLog $runLog -Step "generate_report" -Status "fallback" -DurationMs ($reportGen.elapsed_ms + $reportFallback.elapsed_ms) -OutputFile $reportMdPath -Message "Artifact ID missing from NotebookLM generate report"
  }

  $slidePrompt = if ($isKoreanTarget) {
    "Generate a presentation slide deck for '$topic'. Output language must be Korean (ko-KR) only. Use 10-12 slides and include title, key points, and speaker notes per slide."
  } else {
    "Generate a presentation slide deck for '$topic'. Emphasize key insights, trade-offs, and actionable next steps."
  }
  $slideDeckBasePath = Join-Path $runDir "final_slide_deck.md"
  $slideRawPath = Join-Path $rawDir "step_generate_slides.txt"
  $slideGen = Invoke-CliCapture -Name "Generate slide deck" -AllowFailure -CapturePath $slideRawPath -Runner {
    notebooklm.cmd generate slide-deck -w -f $slideFormat -l $slideLength -p $slidePrompt $notebookId
  }
  $slideMatch = [regex]::Match($slideGen.output, "Artifact ID:\s*([A-Za-z0-9_-]+)")
  $slideArtifactId = if ($slideMatch.Success) { $slideMatch.Groups[1].Value } else { "" }
  if ($slideGen.exit_code -eq 0 -and -not [string]::IsNullOrWhiteSpace($slideArtifactId)) {
    $slideDownloadRawPath = Join-Path $rawDir "step_download_slides.txt"
    $slideDownload = Invoke-CliCapture -Name "Download slide deck" -CapturePath $slideDownloadRawPath -Runner {
      notebooklm.cmd generate download $notebookId $slideArtifactId $slideDeckBasePath
    }
    Add-RunStep -RunLog $runLog -Step "generate_slide_deck" -Status "ok" -DurationMs ($slideGen.elapsed_ms + $slideDownload.elapsed_ms) -OutputFile $slideDeckBasePath -Message $slideArtifactId
  } else {
    $slideFallbackRawPath = Join-Path $rawDir "step_slide_fallback_ask.txt"
    $slideFallbackPrompt = if ($isKoreanTarget) {
      "Create 10-12 presentation slides for '$topic' in Korean (ko-KR). For each slide include a title, three key points, and two sentences of speaker notes."
    } else {
      "Generate a presentation slide deck for '$topic'. Emphasize key insights, trade-offs, and actionable next steps."
    }
    $slideFallback = Invoke-CliCapture -Name "NotebookLM slide fallback" -CapturePath $slideFallbackRawPath -Runner {
      notebooklm.cmd ask $notebookId $slideFallbackPrompt
    }
    $slideBody = Extract-NotebookLmAnswer -Text $slideFallback.output
    Set-Content -Path $slideDeckBasePath -Value $slideBody -Encoding utf8
    Add-RunStep -RunLog $runLog -Step "generate_slide_deck" -Status "fallback" -DurationMs ($slideGen.elapsed_ms + $slideFallback.elapsed_ms) -OutputFile $slideDeckBasePath -Message "Artifact ID missing from NotebookLM generate slide-deck"
  }

  if ($isKoreanTarget) {
    $slideText = if (Test-Path -LiteralPath $slideDeckBasePath) { Get-Content -Raw $slideDeckBasePath } else { "" }
    if (-not (Test-HasKorean -Text $slideText -MinHangulChars 40)) {
      $forceKoreanPrompt = @"
Rewrite the slide deck in Korean (ko-KR) only.
Topic: $topic
Requirements:
- 10-12 slides
- Strict structure:
  **Slide N: Title**
  - Three key points
  **Speaker Notes:** Two sentences
- Do not use English sentences. Only allow unavoidable terms with brief parenthesized English.
"@
      $forceRawPath = Join-Path $rawDir "step_force_korean_slide_deck.txt"
      $forceResult = Invoke-CliCapture -Name "Force Korean slide deck" -CapturePath $forceRawPath -Runner {
        notebooklm.cmd ask $notebookId $forceKoreanPrompt
      }
      $forcedBody = Extract-NotebookLmAnswer -Text $forceResult.output
      Set-Content -Path $slideDeckBasePath -Value $forcedBody -Encoding utf8
      Add-RunStep -RunLog $runLog -Step "force_korean_slide_deck" -Status "ok" -DurationMs $forceResult.elapsed_ms -OutputFile $slideDeckBasePath -Message "Applied Korean-only fallback via notebooklm ask"
    }
  }

  $finalPrompt = @"
Create a final presentation draft in Korean using the following inputs.

Requirements:
- 8-12 slide structure
- each slide: title + 3-4 bullets + short speaker note
- include a final Q&A slide

Topic: $topic

[Report]
$(Get-Content -Raw $reportMdPath)

[Debate]
$(Get-Content -Raw $debateMdPath)
"@

  $finalPromptPath = Join-Path $rawDir "prompt_claude_final_presentation.txt"
  Set-Content -Path $finalPromptPath -Value $finalPrompt -Encoding utf8
  $finalRawPath = Join-Path $rawDir "step_claude_final_presentation.txt"
  $finalResult = Invoke-CliCapture -Name "Claude final presentation draft" -CapturePath $finalRawPath -Runner {
    (Get-Content -Raw $finalPromptPath) | claude.cmd -p --output-format text --permission-mode bypassPermissions
  }
  $finalPresentationPath = Join-Path $runDir "final_presentation.md"
  Set-Content -Path $finalPresentationPath -Value $finalResult.output -Encoding utf8
  Add-RunStep -RunLog $runLog -Step "write_final_presentation" -Status "ok" -DurationMs $finalResult.elapsed_ms -OutputFile $finalPresentationPath

  $referenceUrlPattern = "https?://[^\s\)\]]+"
  $foundUrls = New-Object System.Collections.Generic.HashSet[string]
  foreach ($u in @($sourceUrls)) {
    if (-not [string]::IsNullOrWhiteSpace([string]$u)) { [void]$foundUrls.Add([string]$u) }
  }
  foreach ($match in [regex]::Matches((Get-Content -Raw $researchMdPath), $referenceUrlPattern)) {
    [void]$foundUrls.Add($match.Value)
  }
  $referencesPath = Join-Path $runDir "references.md"
  $refSb = New-Object System.Text.StringBuilder
  [void]$refSb.AppendLine("# References")
  [void]$refSb.AppendLine("")
  [void]$refSb.AppendLine("- Captured At: $(Get-Date -Format o)")
  [void]$refSb.AppendLine("")
  [void]$refSb.AppendLine("## URLs")
  foreach ($u in $foundUrls) {
    [void]$refSb.AppendLine("- $u")
  }
  [void]$refSb.AppendLine("")
  [void]$refSb.AppendLine("## Local Files")
  foreach ($f in $sourceFiles) {
    if (-not [string]::IsNullOrWhiteSpace([string]$f)) {
      [void]$refSb.AppendLine("- $f")
    }
  }
  Set-Content -Path $referencesPath -Value $refSb.ToString() -Encoding utf8
  Add-RunStep -RunLog $runLog -Step "write_references" -Status "ok" -OutputFile $referencesPath

  $runLog.status = "completed"
  $runLog.completed_at = (Get-Date).ToString("o")
  ($runLog | ConvertTo-Json -Depth 20) | Set-Content -Path $runLogPath -Encoding utf8

  Write-Output "Assignment 2 pipeline completed."
  Write-Output "Run directory: $runDir"
  Write-Output "Notebook ID: $notebookId"
  Write-Output "Files:"
  Write-Output " - $researchMdPath"
  Write-Output " - $debateMdPath"
  Write-Output " - $reportMdPath"
  Write-Output " - $finalPresentationPath"
  Write-Output " - $referencesPath"
  Write-Output " - $runLogPath"
}
catch {
  $runLog.status = "failed"
  $runLog.failed_at = (Get-Date).ToString("o")
  $runLog.error = $_.Exception.Message
  ($runLog | ConvertTo-Json -Depth 20) | Set-Content -Path $runLogPath -Encoding utf8
  throw
}

