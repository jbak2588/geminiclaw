# GeminiClaw: AI 기반 회사 운영 OS — 기획문서

> **작성일**: 2026년 2월 24일  
> **프로젝트**: GeminiClaw (openclaw_backend + openclaw_app)  
> **목표**: AI 에이전트 팀이 회사 운영을 자동화하는 시스템

---

## 1. 프로젝트 개요

### 1.1 비전
1인 창업자(CTO)가 AI 에이전트 팀을 구성하여 회사 운영 전반(법무, 회계, 마케팅, 개발 등)을 
자동화하는 **"AI 회사 운영 OS"**. 

### 1.2 대상 회사
| 항목 | 값 |
|---|---|
| 회사명 | PT Humantric Net Indonesia |
| 법인 유형 | PMA (외국인 투자 법인) |
| KBLI | 63122 (포털 웹 및 소셜 미디어 플랫폼 운영) |
| 웹사이트 | [humantric.net](https://humantric.net) |
| 제품 | Mozzy (모지) — AI 기반 글로벌 하이퍼로컬 커뮤니티 슈퍼앱 |
| 앱 코드 | `C:\bling\bling_app` (Flutter) |
| GitHub | [github.com/jbak2588/bling](https://github.com/jbak2588/bling) |
| 현재 단계 | 앱 완성 (PG 제외), 필드 테스트 중, 앱스토어 등록 준비 |

---

## 2. 시스템 아키텍처

### 2.1 전체 프로세스

```
CTO 지시 → PM Agent → [법무팀, 개발팀, 마케팅팀, ...] → Reviewer → 결과물
              ↑                                              ↓
         Setup Wizard                              순차 실행 (Dispatcher)
     (회사 프로필 → AI 조직도 → 팀 선택)
```

### 2.2 기술 스택

| 구분 | 기술 |
|---|---|
| Backend | Python + FastAPI + LangGraph + Gemini 2.5 Flash |
| Frontend | Flutter Web (Dart) |
| 통신 | WebSocket (실시간 스트리밍) |
| AI 모델 | Google Gemini 2.5 Flash Lite |
| 보안 | HITL (Human-in-the-Loop) — 위험 명령어 CTO 승인 |

### 2.3 핵심 파일 구조

```
openclaw_backend/
├── agents/
│   ├── agent_config.py      # 9개 역할 정의 + 5개 팀 프리셋 + COMPANY_CONTEXT
│   ├── agent_factory.py     # 동적 노드 생성 + Reviewer status 파싱
│   ├── company_setup.py     # AI 조직도 생성기
│   ├── graph.py             # LangGraph 워크플로우 (Dispatcher 기반 순차 실행)
│   ├── pm_agent.py          # PM 에이전트 (태스크 분배)
│   └── state.py             # AgentState (agent_order, current_agent_index)
├── api/
│   └── websockets.py        # WebSocket API (org_chart, task, HITL)
├── tools/
│   ├── file_tools.py        # read_file, write_file
│   └── shell_tools.py       # execute_shell_command (HITL 보호)
└── doc/                     # 백서, 회사 서류

openclaw_app/
└── lib/
    └── main.dart            # 3단계 Setup Wizard + 실시간 터미널
```

---

## 3. Agent 역할 (9개)

| Agent | 역할 | 도구 권한 |
|---|---|---|
| PM | CTO 지시 분석 → 팀원에게 하위 태스크 분배 | 없음 (순수 라우팅) |
| Developer | 코드 작성/수정/빌드 | read_file, write_file, shell |
| Reviewer | 품질 검수 (APPROVED/REJECTED) | read_file |
| Legal | 이용약관, 개인정보처리방침, PSE 등록 | read_file, write_file |
| Accountant | SPT 세무신고, VAT, 재무제표 | read_file, write_file |
| Admin | PMA 유지관리, LKPM 보고, NIB 갱신 | read_file, write_file |
| Marketer | ASO, 소셜미디어, 커뮤니티 시딩 | read_file, write_file |
| CS | FAQ, 사용자 문의 템플릿, 신고 처리 | read_file, write_file |
| HR | 채용, BPJS, 근로계약서 | read_file, write_file |

---

## 4. Mozzy 앱 분석 방안

### 4.1 현재 에이전트가 접근 가능한 방법

| 방법 | 가능 여부 | 설명 |
|---|---|---|
| **로컬 프로젝트 폴더** (`C:\bling\bling_app`) | ✅ 가능 | `read_file` 도구로 직접 읽기 가능 |
| **GitHub repo** (`github.com/jbak2588/bling`) | ⚠️ 간접 가능 | `execute_shell_command`로 `git clone` 또는 `curl` 가능 |
| **GitHub API** | ❌ 직접 불가 | 별도 도구 추가 필요 (향후) |

### 4.2 권장 방식: 로컬 폴더 참조

에이전트의 `read_file` 도구에 `C:\bling\bling_app` 경로를 직접 지정하면 
Dart 소스코드를 읽고 분석할 수 있습니다.

**예시**: Legal Agent가 개인정보처리방침을 작성할 때,
```
read_file("C:\bling\bling_app\lib\models\user_model.dart")
```
→ 사용자 데이터 구조를 확인 → 어떤 개인정보를 수집하는지 파악 → 문서에 반영

### 4.3 향후 확장: GitHub 연동 도구

```python
# 추가 예정 도구
TOOL_REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
    "execute_shell_command": execute_shell_command,
    "github_read_file": github_read_file,      # GitHub API로 파일 읽기
    "github_list_files": github_list_files,     # 레포 파일 목록
    "github_search_code": github_search_code,   # 코드 검색
}
```

---

## 5. 개발 로드맵

### Phase 1: AI 조직도 + 멀티 에이전트 (✅ 완료)

| 항목 | 상태 | 내용 |
|---|---|---|
| AI 조직도 생성 | ✅ | LLM이 회사 정보 기반 부서 추천 |
| 9개 에이전트 역할 | ✅ | PM, Dev, Reviewer, Legal, Accountant, Admin, Marketer, CS, HR |
| 5개 팀 프리셋 | ✅ | 스타트업 최소, 앱 출시, 정식 법인, 성장, 준법 |
| 순차 실행 (Dispatcher) | ✅ | PM → Agent1 → Reviewer → Agent2 → ... → END |
| Reviewer status 파싱 | ✅ | APPROVED → 다음, REJECTED → 재작업 |
| HITL (위험 명령 차단) | ✅ | CTO 승인/거절 다이얼로그 |
| COMPANY_CONTEXT 주입 | ✅ | 모든 에이전트에 PT Humantric + Mozzy 정보 자동 제공 |
| Knowledge 시스템 | ✅ | `E:\geminiclaw\doc` 폴더 자동 참조 (.md, .txt, .json) |
| Flutter Setup Wizard | ✅ | 3단계: 회사 선택 → 조직도 토글 → Deploy |
| 무한 루프 버그 수정 | ✅ | Reviewer status + 순차 실행 + 컨텍스트 주입 |

### Phase 2: 컨텍스트 강화 (🔶 다음 단계)

| 항목 | 상태 | 내용 |
|---|---|---|
| PDF 파서 추가 | ⬜ | PyPDF2로 회사 서류(AKTA, NIB 등) 읽기 |
| 로컬 프로젝트 참조 | ⬜ | `C:\bling\bling_app` 소스코드 분석 기능 |
| GitHub 연동 도구 | ⬜ | GitHub API로 레포 파일 읽기/검색 |
| 에이전트 메모리 | ⬜ | 이전 세션 결과 기억 (태스크 DB) |

### Phase 3: 진행 관리 (🔷 향후)

| 항목 | 상태 | 내용 |
|---|---|---|
| 태스크 DB | ⬜ | SQLite/Firestore로 태스크 상태 저장 |
| 칸반 보드 UI | ⬜ | TODO → IN_PROGRESS → DONE 시각화 |
| 산출물 관리 | ⬜ | 각 에이전트 결과물 파일로 저장/다운로드 |

### Phase 4: 개인 비서 (🔷 장기)

| 항목 | 상태 | 내용 |
|---|---|---|
| 웹 브라우징 | ⬜ | MCP 서버 연동으로 웹 검색 |
| 이메일 관리 | ⬜ | Gmail API 연동 |
| 일정 관리 | ⬜ | Google Calendar 연동 |

---

## 6. 회사 서류 관리

### 6.1 서류 저장 경로

**`E:\geminiclaw\doc\company_docs\`**

| 서류 | 설명 | 파일명 |
|---|---|---|
| AKTA PENDIRIAN | 법인설립정관 | `akta_pendirian.pdf` |
| SK KEHAKIMAN | 법무부 승인서 | `sk_kehakiman.pdf` |
| NPWP | 납세자 번호 | `npwp.pdf` |
| NIB | 사업자등록번호 (OSS) | `nib.pdf` |
| PKKPR | 위치적합성 확인서 | `pkkpr.pdf` |

### 6.2 에이전트 참조 방법

현재 `.md`, `.txt`, `.json` 파일만 자동 참조.
PDF → 텍스트 변환 필요 (Phase 2에서 PyPDF2 추가 예정).

---

## 7. 버그 수정 이력

### 7.1 무한 루프 (2026-02-24 수정)

**원인**: Reviewer가 `create_agent_node()` 팩토리로 생성 → 항상 `status: "needs_review"` 반환 → graph.py에서 "rejected"로 분기 → 첫 에이전트로 되돌아감 → 무한 루프

**증상**: `session_20260224_143729_17719186.txt` — 7,652줄의 반복 (legal → reviewer APPROVED → legal → ...)

**수정**: 
1. `agent_factory.py`: Reviewer 텍스트에 "APPROVED" 포함 시 `status: "approved"` 반환
2. `graph.py`: Dispatcher 노드 기반 순차 실행
3. `agent_config.py`: COMPANY_CONTEXT 주입으로 "정보 요청" 루프 방지
