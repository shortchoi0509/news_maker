# NAVER WORKS Mail MCP Setup

Claude Desktop에서 네이버웍스 메일을 읽고 발송할 수 있게 하는 MCP 서버 설정.

## 사용 패키지

[`yunfeizhu/mcp-mail-server`](https://github.com/yunfeizhu/mcp-mail-server)
(npm: `mcp-mail-server`) — TypeScript 기반 IMAP/SMTP MCP 서버.

## 패치 빌드 (`server/`)

상류 `mcp-mail-server` v1.2.1을 그대로 쓰면 `get_recent_messages` 응답에 항상
본문/첨부가 포함돼서 7건만 요청해도 1MB 한도를 넘기고 실패한다. `server/`에
**같은 코드 + 두 가지 옵션 추가**한 패치 빌드를 둔다:

- `headers_only: true` → 본문·HTML·첨부 메타데이터 모두 빼고 메타데이터만 반환
  (100건도 한 번에 통과)
- `max_body_length: <int>` → 본문 텍스트를 N자로 자름 (0이면 본문 제거, 음수면 그대로)

이 옵션들은 `get_recent_messages`, `get_unseen_messages`에 추가됐다. 다른 22개
도구는 상류와 동일.

### 패치 빌드로 전환하기

```powershell
# 0. 자격증명을 아직 등록 안 했으면 먼저 한 번 실행
powershell -ExecutionPolicy Bypass -File .\setup-naverworks-mcp.ps1

# 1. 패치 빌드 의존성 설치 + claude_desktop_config의 command/args 갱신
powershell -ExecutionPolicy Bypass -File .\install-patched.ps1

# 2. Claude Desktop 완전 종료 후 재시작
# 3. Chat에서 테스트:
#    "get_recent_messages로 INBOX 최근 30개 메일을 headers_only=true로 가져와줘"
```

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
