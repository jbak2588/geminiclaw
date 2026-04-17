# GeminiClaw + Autopus-ADK 통합 및 마이그레이션 계획서

> **안내사항 (다음 에이전트에게 띄우는 메시지)**
> 이 문서는 `HNI_AutoTeam` (Go 기반) 프로젝트의 핵심 로직인 **Autopus-ADK(14+ 전문 에이전트 및 프롬프트 로직)**를 `GeminiClaw` (Python + Flutter 기반) 플랫폼으로 이식(마이그레이션)하기 위한 방향성을 정의한 기획서입니다.
> 개발 에이전트는 이 문서를 읽고, 아래 명시된 단계에 따라 마이그레이션 작업을 즉시 시작해 주십시오.

---

## 1. 개요 (Overview)

*   **목적:** 단순히 코드 스크립트를 실행하는 CLI를 넘어, 직관적인 대시보드(Google Opal 형태)와 외부 채널(Telegram)을 통해 14개의 AI 개발 요원을 시각적으로 관제하고 제어하는 "가상 회사 조직 시스템" 구축.
*   **플랫폼 (Vessel):** `GeminiClaw` (Python/FastAPI 백엔드 + Flutter 프론트엔드 + Telegram 기능 내장)
*   **로직 (Brain):** `Autopus-ADK` (기존 `HNI_AutoTeam`에 정의되어 있는 역할별 14개 에이전트의 프롬프트, 역할, 워크플로우 정의)

---

## 2. 작업 목표 및 원칙 (Goals)

1.  **"그릇" 유지, "내용물" 교체:** GeminiClaw가 가지고 있는 기존 채팅 인터페이스, Telegram 봇 연결, 노드 트리 시각화, `graph.py` 동작 구조 등 **인프라 코드는 대부분 재사용**합니다.
2.  **Autopus 에이전트 도입:** 현재 GeminiClaw 백엔드(`openclaw_backend/agents`)에 하드코딩된 기존 에이전트들을 삭제/수정하고, Autopus의 14개 에이전트 (Planner, Architect, Executor, Reviewer, DevOps 등) 로직을 파이썬 코드로 이식합니다.
3.  **UI 호환성:** 모델이나 노드가 추가 변경되더라도, Flutter 프론트엔드가 상태 이벤트(Idle, Working, Pending, Done 등)를 무리 없이 렌더링할 수 있도록 백엔드 이벤트 형식을 맞춥니다.

---

## 3. 단계별 마이그레이션 계획 (Phases)

### Phase 1: 백엔드 에이전트 구조 재설계 (Python)
*   **파일 접근:** `openclaw_backend/agents/agent_factory.py`, `company_setup.py`, `graph.py` 확인.
*   **작업 내용:** 
    1.  `E:\HNI_AutoTeam` (또는 로컬 어딘가에 백업된 Autopus 설정 파일들)의 내용(예: `.agents/` 내의 `system_prompt` 내용들)을 Python 문자열이나 설정 파일 구조로 마이그레이션합니다.
    2.  에이전트 목록 확장: Planner, Architect, Debugger, Deep Worker, DevOps, Executor, Explorer, Frontend-Specialist, Perf-Engineer, Reviewer, Security Auditor, Spec Writer, Tester, UX Validator, Validator 등 14개.
    3.  이들이 협업하는 순서도 (DAG)를 `graph.py` 로직 내에 새로 정의합니다.

### Phase 2: 외부 메신저 채널(Telegram) 테스트 및 연동
*   **파일 접근:** `openclaw_backend/channels/`
*   **작업 내용:**
    1.  기존 텔레그램 연동 로직이 새로운 Autopus 그래프(Graph)를 정상적으로 트리거(Trigger) 하는지 확인합니다.
    2.  메시지를 보냈을 때 백엔드 에이전트 릴레이 작업이 시작되고 그 결과(Commit Msg 또는 요약 요약)가 메신저로 텍스트 콜백 되는지 점검합니다.

### Phase 3: 프론트엔드 (Node 시각화 및 대시보드 정리)
*   **파일 접근:** `openclaw_app` (Flutter 소스코드)
*   **작업 내용:**
    1.  UI에서 각 노드가 14개의 Autopus 에이전트 파이프라인으로 정확하게 랜더링되는지 확인합니다.
    2.  작업 지시 채팅 인터페이스에서 내린 명령과 실시간 진행 현황 차트가 어긋남이 없는지 테스트합니다.

---

## 4. 첫 번째 작업 지시 (First Action for the Next Agent)
이 문서를 읽은 에이전트는 곧바로 아래 명령을 수행하십시오.

1.  `openclaw_backend/agents/agent_factory.py` 파일과 `company_setup.py` 파일의 기존 코드를 읽고 (`view_file` 또는 `read_file`),
2.  현재 어떻게 에이전트가 팩토리 패턴이나 그래프 스코프로 생성되고 있는지 분석합니다.
3.  Autopus 에이전트 구조를 파이썬 쪽에 어떻게 밀어 넣을지 **구현 계획**을 세우고 사용자에게 첫 보고를 진행하십시오.
