# Cloudflare Tunnel for social-dance.org
# Uses authenticated account with reliable, stable named tunnel

Write-Host "Starting Cloudflare tunnel for social-dance.org..." -ForegroundColor Green
Write-Host "Local service: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Public URL: https://social-dance.org" -ForegroundColor Cyan
Write-Host ""

$cloudflareDir = "c:\Users\frash\OneDrive\Documents\PythonBasics\cloudflare"
Set-Location $cloudflareDir

# Run the named tunnel with config
Write-Host "Connecting with your Cloudflare account..." -ForegroundColor Yellow
& ".\cloudflared.exe" tunnel --config config.yml run social-dance-app


