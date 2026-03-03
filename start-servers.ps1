# Chanho Playground - Start Servers
Write-Host "========================================"
Write-Host "  Chanho Playground - Server Start"
Write-Host "========================================"
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Backend server (background job)
Write-Host "[1/2] Starting Backend server... (port 8000)"
$backend = Start-Job -ScriptBlock {
    param($path)
    Set-Location "$path\backend"
    python main.py
} -ArgumentList $scriptPath

# Wait for backend to start
Start-Sleep -Seconds 2

# Frontend server with live reload (background job)
Write-Host "[2/2] Starting Frontend server with live reload... (port 3000)"
$frontend = Start-Job -ScriptBlock {
    param($path)
    Set-Location "$path\frontend"
    npx live-server --port=3000 --no-browser
} -ArgumentList $scriptPath

Write-Host ""
Write-Host "========================================"
Write-Host "  Servers started!"
Write-Host "========================================"
Write-Host ""
Write-Host "  - Backend:  http://localhost:8000"
Write-Host "  - Frontend: http://localhost:3000"
Write-Host "  - API Docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "  Press Ctrl+C to stop servers."
Write-Host "========================================"

# Wait and show logs
try {
    while ($true) {
        Receive-Job -Job $backend, $frontend 2>&1 | Write-Host
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nStopping servers..."
    Stop-Job -Job $backend, $frontend -ErrorAction SilentlyContinue
    Remove-Job -Job $backend, $frontend -Force -ErrorAction SilentlyContinue
}
