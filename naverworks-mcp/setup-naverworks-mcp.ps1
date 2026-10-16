# =============================================================================
# NAVER WORKS Mail MCP Server Setup for Claude Desktop (Windows)
# =============================================================================
# Package: yunfeizhu/mcp-mail-server (24 tools — read, send, reply, search,
#          attachments, threading)
# Verified: Linux sandbox에서 패키지 다운로드 + stdio 초기화 + tools/list 24개
#           응답 확인 (2026-06-02)
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  NAVER WORKS Mail MCP Setup (mcp-mail-server)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Check / Install Node.js ──────────────────────────────────────────
Write-Host "[1/5] Node.js / npx 설치 확인..." -ForegroundColor Yellow

$nodeInstalled = $null -ne (Get-Command node -ErrorAction SilentlyContinue)
if (-not $nodeInstalled) {
    Write-Host "  Node.js 미설치 → winget으로 설치합니다..." -ForegroundColor Gray
    try {
        winget install OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH", "User")
        Write-Host "  Node.js 설치 완료." -ForegroundColor Green
    } catch {
        Write-Host "  [오류] Node.js 설치 실패. https://nodejs.org/ 에서 수동 설치하세요." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  Node.js $(node --version) / npx $(npx --version) 확인됨." -ForegroundColor Green
}

# ── Step 2: Pre-fetch the package ─────────────────────────────────────────────
Write-Host ""
Write-Host "[2/5] mcp-mail-server 패키지 사전 다운로드..." -ForegroundColor Yellow
try {
    $null = npx -y mcp-mail-server@latest --version 2>&1
    Write-Host "  패키지 다운로드 완료." -ForegroundColor Green
} catch {
    Write-Host "  [경고] 사전 다운로드 실패. Claude Desktop 첫 실행 시 자동 다운로드됩니다." -ForegroundColor DarkYellow
}

# ── Step 3: Collect credentials ──────────────────────────────────────────────
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
$passwordPlain  = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
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

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    Write-Host "  설정 폴더 생성: $configDir" -ForegroundColor Gray
}

if (Test-Path $configPath) {
    $backupPath = "$configPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $configPath $backupPath
    Write-Host "  기존 설정 백업: $backupPath" -ForegroundColor Gray
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
} else {
    Write-Host "  새 설정 파일 생성." -ForegroundColor Gray
    $config = [PSCustomObject]@{}
}

if (-not ($config.PSObject.Properties.Name -contains "mcpServers")) {
    $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value ([PSCustomObject]@{})
}

$entry = [PSCustomObject]@{
    command = "npx"
    args    = @("-y", "mcp-mail-server@latest")
    env     = [PSCustomObject]@{
        IMAP_HOST   = "imap.worksmobile.com"
        IMAP_PORT   = "993"
        IMAP_SECURE = "true"
        SMTP_HOST   = "smtp.worksmobile.com"
        SMTP_PORT   = "465"
        SMTP_SECURE = "true"
        EMAIL_USER  = $email
        EMAIL_PASS  = $passwordPlain
    }
}

if ($config.mcpServers.PSObject.Properties.Name -contains "naverworks-mail") {
    $config.mcpServers.PSObject.Properties.Remove("naverworks-mail")
    Write-Host "  기존 naverworks-mail 항목 덮어씁니다." -ForegroundColor Gray
}
$config.mcpServers | Add-Member -MemberType NoteProperty -Name "naverworks-mail" -Value $entry

$config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
Write-Host "  설정 저장 완료: $configPath" -ForegroundColor Green

# ── Step 5: Restrict file permissions ─────────────────────────────────────────
Write-Host ""
Write-Host "[5/5] 파일 권한 제한 (비밀번호 평문 보호)..." -ForegroundColor Yellow

$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls $configPath /inheritance:r /grant:r "${currentUser}:(R,W)" /q | Out-Null
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
Write-Host "  1. Claude Desktop을 작업표시줄에서 완전히 종료 (트레이 포함)" -ForegroundColor White
Write-Host "  2. Claude Desktop 다시 시작" -ForegroundColor White
Write-Host "  3. 새 대화에서 다음을 입력해 확인:" -ForegroundColor White
Write-Host '     "내 메일 받은 편지함 최근 5개 보여줘"' -ForegroundColor Cyan
Write-Host ""
Write-Host "  사용 가능한 24개 도구:" -ForegroundColor White
Write-Host "  - 읽기/검색: 발신자/수신자/제목/본문/날짜/키워드/읽지 않음" -ForegroundColor Gray
Write-Host "  - 발송: send_email, reply_to_email (스레드 자동 유지)" -ForegroundColor Gray
Write-Host "  - 첨부파일: 메타데이터 조회, 다운로드/저장" -ForegroundColor Gray
Write-Host "  - 관리: 폴더 목록, 메시지 삭제, 연결 상태 확인" -ForegroundColor Gray
Write-Host ""
Write-Host "  보안 주의사항:" -ForegroundColor DarkYellow
Write-Host "  - 설정 파일: $configPath" -ForegroundColor Gray
Write-Host "  - 이 파일을 git에 커밋하거나 공유하지 마세요." -ForegroundColor Gray
Write-Host "  - 발송은 항상 사람이 내용을 확인하는 워크플로우를 권장합니다." -ForegroundColor Gray
Write-Host ""
