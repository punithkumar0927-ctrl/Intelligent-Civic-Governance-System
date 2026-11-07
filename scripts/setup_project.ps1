# scripts/setup_project.ps1
# One-time setup for NEXUS AI on Windows
$ErrorActionPreference = "Stop"
Write-Host "=== NEXUS AI Setup ===" -ForegroundColor Cyan

# 1. Check Python
try { python --version } catch { Write-Host "Python 3.10+ not found. Install from python.org" -ForegroundColor Red; exit 1 }

# 2. Check Node.js
try { node --version } catch { Write-Host "Node.js 18+ not found. Install from nodejs.org" -ForegroundColor Red; exit 1 }

# 3. Create Python virtual environment
$venvPath = ".\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}
& "$venvPath\Scripts\Activate.ps1"

# 4. Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r backend\requirements.txt

# 5. Install frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

# 6. Create storage directories
$dirs = @(
    "storage\uploads", "storage\processed_images", "storage\thumbnails", "storage\temporary",
    "datasets\road_damage\images\train", "datasets\road_damage\images\val", "datasets\road_damage\images\test",
    "datasets\road_damage\labels\train", "datasets\road_damage\labels\val", "datasets\road_damage\labels\test",
    "ai_engine\models\detection", "ai_engine\models\severity", "ai_engine\models\embeddings"
)
foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
Write-Host "Storage directories ready." -ForegroundColor Green

# 7. Copy .env.example -> .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example - edit before running!" -ForegroundColor Yellow
} else {
    Write-Host ".env already exists, skipping." -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Start PostgreSQL (or run: docker-compose up db -d)"
Write-Host "2. Edit .env and set DATABASE_URL"
Write-Host "3. Run: python database\seed_data.py"
Write-Host "4. Start backend:  .\scripts\run_backend.ps1"
Write-Host "5. Start frontend: cd frontend; npm run dev"
Write-Host "6. Open http://localhost:5173"
Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
