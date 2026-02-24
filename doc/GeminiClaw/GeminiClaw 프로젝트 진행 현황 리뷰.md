# GeminiClaw 프로젝트 진행 현황 리뷰

## 원래 비전 요약

> CTO가 AI 에이전트 팀을 설계·지시하고, **전용 앱**에서 작업 진행도·실시간 로그·보안 통제를 관리하는 멀티 에이전트 개발 플랫폼

---

## PoC 검증 목표 달성 현황

|PoC 단계|목표|상태|
|---|---|---|
|**PoC 1**|Worker + Reviewer 2인 에이전트 루프|✅ 완료 (Tool Use 연동까지)|
|**PoC 2**|WebSocket 실시간 이벤트 스트리밍|✅ 완료|
|**PoC 3**|HITL 위험 명령 거절 메커니즘|⚠️ 백엔드만 (프론트 미연결)|

---

## Phase별 상세 현황

### Phase 1: Core Agent Engine (백엔드) — 80%

|항목|상태|비고|
|---|---|---|
|프로젝트 구조 초기화|✅|FastAPI + LangGraph|
|Google GenAI SDK 설정|✅|`gemini-2.5-flash-lite`|
|핵심 도구 정의|✅|read_file, <br><br>write_file, <br><br>execute_shell_command|
|Worker Agent (Tool Use)|✅|LLM → 도구 호출 → 실행 → 결과 반환|
|Reviewer Agent|✅|관대한 리뷰 + 토큰 절약|
|Worker↔Reviewer 루프|✅|에러 시 END 라우팅 포함|
|**HITL 인터럽트 (LangGraph)**|❌|백엔드에 `APPROVAL_REQUIRED` 반환은 있으나 실제 pause/resume 미구현|

### Phase 2: Live Observability & API (백엔드) — 50%

|항목|상태|비고|
|---|---|---|
|FastAPI 백엔드|✅|동작 중|
|WebSocket 실시간 스트리밍|✅|로그 파일 저장 기능 포함|
|**프로젝트/태스크 생성 API**|❌|현재 단일 태스크만, DB 없음|
|**Shared Blackboard (상태 DB)**|❌|에이전트 간 컨텍스트 공유 없음|

### Phase 3: 전용 UI/UX 대시보드 (프론트) — 60%

|항목|상태|비고|
|---|---|---|
|Flutter 앱 스캐폴딩|✅|Chrome 웹 앱 동작|
|태스크 입력 + Deploy Team|✅|단일 텍스트 입력|
|Live Terminal 패널|✅|실시간 에이전트 로그 표시|
|워크플로우 상태 표시|✅|Active Node + Overall Status|
|**칸반 보드 (Swimlane)**|❌|TODO→IN PROGRESS→REVIEW→DONE 열 없음|
|**팀 구성 UI**|❌|에이전트 추가/구성 기능 없음|
|**HITL 승인 다이얼로그**|❌|프론트엔드 팝업 미구현|

### Phase 4: Security & Sandbox — 30%

|항목|상태|비고|
|---|---|---|
|위험 명령어 정규식 차단|✅|`rm -rf`, `sudo`, `del /f` 등|
|**Docker 샌드박스**|❌|미래 범위|

---

## 원래 비전 vs 현재의 GAP 분석

### ✅ 달성된 핵심 차별점

1. **전용 앱** — 채팅 UI가 아닌 대시보드 형태 ✅
2. **실시간 작업 모니터링** — WebSocket 스트리밍 ✅
3. **실제 도구 실행** — 파일 생성/읽기/셸 명령 ✅
4. **보안 규칙** — 위험 명령어 차단 패턴 ✅

### ❌ 미달성 핵심 기능 (우선순위순)

|순위|기능|원래 비전|난이도|
|---|---|---|---|
|**1**|HITL 승인 플로우|CTO가 위험 작업을 팝업으로 승인/거절|⭐⭐⭐|
|**2**|다중 에이전트 팀|PM → Worker1/Worker2 → QA 계층적 팀|⭐⭐⭐⭐|
|**3**|프로젝트/태스크 관리|프로젝트별 팀 구성 + 태스크 목록|⭐⭐⭐|
|**4**|칸반 보드 UI|TODO→PROGRESS→REVIEW→DONE 시각화|⭐⭐|
|**5**|Shared Blackboard|에이전트 간 상태/컨텍스트 공유 DB|⭐⭐⭐|
|**6**|Docker 샌드박스|격리된 코드 실행 환경|⭐⭐⭐⭐⭐|

---

## 다음 우선 추천: HITL 승인 플로우

현재 가장 빠르게 체감할 수 있고, 원래 비전의 **핵심 차별점**인 기능:

Worker가 "rm -rf /" 실행 시도

  → shell_tools가 "APPROVAL_REQUIRED" 반환

  → WebSocket으로 프론트엔드에 승인 요청

  → 프론트에 팝업 표시: "위험 명령입니다. 승인하시겠습니까?"

  → CTO 승인/거절 → 결과를 Worker에게 전달

이 기능이 완성되면 **프로젝트의 핵심 가치(보안 통제 + 인간 감독)**가 실증됩니다.

CommentCtrl+Alt+M