# =============================================================================
# NAVER WORKS Mail MCP Server Setup Script for Claude Desktop (Windows)
# =============================================================================
# Run this in PowerShell (admin not required, but recommended)
# Usage: .\setup-naverworks-mcp.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  NAVER WORKS Mail MCP Server Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Check / Install uv ────────────────────────────────────────────────
Write-Host "[1/5] uv 설치 확인..." -ForegroundColor Yellow

$uvInstalled = $null -ne (Get-Command uv -ErrorAction SilentlyContinue)
if (-not $uvInstalled) {
    Write-Host "  uv 미설치 → 지금 설치합니다..." -ForegroundColor Gray
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        # Refresh PATH in current session
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + $env:PATH
        Write-Host "  uv 설치 완료." -ForegroundColor Green
    } catch {
        Write-Host "  [오류] uv 설치 실패: $_" -ForegroundColor Red
        Write-Host "  수동 설치: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Gray
        exit 1
    }
} else {
    $uvVer = uv --version
    Write-Host "  uv 이미 설치됨: $uvVer" -ForegroundColor Green
}

# ── Step 2: Verify uvx can reach mcp-email-server ────────────────────────────
Write-Host ""
Write-Host "[2/5] mcp-email-server 패키지 확인..." -ForegroundColor Yellow
try {
    $null = uvx mcp-email-server@latest --help 2>&1
    Write-Host "  패키지 접근 가능." -ForegroundColor Green
} catch {
    Write-Host "  [경고] 패키지 확인 실패 - 네트워크 연결을 확인하세요." -ForegroundColor DarkYellow
    Write-Host "  계속 진행합니다 (첫 실행 시 Claude Desktop이 자동으로 받습니다)." -ForegroundColor Gray
}

# ── Step 3: Collect credentials securely ─────────────────────────────────────
Write-Host ""
Write-Host "[3/5] 네이버웍스 계정 정보 입력" -ForegroundColor Yellow
Write-Host "  주의: 외부 앱 비밀번호를 사용하세요 (로그인 비밀번호 X)" -ForegroundColor DarkYellow
Write-Host ""

$email = Read-Host "  네이버웍스 이메일 전체 주소 (예: yourname@company.com)"
if ([string]::IsNullOrWhiteSpace($email)) {
    Write-Host "[오류] 이메일을 입력해야 합니다." -ForegroundColor Red
    exit 1
}

$passwordSecure = Read-Host "  외부 앱 비밀번호" -AsSecureString
$passwordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($passwordSecure)
)
if ([string]::IsNullOrWhiteSpace($passwordPlain)) {
    Write-Host "[오류] 비밀번호를 입력해야 합니다." -ForegroundColor Red
    exit 1
}

# ── Step 4: Update claude_desktop_config.json ─────────────────────────────────
Write-Host ""
Write-Host "[4/5] Claude Desktop 설정 파일 업데이트..." -ForegroundColor Yellow

$configDir  = "$env:APPDATA\Claude"
$configPath = "$configDir\claude_desktop_config.json"

# Ensure config directory exists
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    Write-Host "  설정 폴더 생성: $configDir" -ForegroundColor Gray
}

# Load existing config or start fresh
if (Test-Path $configPath) {
    $backupPath = "$configPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $configPath $backupPath
    Write-Host "  기존 설정 백업: $backupPath" -ForegroundColor Gray
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
} else {
    Write-Host "  새 설정 파일 생성." -ForegroundColor Gray
    $config = [PSCustomObject]@{}
}

# Ensure mcpServers key exists
if (-not ($config.PSObject.Properties.Name -contains "mcpServers")) {
    $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value ([PSCustomObject]@{})
}

# Build the NAVER WORKS MCP entry
$naverwWorksEntry = [PSCustomObject]@{
    command = "uvx"
    args    = @("mcp-email-server@latest", "stdio")
    env     = [PSCustomObject]@{
        MCP_EMAIL_SERVER_IMAP_HOST = "imap.worksmobile.com"
        MCP_EMAIL_SERVER_IMAP_PORT = "993"
        MCP_EMAIL_SERVER_SMTP_HOST = "smtp.worksmobile.com"
        MCP_EMAIL_SERVER_SMTP_PORT = "465"
        MCP_EMAIL_SERVER_USER_NAME = $email
        MCP_EMAIL_SERVER_PASSWORD  = $passwordPlain
    }
}

# Add / overwrite the naverworks-email entry
if ($config.mcpServers.PSObject.Properties.Name -contains "naverworks-email") {
    $config.mcpServers.PSObject.Properties.Remove("naverworks-email")
    Write-Host "  기존 naverworks-email 항목 덮어씁니다." -ForegroundColor Gray
}
$config.mcpServers | Add-Member -MemberType NoteProperty -Name "naverworks-email" -Value $naverwWorksEntry

# Write back
$config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
Write-Host "  설정 저장 완료: $configPath" -ForegroundColor Green

# ── Step 5: Restrict file permissions (icacls) ────────────────────────────────
Write-Host ""
Write-Host "[5/5] 파일 권한 제한 (비밀번호 평문 보호)..." -ForegroundColor Yellow

$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Remove inheritance, then grant only current user
icacls $configPath /inheritance:r /grant:r "${currentUser}:(R,W)" /q
if ($LASTEXITCODE -eq 0) {
    Write-Host "  권한 설정 완료 - 현재 사용자만 읽기/쓰기 가능." -ForegroundColor Green
} else {
    Write-Host "  [경고] 권한 설정 실패 - 수동으로 설정하세요." -ForegroundColor DarkYellow
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  설정 완료!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  다음 단계:" -ForegroundColor White
Write-Host "  1. Claude Desktop을 완전히 종료하고 다시 시작하세요." -ForegroundColor White
Write-Host "  2. 새 대화에서 다음을 입력해 확인:" -ForegroundColor White
Write-Host '     "내 이메일 받은 편지함에서 최근 5개 메일을 보여줘"' -ForegroundColor Cyan
Write-Host "  3. naverworks-email 도구가 목록에 보이면 성공입니다." -ForegroundColor White
Write-Host ""
Write-Host "  보안 주의사항:" -ForegroundColor DarkYellow
Write-Host "  - 설정 파일 경로: $configPath" -ForegroundColor Gray
Write-Host "  - 이 파일을 git에 커밋하거나 공유하지 마세요." -ForegroundColor Gray
Write-Host "  - 백업 파일도 같은 경로에 있으니 주의하세요." -ForegroundColor Gray
Write-Host ""
