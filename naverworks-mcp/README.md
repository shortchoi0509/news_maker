# NAVER WORKS Mail MCP Setup

Claude Desktop에서 네이버웍스 메일을 읽고 발송할 수 있게 하는 MCP 서버 설정.

## 사용 패키지

[`yunfeizhu/mcp-mail-server`](https://github.com/yunfeizhu/mcp-mail-server)
(npm: `mcp-mail-server`) — TypeScript 기반 IMAP/SMTP MCP 서버.
**Linux 샌드박스에서 직접 검증 완료** (2026-06-02): 패키지 다운로드 →
stdio 초기화 → `tools/list` 24개 도구 응답 확인.

## 사용법

### 1. 파일 두 개를 Windows로 복사

- `setup-naverworks-mcp.ps1`
- `test-connection.ps1`

### 2. PowerShell에서 실행

```powershell
# 네트워크 연결 사전 확인
powershell -ExecutionPolicy Bypass -File .\test-connection.ps1

# 메인 설정 (이메일 + 외부 앱 비밀번호 입력 받음)
powershell -ExecutionPolicy Bypass -File .\setup-naverworks-mcp.ps1
```

### 3. Claude Desktop 완전히 종료 후 재시작

작업표시줄 트레이 아이콘까지 닫고 다시 실행.

### 4. 테스트

새 대화에서:
```
내 메일 받은 편지함 최근 5개 보여줘
```

## 스크립트가 하는 일

1. Node.js 자동 설치 (winget, 없을 경우)
2. `mcp-mail-server` 패키지 사전 다운로드
3. 네이버웍스 이메일 + 외부 앱 비밀번호 입력 받기 (`-AsSecureString`)
4. `%APPDATA%\Claude\claude_desktop_config.json` 갱신 (기존 설정 자동 백업/병합)
5. `icacls`로 파일 권한 제한 (본인만 읽기/쓰기)

## 메일 서버 정보

| 항목 | 값 |
|------|----|
| IMAP | `imap.worksmobile.com:993` (SSL) |
| SMTP | `smtp.worksmobile.com:465` (SSL) |
| 인증 | 외부 앱 비밀번호 |

## 제공되는 24개 MCP 도구

### 연결/상태
- `connect_all`, `disconnect_all`, `get_connection_status`

### 폴더/메시지 카운트
- `list_mailboxes`, `open_mailbox`, `get_message_count`

### 읽기
- `get_recent_messages`, `get_unseen_messages`
- `get_message`, `get_messages`

### 검색
- `search_by_sender`, `search_by_recipient`, `search_by_subject`
- `search_by_body`, `search_with_keyword`
- `search_since_date`, `search_unread_from_sender`
- `search_unreplied_from_sender`, `search_all_messages`

### 발송
- `send_email` (수신자/제목/본문/CC/BCC/첨부)
- `reply_to_email` (스레드 헤더 자동, Re: 접두사 자동)

### 첨부파일
- `get_attachments`, `save_attachment`

### 메시지 관리
- `delete_message`

## 보안 주의사항

- 비밀번호가 `claude_desktop_config.json`에 **평문**으로 저장됨
- 이 파일을 git에 커밋하거나 공유 금지
- 스크립트가 `icacls`로 권한 자동 제한
- **메일 발송 전 항상 사람이 내용 확인 권장** (Claude Desktop의 도구 사용
  승인 프롬프트를 절대 끄지 마세요)

## 사후 검증 (선택)

설정이 잘 들어갔는지 확인:

```powershell
Get-Content "$env:APPDATA\Claude\claude_desktop_config.json"
```

`naverworks-mail` 항목과 `IMAP_HOST` / `SMTP_HOST` / `EMAIL_USER`가 보이면 OK.
