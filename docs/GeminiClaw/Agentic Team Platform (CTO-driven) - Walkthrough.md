[[Task]]

이 문서에서는 '채팅 대신 전용 앱 지시', '실시간 작업 시각화', '보안/통제 체계'를 목표로 개발된 **Gemini 전용 OpenClaw 멀티 에이전트 시스템**의 초기 구현체(PoC)를 리뷰합니다.

## 달성한 마일스톤 (Phases 1-3)

### 1. Backend Core Engine (Python/LangGraph)

단일 모델을 호출하는 것을 넘어, 에이전트들을 생성하고 워크플로우로 묶어 서로 피드백을 주고받는 순차적 파이프라인(LangGraph)을 구축했습니다.

- agents/worker.py: 코딩과 작업을 수행하는 **Worker Node**. LLM이 할당된 태스크를 풀고 코드를 생성합니다.
- agents/reviewer.py: 워커의 결과물을 다시 평가하여 `approved` 혹은 `rejected + feedback`을 뱉는 **Reviewer Node**. (이로써 자율적 오류 수정 루프가 형성됩니다)
- agents/graph.py: 위 노드들을 StateGraph로 연결하고 사이클을 완성했습니다.
- tools/file_tools.py & 
    
    tools/shell_tools.py: 에이전트가 로컬 환경의 파일을 읽거나 셀 명령어(ls, mkdir 등)를 칠 수 있게 해주는 도구 구성을 마련했습니다.

### 2. Live Observability API (FastAPI)

전용 앱(UI)에서 이 에이전트들이 작업하는 순간순간을 들여다 볼 수 있는 백엔드 통신 레이어입니다.

- api/websockets.py: `ws://localhost:8000/ws/{client_id}` 엔드포인트를 열어, 클라이언트가 태스크를 던지면 `team_graph.stream()`이 작동하면서
    - 지금 어느 노드(Worker or Reviewer)가 작동 중인지
    - 현재 무슨 생각을 하고 어떤 코드를 배출했는지 JSON 이벤트로 프론트엔드에 실시간(Streaming)으로 밀어냅니다(SSE/WebSocket).

### 3. Dedicated UI App (Flutter)

사용자(CTO)가 채팅 대신 직관적인 대시보드로 작업할 수 있는 프론트엔드 앱입니다. (`openclaw_app`)

- **왼쪽 패널 (Deploy Team):** 새로운 에픽(Epic)이나 버그 수정 요청을 구조화하여 던집니다.
- **중앙 패널 (State Kanban):** 현재 워크플로우가 진행 중인지, Worker가 작업 중인지, Reviewer가 검수 중인지, 아니면 거절(Rejected)되어 다시 루프를 도는지 직관적으로 상태값을 띄워줍니다.
- **우측 패널 (Live Terminal & Thoughts):** 백엔드 WebSocket을 통해 넘어오는 에이전트들의 생생한 사고 프로세스와 터미널 로그를 실시간으로 출력합니다.

---

## 실행해 보기 (How to Test)

TIP

두 개의 터미널을 열어 백엔드와 프론트엔드를 동시에 띄웁니다.

**1. Backend Server 실행**

bash

cd e:\geminiclaw\openclaw_backend

.\venv\Scripts\activate

# .env 파일에 GEMINI_API_KEY=xxx 를 꼭 추가해야 합니다.

python main.py

_(서버가 `localhost:8000` 에서 시작됩니다.)_

**2. Frontend App (Flutter) 실행**

bash

cd e:\geminiclaw\openclaw_app

flutter run -d windows  # 또는 -d chrome

_(앱이 켜지면 좌측 입력칸에 "피보나치 수열 파이썬 함수 작성해줘" 등을 입력하고 'Deploy Team' 버튼을 누르시면, 우측 패널에 실시간으로 동작 로그가 찍히는 것을 볼 수 있습니다.)_

---

## 다음 목표 (Phase 4: Security Rules)

UI와 실시간 스트리밍 루프가 완성되었으므로, 원래 제안하셨던 **최종 보안 규칙 제정(Security Sandbox)**로 넘어갈 계획입니다.

- **Human-in-the-Loop 기능:** 에이전트가 
    
    shell_tools.py에서 파괴적 명령어(예: rm)나 알 수 없는 네트워크 호출을 할 때, 프론트엔드 중앙 패널에 `[승인 대기 중]` 팝업을 띄우고 사용자가 OK/Reject 하는 로직 추가.
- **Docker Container Sandbox:** 코드를 내 PC에 직접 쓰는 게 아니라 도커 내부에 쓰도록 분리.

NOTE

**UPDATE:** Phase 4의 첫 단계인 **명령어 기반 승인 모달(HITL Dialog)**이 

lib/main.dart 에 구현되었습니다. 현재 백엔드 

shell_tools.py가 `rm -rf`, `drop table`, `sudo` 등의 명령어를 감지하면 즉시 "APPROVAL_REQUIRED"를 포함한 메세지를 쏘며, 이 메시지를 받은 Flutter 대시보드는 중앙에서 알럿 창을 띄워 사용자에게 Approve(허가) / Reject(거부)를 강제로 요청합니다.