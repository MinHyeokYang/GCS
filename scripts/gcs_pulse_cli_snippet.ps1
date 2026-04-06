param(
  [Parameter(Mandatory = $true, Position = 0)]
  [ValidateSet("rooms-list", "reservations-list", "reserve", "cancel-reservation", "create-daily-snippet")]
  [string]$Command,

  [int]$RoomId,
  [string]$Date,
  [string]$StartAt,
  [string]$EndAt,
  [string]$Purpose,
  [int]$ReservationId,
  [string]$Content
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-BaseUrl {
  if ($env:GCS_PULSE_API_BASE_URL) { return $env:GCS_PULSE_API_BASE_URL.TrimEnd("/") }
  return "https://api.1000.school"
}

function Get-Token {
  if ($env:GCS_PULSE_TOKEN) { return $env:GCS_PULSE_TOKEN }
  if ($env:ANTHROPIC_AUTH_TOKEN) { return $env:ANTHROPIC_AUTH_TOKEN }
  throw "Missing token. Set GCS_PULSE_TOKEN (or ANTHROPIC_AUTH_TOKEN)."
}

function Invoke-GcsApi {
  param(
    [string]$Method,
    [string]$Path,
    [object]$Body = $null
  )

  $baseUrl = Get-BaseUrl
  $token = Get-Token
  $uri = "$baseUrl$Path"

  $headers = @{
    Authorization = "Bearer $token"
    Accept = "application/json"
  }

  if ($null -eq $Body) {
    return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers
  }

  $jsonBody = $Body | ConvertTo-Json -Depth 12
  $headers["Content-Type"] = "application/json"
  return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers -Body $jsonBody
}

switch ($Command) {
  "rooms-list" {
    $result = Invoke-GcsApi -Method "GET" -Path "/meeting-rooms"
    if ($null -eq $result -or @($result).Count -eq 0) {
      "[]"
    } else {
      @($result) | ConvertTo-Json -Depth 12
    }
    break
  }
  "reservations-list" {
    if (-not $RoomId) { throw "reservations-list requires -RoomId" }
    if (-not $Date) { throw "reservations-list requires -Date (YYYY-MM-DD)" }
    $result = Invoke-GcsApi -Method "GET" -Path "/meeting-rooms/$RoomId/reservations?date=$Date"
    if ($null -eq $result -or @($result).Count -eq 0) {
      "[]"
    } else {
      @($result) | ConvertTo-Json -Depth 12
    }
    break
  }
  "reserve" {
    if (-not $RoomId) { throw "reserve requires -RoomId" }
    if (-not $StartAt) { throw "reserve requires -StartAt (ISO 8601)" }
    if (-not $EndAt) { throw "reserve requires -EndAt (ISO 8601)" }

    $payload = @{
      start_at = $StartAt
      end_at = $EndAt
    }
    if ($Purpose) { $payload["purpose"] = $Purpose }

    $result = Invoke-GcsApi -Method "POST" -Path "/meeting-rooms/$RoomId/reservations" -Body $payload
    $result | ConvertTo-Json -Depth 12
    break
  }
  "cancel-reservation" {
    if (-not $ReservationId) { throw "cancel-reservation requires -ReservationId" }
    $result = Invoke-GcsApi -Method "DELETE" -Path "/meeting-rooms/reservations/$ReservationId"
    $result | ConvertTo-Json -Depth 12
    break
  }
  "create-daily-snippet" {
    if (-not $Content) { throw "create-daily-snippet requires -Content" }
    $result = Invoke-GcsApi -Method "POST" -Path "/daily-snippets" -Body @{ content = $Content }
    $result | ConvertTo-Json -Depth 12
    break
  }
  default {
    throw "Unsupported command: $Command"
  }
}
