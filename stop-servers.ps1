# Chanho Playground - Stop Servers
Write-Host "========================================"
Write-Host "  Chanho Playground - Server Stop"
Write-Host "========================================"
Write-Host ""

# Find and kill processes on port 8000 (Backend)
$backend = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($backend) {
    Write-Host "Stopping Backend server (PID: $backend)"
    Stop-Process -Id $backend -Force -ErrorAction SilentlyContinue
}

# Find and kill processes on port 3000 (Frontend)
$frontend = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($frontend) {
    Write-Host "Stopping Frontend server (PID: $frontend)"
    Stop-Process -Id $frontend -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================"
Write-Host "  All servers stopped."
Write-Host "========================================"
