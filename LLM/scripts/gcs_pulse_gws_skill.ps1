param(
  [Parameter(Mandatory = $true)]
  [string]$StartAt,

  [Parameter(Mandatory = $true)]
  [string]$EndAt,

  [Parameter(Mandatory = $true)]
  [string]$Title,

  [string]$Room = "N.MR1",
  [string]$Purpose = "GCS-PULSE + GWS automation",
  [string]$Attendees = "",
  [string]$CalendarId = "primary",
  [int]$MaxRetries = 3,
  [switch]$DryRun,
  [switch]$SendInviteEmail
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Parse-Json {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $null }

  $trimmed = $Text.Trim()
  try {
    return $trimmed | ConvertFrom-Json
  } catch {
    # Some CLIs print extra log lines before/after JSON.
    $candidates = @()

    $objStart = $trimmed.IndexOf("{")
    $objEnd = $trimmed.LastIndexOf("}")
    if ($objStart -ge 0 -and $objEnd -gt $objStart) {
      $candidates += $trimmed.Substring($objStart, $objEnd - $objStart + 1)
    }

    $arrStart = $trimmed.IndexOf("[")
    $arrEnd = $trimmed.LastIndexOf("]")
    if ($arrStart -ge 0 -and $arrEnd -gt $arrStart) {
      $candidates += $trimmed.Substring($arrStart, $arrEnd - $arrStart + 1)
    }

    foreach ($candidate in $candidates) {
      try {
        return $candidate | ConvertFrom-Json
      } catch {
        continue
      }
    }

    throw
  }
}

function Invoke-ExternalJson {
  param(
    [Parameter(Mandatory = $true)][scriptblock]$Runner,
    [Parameter(Mandatory = $true)][string]$SourceName
  )

  $prevErrorAction = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $lines = & $Runner 2>&1
  } finally {
    $ErrorActionPreference = $prevErrorAction
  }

  $exitCodeVar = Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue
  $exitCode = if ($exitCodeVar) { [int]$exitCodeVar.Value } else { 0 }
  $text = ($lines -join [Environment]::NewLine).Trim()

  if ($exitCode -ne 0) {
    if ([string]::IsNullOrWhiteSpace($text)) {
      throw "$SourceName failed (exit code: $exitCode)."
    }
    throw "$SourceName failed (exit code: $exitCode): $text"
  }

  if ([string]::IsNullOrWhiteSpace($text)) {
    return $null
  }

  try {
    return Parse-Json $text
  } catch {
    throw "$SourceName returned non-JSON output: $text"
  }
}

function Invoke-GcsCli {
  param(
    [Parameter(Mandatory = $true)][string]$Command,
    [hashtable]$NamedArgs = @{}
  )

  $scriptPath = (Resolve-Path "scripts/gcs_pulse_cli_snippet.ps1").Path
  return Invoke-ExternalJson -SourceName "gcs-cli/$Command" -Runner {
    & $scriptPath -Command $Command @NamedArgs
  }
}

function Resolve-RoomId {
  param(
    [string]$RoomValue,
    [array]$Rooms
  )

  if ($RoomValue -match '^\d+$') {
    return [int]$RoomValue
  }

  $room = $Rooms | Where-Object { $_.name -eq $RoomValue } | Select-Object -First 1
  if (-not $room) {
    throw "Room '$RoomValue' not found. Use room id or exact room name."
  }
  return [int]$room.id
}

function Get-AlternativeSlots {
  param(
    [datetimeoffset]$Start,
    [datetimeoffset]$End
  )

  return @(
    @{
      start = $Start.AddMinutes(30).ToString("o")
      end = $End.AddMinutes(30).ToString("o")
    },
    @{
      start = $Start.AddMinutes(60).ToString("o")
      end = $End.AddMinutes(60).ToString("o")
    }
  )
}

function Invoke-Gws {
  param(
    [Parameter(Mandatory = $true)][string[]]$CmdArgs
  )

  return Invoke-ExternalJson -SourceName "gws/$($CmdArgs -join ' ')" -Runner {
    & gws.cmd @CmdArgs
  }
}

function Convert-ToGwsJsonArg {
  param(
    [Parameter(Mandatory = $true)][object]$Value,
    [int]$Depth = 12
  )

  $json = if ($Value -is [string]) {
    [string]$Value
  } else {
    $Value | ConvertTo-Json -Depth $Depth -Compress
  }

  # gws on Windows can split args when raw spaces remain in JSON values.
  $jsonNoSpaces = $json.Replace(" ", "\u0020")

  # gws on Windows expects embedded quotes to be escaped in CLI args.
  return $jsonNoSpaces.Replace('"', '\"')
}

function Assert-GwsAuthenticated {
  $status = Invoke-Gws -CmdArgs @("auth", "status")
  if ($null -eq $status -or -not $status.auth_method -or $status.auth_method -eq "none") {
    throw "GWS auth is not configured. Run 'gws auth setup --login' (or set GOOGLE_WORKSPACE_CLI_CLIENT_ID/SECRET and run 'gws auth login')."
  }
  return $status
}

function New-GmailRaw {
  param(
    [string]$Subject,
    [string]$Body,
    [string[]]$ToList
  )

  $mime = @(
    "To: $($ToList -join ', ')",
    "Subject: $Subject",
    "Content-Type: text/plain; charset=UTF-8",
    "",
    $Body
  ) -join "`r`n"

  $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($mime))
  return $b64.TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

$startDto = [datetimeoffset]::Parse($StartAt)
$endDto = [datetimeoffset]::Parse($EndAt)
if ($endDto -le $startDto) {
  throw "EndAt must be later than StartAt."
}

$attendeeList = @()
if (-not [string]::IsNullOrWhiteSpace($Attendees)) {
  $attendeeList = @(
    $Attendees.Split(",") |
      ForEach-Object { $_.Trim() } |
      Where-Object { $_ }
  )
}

$summary = [ordered]@{
  dry_run = [bool]$DryRun
  room = $Room
  start_at = $startDto.ToString("o")
  end_at = $endDto.ToString("o")
  gws_auth = $null
  reserved = $false
  reservation = $null
  calendar_event = $null
  invite_email = $null
  fallback_used = $false
  rollback = $null
  errors = @()
}

$createdReservationId = $null

try {
  if (-not $DryRun) {
    $summary["gws_auth"] = Assert-GwsAuthenticated
  }

  $rooms = Invoke-GcsCli -Command "rooms-list"
  if (-not $rooms) { throw "Failed to fetch room list from GCS-PULSE API." }
  $roomId = Resolve-RoomId -RoomValue $Room -Rooms $rooms
  $summary["room_id"] = $roomId

  $targetStart = $startDto.ToString("o")
  $targetEnd = $endDto.ToString("o")

  $reserveSucceeded = $false
  $attempts = @(
    @{ start = $targetStart; end = $targetEnd; fallback = $false }
  ) + (Get-AlternativeSlots -Start $startDto -End $endDto | ForEach-Object { @{ start = $_.start; end = $_.end; fallback = $true } })

  foreach ($attempt in $attempts) {
    if ($DryRun) {
      $summary["reserved"] = $true
      $summary["reservation"] = @{
        room_id = $roomId
        start_at = $attempt.start
        end_at = $attempt.end
        purpose = $Purpose
        dry_run = $true
      }
      $summary["fallback_used"] = [bool]$attempt.fallback
      $reserveSucceeded = $true
      break
    }

    try {
      $reservation = Invoke-GcsCli -Command "reserve" -NamedArgs @{
        RoomId = $roomId
        StartAt = $attempt.start
        EndAt = $attempt.end
        Purpose = $Purpose
      }

      if ($reservation -and $reservation.PSObject.Properties["id"]) {
        $createdReservationId = [int]$reservation.id
      } elseif ($reservation -and $reservation.PSObject.Properties["reservation_id"]) {
        $createdReservationId = [int]$reservation.reservation_id
      }

      $summary["reserved"] = $true
      $summary["reservation"] = $reservation
      $summary["fallback_used"] = [bool]$attempt.fallback
      $reserveSucceeded = $true
      break
    } catch {
      $summary["errors"] += "Reservation failed for slot $($attempt.start) ~ $($attempt.end): $($_.Exception.Message)"
    }
  }

  if (-not $reserveSucceeded) {
    throw "Unable to reserve room after trying base and fallback slots."
  }

  $eventStart = if ($summary.reservation.start_at) { $summary.reservation.start_at } else { $summary.start_at }
  $eventEnd = if ($summary.reservation.end_at) { $summary.reservation.end_at } else { $summary.end_at }

  $eventPayload = @{
    summary = $Title
    description = "Room: $Room / Purpose: $Purpose"
    start = @{
      dateTime = $eventStart
      timeZone = "Asia/Seoul"
    }
    end = @{
      dateTime = $eventEnd
      timeZone = "Asia/Seoul"
    }
    attendees = @($attendeeList | ForEach-Object { @{ email = $_ } })
  }

  if ($DryRun) {
    $summary["calendar_event"] = @{
      dry_run = $true
      params = @{
        calendarId = $CalendarId
        sendUpdates = "all"
      }
      body = $eventPayload
    }
  } else {
    $calendarParamsArg = Convert-ToGwsJsonArg -Value @{
      calendarId = $CalendarId
      sendUpdates = "all"
    }
    $calendarBodyArg = Convert-ToGwsJsonArg -Value $eventPayload -Depth 12

    $calendarEvent = Invoke-Gws -CmdArgs @(
      "calendar", "events", "insert",
      "--params", $calendarParamsArg,
      "--json", $calendarBodyArg
    )
    if ($calendarEvent -and $calendarEvent.PSObject.Properties["error"]) {
      throw "Calendar event creation failed: $($calendarEvent.error.message)"
    }
    $summary["calendar_event"] = $calendarEvent
  }

  if ($SendInviteEmail -and @($attendeeList).Count -gt 0) {
    $mailSubject = "[Meeting Invite] $Title"
    $mailBody = "Room: $Room`nStart: $eventStart`nEnd: $eventEnd`nPurpose: $Purpose"
    $raw = New-GmailRaw -Subject $mailSubject -Body $mailBody -ToList $attendeeList

    if ($DryRun) {
      $summary["invite_email"] = @{
        dry_run = $true
        to = $attendeeList
        subject = $mailSubject
      }
    } else {
      $gmailParamsArg = Convert-ToGwsJsonArg -Value @{ userId = "me" }
      $gmailBodyArg = Convert-ToGwsJsonArg -Value @{ raw = $raw }

      $gmailResult = Invoke-Gws -CmdArgs @(
        "gmail", "users", "messages", "send",
        "--params", $gmailParamsArg,
        "--json", $gmailBodyArg
      )
      if ($gmailResult -and $gmailResult.PSObject.Properties["error"]) {
        throw "Gmail invite failed: $($gmailResult.error.message)"
      }
      $summary["invite_email"] = $gmailResult
    }
  }
} catch {
  $summary["errors"] += $_.Exception.Message

  if (-not $DryRun -and $createdReservationId -and -not $summary.calendar_event) {
    try {
      $rollbackResult = Invoke-GcsCli -Command "cancel-reservation" -NamedArgs @{
        ReservationId = $createdReservationId
      }
      $summary["rollback"] = @{
        attempted = $true
        reservation_id = $createdReservationId
        success = $true
        result = $rollbackResult
      }
    } catch {
      $summary["rollback"] = @{
        attempted = $true
        reservation_id = $createdReservationId
        success = $false
        error = $_.Exception.Message
      }
      $summary["errors"] += "Rollback failed for reservation ${createdReservationId}: $($_.Exception.Message)"
    }
  }
}

$summary | ConvertTo-Json -Depth 12
