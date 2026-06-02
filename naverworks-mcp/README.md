# NAVER WORKS Mail MCP Setup

Claude Desktop에서 네이버웍스 메일을 읽고 쓸 수 있게 하는 MCP 서버 설정 스크립트입니다.

## 사용법

### 1. 스크립트 다운로드

이 폴더의 파일 두 개를 Windows로 복사합니다:
- `setup-naverworks-mcp.ps1`
- `test-connection.ps1`

### 2. PowerShell에서 실행

```powershell
# 먼저 네트워크 연결 확인
.\test-connection.ps1

# 메인 설정 스크립트 실행
.\setup-naverworks-mcp.ps1
```

> **PowerShell 실행 정책 오류가 나면:**
> ```powershell
> powershell -ExecutionPolicy Bypass -File .\setup-naverworks-mcp.ps1
> ```

### 3. 스크립트가 하는 일

1. `uv` 패키지 매니저 자동 설치 (없을 경우)
2. 네이버웍스 이메일 주소와 외부 앱 비밀번호 입력 받기
3. `%APPDATA%\Claude\claude_desktop_config.json` 업데이트
4. 기존 설정 자동 백업
5. `icacls`로 파일 권한 제한 (본인만 접근 가능)

### 4. Claude Desktop 재시작 후 테스트

새 대화에서 입력:
```
내 받은 편지함에서 최근 5개 메일 제목을 보여줘
```

## 사전 요구사항

| 항목 | 확인 방법 |
|------|-----------|
| Git | `git --version` |
| uv | 스크립트가 자동 설치 |
| Claude Desktop | 설치되어 있어야 함 |
| 네이버웍스 외부 앱 비밀번호 | 네이버웍스 관리자 콘솔 → 보안 → 외부 앱 비밀번호 |

## 메일 서버 정보

| 항목 | 값 |
|------|----|
| IMAP 호스트 | `imap.worksmobile.com` |
| IMAP 포트 | `993` (SSL) |
| SMTP 호스트 | `smtp.worksmobile.com` |
| SMTP 포트 | `465` (SSL) |

## 보안 주의사항

- `claude_desktop_config.json`에 비밀번호가 평문으로 저장됨
- 이 파일을 git에 커밋하거나 공유하지 말 것
- 스크립트가 icacls로 파일 권한을 자동 제한함
- 메일 발송 전 항상 사람이 내용을 확인하는 습관 권장

## 제공되는 MCP 도구

`mcp-email-server` 패키지가 제공하는 기능:

- 메일 읽기 (받은 편지함, 폴더 지정)
- 메일 검색
- 메일 발송
- 메일 답장 (스레드 유지)
- 첨부파일 다운로드
- 폴더 관리
