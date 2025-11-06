# PowerShell script for deploying agent to LiveKit Cloud
# Usage: .\deploy_livekit_cloud.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying Agent to LiveKit Cloud" -ForegroundColor Green
Write-Host ""

# Check if LiveKit CLI is installed
try {
    $null = lk --version 2>&1
    Write-Host "✅ LiveKit CLI ready" -ForegroundColor Green
} catch {
    Write-Host "❌ LiveKit CLI not found!" -ForegroundColor Red
    Write-Host "Installing LiveKit CLI..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "LiveKit CLI is NOT a pip package!" -ForegroundColor Yellow
    Write-Host "Please install it using one of these methods:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1 (Recommended):" -ForegroundColor Cyan
    Write-Host "  winget install LiveKit.LiveKitCLI" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 2: Download from GitHub:" -ForegroundColor Cyan
    Write-Host "  https://github.com/livekit/livekit-cli/releases" -ForegroundColor White
    Write-Host ""
    Write-Host "After installation, run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check if logged in
try {
    $null = lk cloud whoami 2>&1
    Write-Host "✅ Authenticated with LiveKit Cloud" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Not logged in to LiveKit Cloud" -ForegroundColor Yellow
    Write-Host "Please login:" -ForegroundColor Yellow
    lk cloud login
}

Write-Host ""

# Check for required files
Write-Host "Checking required files..." -ForegroundColor Yellow

$requiredFiles = @("agent.py", "livekit-agent.yaml", "requirements.txt")

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ $file not found!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ All required files found" -ForegroundColor Green
Write-Host ""

# Check for entrypoint function
$agentContent = Get-Content agent.py -Raw
if ($agentContent -notmatch "async def entrypoint") {
    Write-Host "❌ entrypoint function not found in agent.py!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Entrypoint function found" -ForegroundColor Green
Write-Host ""

# Check environment variables
Write-Host "Checking environment variables..." -ForegroundColor Yellow

if (-not $env:OPENAI_API_KEY) {
    Write-Host "⚠️  OPENAI_API_KEY not set in environment" -ForegroundColor Yellow
    Write-Host "Make sure to set it in LiveKit Cloud dashboard!" -ForegroundColor Yellow
}

Write-Host "✅ Environment check complete" -ForegroundColor Green
Write-Host ""

# Deploy
Write-Host "📦 Deploying agent to LiveKit Cloud..." -ForegroundColor Green
Write-Host ""

lk cloud deploy agent --config livekit-agent.yaml

Write-Host ""
Write-Host "════════════════════════════════════════" -ForegroundColor Green
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Check agent status in LiveKit Cloud dashboard"
Write-Host "2. View logs: lk cloud logs agent"
Write-Host "3. Test by calling your Twilio number"
Write-Host ""
Write-Host "════════════════════════════════════════" -ForegroundColor Green

