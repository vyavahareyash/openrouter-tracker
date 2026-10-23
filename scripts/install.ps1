# ==============================================================================
# OpenRouter Tracker - Automated Windows Installer
# No git clone or manual build required.
#
# Usage (run in PowerShell):
#   irm https://raw.githubusercontent.com/vyavahareyash/openrouter-tracker/main/scripts/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"

$Repo = "vyavahareyash/openrouter-tracker"
$InstallDir = "$env:LOCALAPPDATA\Programs\OpenRouterTracker"
$ExePath = "$InstallDir\OpenRouterTracker.exe"
$StartMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$ShortcutPath = "$StartMenuDir\OpenRouter Tracker.lnk"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       Installing OpenRouter Tracker for Windows        " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Fetch latest release info from GitHub API
Write-Host "🔍 [1/4] Checking latest release from GitHub ($Repo)..." -ForegroundColor Yellow
$ApiUrl = "https://api.github.com/repos/$Repo/releases/latest"

try {
    $Release = Invoke-RestMethod -Uri $ApiUrl -Headers @{ "User-Agent" = "PowerShell" }
    $TagName = $Release.tag_name
    Write-Host "   Found release: $TagName" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Could not query GitHub API for releases, falling back to direct download link." -ForegroundColor DarkYellow
    $TagName = "latest"
}

# 2. Prepare installation directory
Write-Host "📁 [2/4] Setting up directory: $InstallDir" -ForegroundColor Yellow
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# 3. Download the standalone executable
Write-Host "⬇️  [3/4] Downloading OpenRouterTracker.exe..." -ForegroundColor Yellow
$DownloadUrl = "https://github.com/$Repo/releases/download/$TagName/OpenRouterTracker.exe"
$FallbackZipUrl = "https://github.com/$Repo/releases/download/$TagName/OpenRouterTracker-windows-x64.zip"

$Downloaded = $false
try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ExePath -UseBasicParsing
    $Downloaded = $true
} catch {
    # If direct exe is not present, try zip
    try {
        $ZipPath = "$InstallDir\package.zip"
        Invoke-WebRequest -Uri $FallbackZipUrl -OutFile $ZipPath -UseBasicParsing
        Expand-Archive -Path $ZipPath -DestinationPath $InstallDir -Force
        Remove-Item $ZipPath -Force
        $Downloaded = $true
    } catch {
        Write-Host "❌ Could not download release binary. Please ensure a GitHub Release has been published." -ForegroundColor Red
        exit 1
    }
}

# 4. Create Windows Start Menu Shortcut
Write-Host "🔗 [4/4] Creating Start Menu shortcut..." -ForegroundColor Yellow
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $ExePath
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "OpenRouter Desktop Tracker & Widget"
    $Shortcut.Save()
    Write-Host "   Shortcut created at: $ShortcutPath" -ForegroundColor Green
} catch {
    Write-Host "   (Skipped shortcut creation)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✨ Successfully Installed OpenRouter Tracker!" -ForegroundColor Green
Write-Host "   Executable location: $ExePath" -ForegroundColor Gray
Write-Host ""

$Launch = Read-Host "Would you like to start OpenRouter Tracker now? (Y/n)"
if ($Launch -ne 'n' -and $Launch -ne 'N') {
    Start-Process -FilePath $ExePath
}
