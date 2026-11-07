# scripts/run_backend.ps1
$ErrorActionPreference = "Stop"
Write-Host "=== NEXUS AI Backend ===" -ForegroundColor Cyan

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
    Write-Host "Virtual env activated" -ForegroundColor Green
}

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^(.*?)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
    Write-Host ".env loaded" -ForegroundColor Green
}

$port = if ($args.Count -gt 0) { $args[0] } else { 8000 }
Write-Host "FastAPI: http://localhost:$port | Docs: http://localhost:$port/docs" -ForegroundColor Yellow

Push-Location backend
uvicorn app.main:app --reload --host "0.0.0.0" --port $port --log-level info
Pop-Location
