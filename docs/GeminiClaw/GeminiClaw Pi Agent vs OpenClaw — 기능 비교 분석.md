
> **분석일**: 2026-02-26  
> **비교 대상**: GeminiClaw 
> 
> pi_agent.py (146줄) vs OpenClaw v55+ (230k stars, MIT)

---

## 1. 프로젝트 성격 비교

|구분|OpenClaw (원본)|GeminiClaw (현재)|
|---|---|---|
|**정체성**|범용 개인 AI 비서 플랫폼 (오픈소스, 커뮤니티 860+명)|회사 운영 AI OS (커스텀 포크)|
|**LLM**|Claude (Anthropic), GPT, 다중 모델 + Failover|Gemini 2.5 Flash Lite (단일 모델)|
|**주요 언어**|TypeScript (Node.js)|Python (FastAPI + LangGraph)|
|**프론트엔드**|macOS 네이티브 앱 + iOS/Android + WebChat|Flutter Web (SPA)|
|**규모**|~수만 줄 (Gateway + 16개 채널 + 앱)|~2,000줄 (백엔드 + 프론트엔드)|

---

## 2. 핵심 기능 비교 (10개 카테고리)

### 2.1 아키텍처

|항목|OpenClaw|GeminiClaw|Gap|
|---|---|---|---|
|제어 평면|Gateway WebSocket 서버 (ws://127.0.0.1:18789)|FastAPI WebSocket (ws://localhost:8001)|구조적 유사|
|에이전트 런타임|Pi Agent RPC 모드 (tool streaming + block streaming)|Pi Agent 클래스 (동기 invoke + 2-pass tool call)|⚠️ 스트리밍 미지원|
|멀티 에이전트|Multi-agent routing (세션별 격리)|LangGraph 기반 PM→Worker→Reviewer 워크플로우|✅ GeminiClaw 고유 강점|

### 2.2 통신 채널

|채널|OpenClaw|GeminiClaw|
|---|---|---|
|WhatsApp|✅ (Baileys)|❌|
|Telegram|✅ (grammY)|❌|
|Slack|✅ (Bolt)|❌|
|Discord|✅ (discord.js)|❌|
|Signal|✅ (signal-cli)|❌|
|iMessage|✅ (BlueBubbles + legacy)|❌|
|Google Chat|✅|❌|
|MS Teams|✅|❌|
|WebChat|✅ (내장)|✅ (Flutter Web 자체 UI)|
|**Gap 요약**|16개 채널 지원|WebSocket 1개만 지원|

### 2.3 도구 (Tools)

|도구 카테고리|OpenClaw|GeminiClaw|
|---|---|---|
|파일 I/O|✅ read, write, edit|✅ read_file, write_file|
|Shell 실행|✅ bash (Docker 샌드박스 가능)|✅ execute_shell_command (HITL)|
|시스템 알림|✅ system.notify (macOS TCC 통합)|✅ send_notification (크로스플랫폼)|
|클립보드|✅ (macOS node)|✅ read/write_clipboard|
|브라우저 제어|✅ CDP 기반 Chrome 제어|❌|
|카메라/스크린|✅ camera snap/clip, screen record|❌|
|위치 정보|✅ location.get|❌|
|Cron/스케줄러|✅ cron jobs + wakeups|❌|
|Webhook|✅ 외부 트리거 수신|❌|
|Gmail 연동|✅ Pub/Sub|❌|
|Skill 업데이트|❌ (수동 편집)|✅ update_skill_manual (자가 발전)|
|Knowledge RAG|❌ (외부 플러그인 필요)|✅ 프로젝트별 .md 자동 주입|

### 2.4 보안 모델

|항목|OpenClaw|GeminiClaw|
|---|---|---|
|HITL (승인 팝업)|❌ (elevated 모드 토글 방식)|✅ 위험 명령어 자동 감지 + UI 승인|
|샌드박스|✅ Docker per-session|✅ Docker 샌드박스 (sandbox_manager)|
|인증/인가|Tailscale identity + password auth|❌ (로컬 전용, 인증 없음)|
|DM 정책|allowlist 기반 DM 제어|❌ (단일 사용자 가정)|
|Path Traversal|N/A (파일 도구 자체 보안)|✅ sanitize_project_id 적용|
|CORS|N/A|✅ ALLOWED_ORIGINS 환경변수|

### 2.5 세션 & 메모리

|항목|OpenClaw|GeminiClaw|
|---|---|---|
|세션 모델|main + group 격리, 활성화 모드|단순 History 배열 전달|
|영구 저장|✅ (세션별 자동 유지)|✅ SQLite 기반 memory_store|
|세션 프루닝|✅ 자동 (session-pruning)|❌|
|컨텍스트 압축|✅ `/compact` 명령어|❌|
|Agent-to-Agent|✅ sessions_send, sessions_history|✅ PM→Worker 간 state 공유|

### 2.6 음성 & 미디어

|항목|OpenClaw|GeminiClaw|
|---|---|---|
|Voice Wake|✅ 항시 대기 음성 인식 (ElevenLabs)|❌|
|Talk Mode|✅ 연속 대화 오버레이|❌|
|미디어 파이프라인|✅ 이미지/오디오/비디오 트랜스크립션|❌|
|Canvas (A2UI)|✅ 에이전트 시각적 워크스페이스|❌|

### 2.7 플랫폼

|항목|OpenClaw|GeminiClaw|
|---|---|---|
|macOS|✅ 네이티브 메뉴바 앱|❌|
|iOS|✅ 노드 앱 (Canvas, Voice Wake)|❌|
|Android|✅ 노드 앱 (Canvas, Camera)|❌|
|Windows|✅ WSL2|✅ (크로스플랫폼 tools)|
|Linux|✅ 네이티브|✅ (크로스플랫폼 tools)|
|Web|✅ WebChat|✅ Flutter Web|

### 2.8 운영 & 모니터링

|항목|OpenClaw|GeminiClaw|
|---|---|---|
|Health 체크|✅ Doctor CLI|❌|
|로깅 시스템|✅ 구조화된 logging|✅ (최근 logging 모듈 전환)|
|세션 로그 뷰어|❌ (CLI 기반)|✅ Flutter UI 로그 뷰어|
|칸반 보드|❌|✅ 실시간 태스크 시각화|

### 2.9 Workspace & Skills

|항목|OpenClaw|GeminiClaw|
|---|---|---|
|Skills 위치|`~/.openclaw/workspace/skills/`|`skills/{role}/SKILL.md`|
|프롬프트 파일|AGENTS.md, SOUL.md, TOOLS.md|AGENTS.md, COMPANY.md|
|동적 생성|❌ (수동 설치/관리)|✅ AI가 Skill 자동 생성|
|자가 업데이트|❌|✅ update_skill_manual 도구|
|ClawHub 레지스트리|✅ (외부 Skill 검색/설치)|❌|

### 2.10 채팅 명령어

|명령어|OpenClaw|GeminiClaw|
|---|---|---|
|`/status`|✅|❌|
|`/new` `/reset`|✅|❌|
|`/compact`|✅|❌|
|`/think` (사고 레벨)|✅|❌|
|`/verbose`|✅|❌|
|`/usage`|✅|❌|

---

## 3. GeminiClaw 고유 강점 (OpenClaw에 없는 기능)

|기능|설명|
|---|---|
|🏢 **멀티 에이전트 팀 OS**|PM→Worker→Reviewer 순차 실행 워크플로우|
|📋 **칸반 보드**|실시간 태스크 시각화 (TODO/IN_PROGRESS/REVIEW/DONE)|
|🤖 **AI 조직도 자동 설계**|회사 정보 입력 → 부서/에이전트 자동 구성|
|📄 **Skill 자가 발전**|update_skill_manual 도구로 에이전트가 자기 매뉴얼 수정|
|📚 **Knowledge RAG**|프로젝트별 PDF/MD 자동 파싱 + System Prompt 주입|
|⚠️ **HITL 승인 UI**|위험 명령어 앱 내 승인/거절 팝업|
|🔒 **Path Traversal 방어**|sanitize_project_id() 입력값 검증|

---

## 4. 개선 로드맵 제안 (GeminiClaw에 도입 가능한 OpenClaw 기능)

### 🔴 Priority 1 (핵심)

|기능|효과|난이도|
|---|---|---|
|**응답 스트리밍**|Pi Agent 응답을 토큰 단위 실시간 표시|⭐⭐|
|**세션 컨텍스트 압축**|긴 대화 시 토큰 절약 (`/compact` 기능)|⭐⭐|
|**모델 Failover**|Gemini API 장애 시 대체 모델 자동 전환|⭐⭐⭐|

### 🟠 Priority 2 (확장)

|기능|효과|난이도|
|---|---|---|
|**Telegram 채널**|모바일에서 Pi에 메시지 전송 가능|⭐⭐|
|**브라우저 제어**|웹 검색/스크래핑 도구 추가|⭐⭐⭐|
|**Cron 스케줄러**|"매일 아침 9시에 보고서 생성" 자동화|⭐⭐|

### 🟡 Priority 3 (고급)

|기능|효과|난이도|
|---|---|---|
|**Voice Wake**|"Pi야" 음성 호출로 대화 시작|⭐⭐⭐⭐|
|**Canvas (A2UI)**|에이전트가 UI를 직접 조작하는 시각적 워크스페이스|⭐⭐⭐⭐⭐|
|**ClawHub Skills**|외부 Skill 레지스트리 연동|⭐⭐⭐|

---

## 5. 결론

|관점|OpenClaw|GeminiClaw|
|---|---|---|
|**1:1 개인 비서**|⭐⭐⭐⭐⭐ (16채널, 음성, 캔버스)|⭐⭐⭐ (WebSocket + 기본 도구)|
|**팀 운영 / 멀티 에이전트**|⭐⭐ (세션 분리 수준)|⭐⭐⭐⭐⭐ (PM+9개 역할+칸반)|
|**Skill 자가 발전**|⭐ (수동 관리)|⭐⭐⭐⭐⭐ (AI 자동 생성+수정)|
|**Knowledge/RAG**|⭐⭐ (플러그인 필요)|⭐⭐⭐⭐ (PDF 파싱, 프로젝트별 주입)|
|**플랫폼 커버리지**|⭐⭐⭐⭐⭐ (macOS/iOS/Android/Web)|⭐⭐ (Web only)|

> **핵심 인사이트**: OpenClaw은 **개인 비서의 채널·플랫폼 다양성**에 강하고, GeminiClaw은 **회사 운영 자동화·멀티 에이전트 협업**에 강합니다. 두 시스템은 보완적이며, OpenClaw의 스트리밍/채널 기능을 GeminiClaw에 선택적으로 도입하면 시너지를 극대화할 수 있습니다.