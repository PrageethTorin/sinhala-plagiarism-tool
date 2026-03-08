$ErrorActionPreference = "Stop"

Write-Host "Starting all services..." -ForegroundColor Cyan

# Ports:
# - Gateway (main API):           http://127.0.0.1:8000
# - WSA backend:                 http://127.0.0.1:8001
# - Paraphrase backend:           http://127.0.0.1:5000
# - Semantic similarity (optional): http://127.0.0.1:8002

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$venvPy = Join-Path $root ".venv\Scripts\python.exe"
$py = if (Test-Path $venvPy) { $venvPy } else { "python" }

Set-Location "$root"

Write-Host "Running all services in this terminal..." -ForegroundColor Green
Write-Host "Gateway endpoint: POST http://127.0.0.1:8000/api/plagiarism/analyze-file" -ForegroundColor Green
Write-Host "To also start Semantic Similarity backend: set START_SEMANTIC=1" -ForegroundColor DarkGray

& "$py" "$root\run_all.py"
