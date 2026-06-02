# =============================================================================
# NAVER WORKS IMAP/SMTP 연결 테스트 스크립트
# =============================================================================
# 실행 전 setup-naverworks-mcp.ps1을 먼저 실행하세요.
# =============================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  NAVER WORKS 연결 테스트" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── IMAP 포트 연결 테스트 (TCP 수준) ─────────────────────────────────────────
Write-Host "[1/2] IMAP 서버 연결 테스트 (imap.worksmobile.com:993)..." -ForegroundColor Yellow
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $connect = $tcp.BeginConnect("imap.worksmobile.com", 993, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(5000, $false)
    if ($wait -and $tcp.Connected) {
        Write-Host "  IMAP 연결 성공." -ForegroundColor Green
    } else {
        Write-Host "  [실패] IMAP 연결 불가 - 방화벽 또는 네트워크 확인 필요." -ForegroundColor Red
    }
    $tcp.Close()
} catch {
    Write-Host "  [오류] $_" -ForegroundColor Red
}

# ── SMTP 포트 연결 테스트 (TCP 수준) ─────────────────────────────────────────
Write-Host ""
Write-Host "[2/2] SMTP 서버 연결 테스트 (smtp.worksmobile.com:465)..." -ForegroundColor Yellow
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $connect = $tcp.BeginConnect("smtp.worksmobile.com", 465, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(5000, $false)
    if ($wait -and $tcp.Connected) {
        Write-Host "  SMTP 연결 성공." -ForegroundColor Green
    } else {
        Write-Host "  [실패] SMTP 연결 불가 - 방화벽 또는 네트워크 확인 필요." -ForegroundColor Red
    }
    $tcp.Close()
} catch {
    Write-Host "  [오류] $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "  TCP 레벨 연결만 확인합니다. 인증 테스트는 Claude Desktop에서 확인하세요." -ForegroundColor Gray
Write-Host ""
