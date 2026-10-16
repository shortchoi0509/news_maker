# =============================================================================
# Install the patched mcp-mail-server (with headers_only / max_body_length)
# and switch claude_desktop_config.json to use it.
#
# Run this AFTER cloning the news_maker repo to your PC.
# Run from this folder (naverworks-mcp/):
#   powershell -ExecutionPolicy Bypass -File .\install-patched.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Patched mcp-mail-server installer" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$serverDir = Join-Path $PSScriptRoot "server"
$entry     = Join-Path $serverDir "dist\index.js"

if (-not (Test-Path $entry)) {
    Write-Host "[오류] $entry 가 없습니다. 저장소를 다시 받으세요." -ForegroundColor Red
    exit 1
}

# 1) Install runtime dependencies (skip dev deps)
Write-Host "`n[1/3] 의존성 설치 (production)..." -ForegroundColor Yellow
Push-Location $serverDir
try {
    npm install --omit=dev --no-audit --no-fund 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [오류] npm install 실패 (code=$LASTEXITCODE)" -ForegroundColor Red
        Pop-Location
        exit 1
    }
} finally {
    Pop-Location
}
Write-Host "  설치 완료." -ForegroundColor Green

# 2) Locate the real Claude Desktop config (MSIX virtual store)
Write-Host "`n[2/3] Claude Desktop 설정 파일 찾기..." -ForegroundColor Yellow

$candidates = @(
    "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json",
    "$env:APPDATA\Claude\claude_desktop_config.json"
)
$cfgPath = $null
foreach ($p in $candidates) {
    if (Test-Path $p) { $cfgPath = $p; break }
}
if (-not $cfgPath) {
    Write-Host "[오류] claude_desktop_config.json을 찾을 수 없습니다." -ForegroundColor Red
    exit 1
}
Write-Host "  발견: $cfgPath" -ForegroundColor Gray

# 3) Update mcpServers.naverworks-mail to point at our patched build
Write-Host "`n[3/3] 설정 갱신 (백업 후 병합)..." -ForegroundColor Yellow

Copy-Item $cfgPath "$cfgPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

$cfg = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not ($cfg.PSObject.Properties.Name -contains "mcpServers")) {
    $cfg | Add-Member NoteProperty mcpServers ([PSCustomObject]@{})
}

$existing = $null
if ($cfg.mcpServers.PSObject.Properties.Name -contains "naverworks-mail") {
    $existing = $cfg.mcpServers.'naverworks-mail'
}

if (-not $existing -or -not $existing.env -or -not $existing.env.EMAIL_USER) {
    Write-Host "[오류] 기존 naverworks-mail 항목에 EMAIL_USER/EMAIL_PASS가 없습니다." -ForegroundColor Red
    Write-Host "       먼저 setup-naverworks-mcp.ps1을 실행해 자격증명을 등록하세요." -ForegroundColor Red
    exit 1
}

$newEntry = [PSCustomObject]@{
    command = "cmd"
    args    = @("/c", "node", $entry)
    env     = $existing.env
}

$cfg.mcpServers.PSObject.Properties.Remove("naverworks-mail")
$cfg.mcpServers | Add-Member NoteProperty naverworks-mail $newEntry

$json = $cfg | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText($cfgPath, $json, [System.Text.UTF8Encoding]::new($false))

# Reapply permissions
$me = [Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls $cfgPath /inheritance:r /grant:r "${me}:(R,W)" /q | Out-Null

Write-Host "  설정 갱신 완료." -ForegroundColor Green
Write-Host "    command : cmd /c node $entry" -ForegroundColor Gray
Write-Host "    env     : (이메일/비밀번호 기존 값 유지)" -ForegroundColor Gray

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  완료!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  다음:" -ForegroundColor White
Write-Host "  1. Claude Desktop을 완전히 종료 후 재시작" -ForegroundColor White
Write-Host "  2. 설정 → 개발자 → 로컬 MCP 서버에서 naverworks-mail이 running인지 확인" -ForegroundColor White
Write-Host "  3. Chat에서 테스트:" -ForegroundColor White
Write-Host '     "get_recent_messages로 INBOX 최근 30개 메일을 headers_only=true로 가져와줘"' -ForegroundColor Cyan
Write-Host ""
Write-Host "  새 기능:" -ForegroundColor White
Write-Host "  - headers_only=true : 본문/첨부 빼고 메타데이터만 → 100건도 한번에" -ForegroundColor Gray
Write-Host "  - max_body_length=500 : 본문을 500자로 잘라서 토큰 절약" -ForegroundColor Gray
Write-Host ""
