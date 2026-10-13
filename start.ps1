# Starts the API and serves the built frontend at http://localhost:8000
$root = $PSScriptRoot
$python = Join-Path $root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { Write-Error "Run the one-time setup from README.md first."; exit 1 }
if (-not (Test-Path (Join-Path $root "frontend\dist"))) {
    Write-Host "Building frontend..."
    Push-Location (Join-Path $root "frontend"); npm install; npm run build; Pop-Location
}
Set-Location (Join-Path $root "backend")
& $python -m uvicorn app.main:app --port 8000
