$ErrorActionPreference = "Stop"

Write-Host "Starting all services..." -ForegroundColor Cyan

# Ports:
# - Old combined backend:          http://127.0.0.1:5000
# - Isolated Gateway:              http://127.0.0.1:8000
# - Isolated WSA backend:          http://127.0.0.1:8001
# - Isolated Paraphrase backend:   http://127.0.0.1:5001
# - Isolated Semantic backend:     http://127.0.0.1:8002

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$venvPy = Join-Path $root ".venv\Scripts\python.exe"
$py = if (Test-Path $venvPy) { $venvPy } else { "python" }

Set-Location "$root"

Write-Host "Running backend/server.py in this terminal..." -ForegroundColor Green
Write-Host "Old combined backend: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Isolated plagiarism gateway: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "server.py starts run_all.py for the isolated plagiarism stack." -ForegroundColor DarkGray

& "$py" "$root\backend\server.py"
