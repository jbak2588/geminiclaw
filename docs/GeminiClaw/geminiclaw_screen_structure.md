# GeminiClaw / AI Team OS 화면 구조도 설계

## 1. 화면 설계 목표
- 사용자는 **채팅창 중심**으로 업무를 지시한다.
- 사용자는 현재 AI 팀의 진행 상황을 **그래픽 노드 흐름**으로 이해한다.
- 승인과 결과 확인은 **팝업 + 전용 승인 화면 + 외부 채널**로 동기화된다.
- 모든 작업은 **로그/일지 화면**에서 사후 추적 가능하다.

---

## 2. 전역 레이아웃

```text
┌────────────────────────────────────────────────────────────────────┐
│ Top Bar: Workspace / Provider / Notifications / User / Quick Cmd │
├───────────────┬──────────────────────────────────┬─────────────────┤
│ Left Sidebar  │ Main Content                     │ Right Live Feed │
│               │                                  │                 │
│ - Dashboard   │ Selected screen                  │ - Active agent  │
│ - Command     │                                  │ - Recent events │
│ - Workflow    │                                  │ - Pending appr. │
│ - Approval    │                                  │ - Errors        │
│ - Projects    │                                  │                 │
│ - Knowledge   │                                  │                 │
│ - Logs        │                                  │                 │
│ - Channels    │                                  │                 │
│ - Departments │                                  │                 │
│ - Settings    │                                  │                 │
└───────────────┴──────────────────────────────────┴─────────────────┘
```

---

## 3. 화면 목록

### 3.1 Dashboard
#### 목적
현재 회사 운영 상태를 한눈에 보여주는 홈 화면.

#### 핵심 블록
- 오늘의 작업 수
- 승인 대기 수
- 진행 중 워크플로 수
- 최근 완료 작업
- 최근 오류
- 채널 수신 현황
- 프로젝트별 진행률 카드

#### 주요 액션
- 새 작업 시작
- 승인 센터 이동
- 최근 작업 상세 열기

---

### 3.2 Command Chat
#### 목적
사용자가 자연어로 업무를 입력하는 메인 지시 화면.

#### 레이아웃
```text
┌────────────────────────────────────────────────────────────┐
│ Task Context / Project / Team Preset / Provider           │
├────────────────────────────────────────────────────────────┤
│ Conversation Timeline                                     │
│ - user command                                            │
│ - system interpretation                                   │
│ - agent status updates                                    │
│ - result summary                                          │
├────────────────────────────────────────────────────────────┤
│ Prompt Input Box + Attach Button + Send Button            │
└────────────────────────────────────────────────────────────┘
```

#### 기능
- 프로젝트 선택
- 팀 프리셋 선택
- 파일 첨부
- 빠른 명령 템플릿
- 후속 지시 이어쓰기

#### 출력 예시
- “요청을 Task로 등록했습니다.”
- “Planning Agent와 Developer Agent를 호출했습니다.”
- “승인 필요 단계가 예상됩니다.”

---

### 3.3 Workflow Live
#### 목적
Task가 AI 부서 사이를 어떻게 이동하는지 실시간으로 보여주는 시각화 화면.

#### 표현 방식
- 노드 그래프
- 좌측 → 우측 진행 흐름
- 상태에 따라 색상 변화

#### 기본 노드 예시
```text
User Command
   ↓
Control Agent
   ↓
PM Agent
  ├── Planning Agent
  ├── Developer Agent
  └── Operations Agent
   ↓
Reviewer Agent
   ↓
Approval Queue
   ↓
Final Report
```

#### 노드 상태 규칙
- 대기: 회색
- 진행 중: 파랑
- 승인 대기: 주황
- 완료: 초록
- 실패: 빨강

#### 노드 상세 패널
노드를 클릭하면 아래 정보 표시:
- 노드 이름
- 역할 설명
- 입력 데이터 요약
- 출력 결과 요약
- 처리 시간
- 관련 파일
- 다음 전달 대상

---

### 3.4 Approval Center
#### 목적
사람 승인 필요한 항목을 한곳에서 검토하고 승인/반려하는 화면.

#### 카드 항목
- 요청 제목
- 요청 Agent
- 프로젝트
- 영향 범위
- 위험도
- 승인 필요 이유
- 생성 시각

#### 승인 액션
- 승인
- 반려
- 수정 요청
- 보류

#### 상세 보기
- 실행 예정 명령
- 참조 문서
- 이전 유사 승인 이력
- 채널 회신 여부

---

### 3.5 Projects
#### 목적
프로젝트 단위 컨텍스트와 작업 히스토리를 관리하는 화면.

#### 기능
- 프로젝트 생성/수정
- 설명 및 태그 관리
- 연결된 지식 문서 보기
- 관련 Task 목록 보기
- 활성 부서 프리셋 보기

#### 상세 탭
- Overview
- Tasks
- Knowledge
- Members / Roles
- Settings

---

### 3.6 Knowledge Library
#### 목적
업로드된 PDF, 이미지, 메모, 요약문, SOP를 저장·검색하는 화면.

#### 기능
- 파일 업로드
- 프로젝트 연결
- 문서 요약
- 태그 / 카테고리 분류
- 관련 Task 연결
- AI가 생성한 문서와 원본을 함께 보관

#### 카드 항목
- 제목
- 프로젝트
- 요약
- 업로드 시각
- 문서 타입
- 관련 Task 수

---

### 3.7 Logs / Work Journal
#### 목적
모든 업무를 일지처럼 확인하는 화면.

#### 보기 모드
- Task 타임라인
- 프로젝트별 로그
- 승인 이력
- 실패 작업 이력
- 채널 수신 기록

#### 로그 상세 내용
- 지시 원문
- 해석 결과
- 부서별 수행 내용
- 승인 이력
- 첨부파일
- 최종 결과
- 오류 및 재시도

---

### 3.8 Channel Hub
#### 목적
외부 채널과 내부 Task를 연결하는 화면.

#### 기능
- 채널별 연결 상태 확인
- 수신 메시지 목록
- 메시지 → Task 변환
- 승인 요청 발송 현황
- 파일 수신 현황

#### 지원 채널 후보
- Telegram
- WhatsApp
- Slack
- Email

---

### 3.9 Departments
#### 목적
AI 부서 구조와 역할 설정을 관리하는 화면.

#### 기능
- 부서 추가/비활성화
- 역할 설명 편집
- SOP / Prompt 편집
- 승인 필요 규칙 설정
- 사용 가능한 도구 설정

---

### 3.10 Settings
#### 목적
시스템 기본 설정 및 Provider 설정 화면.

#### 주요 섹션
- AI Provider 설정
- API Key 설정
- 채널 연결 설정
- 보안 및 승인 정책
- 로그 보관 기간
- 파일 업로드 제한

---

## 4. 전역 UX 규칙

### 4.1 알림 규칙
- 승인 대기는 전역 빨간 배지로 표시
- 오류는 우측 Live Feed에 즉시 노출
- 완료 보고는 토스트 + 로그 저장

### 4.2 검색 규칙
모든 핵심 화면에서 검색 지원:
- Task ID
- 프로젝트명
- Agent명
- 채널 발신자
- 승인 상태

### 4.3 상태 일관성 규칙
- Dashboard, Workflow, Logs, Approval Center는 동일 Task 상태를 공유한다.
- 한 화면의 승인 결과는 모든 화면과 채널에 즉시 반영된다.

---

## 5. 핵심 사용자 흐름

### 5.1 대시보드 기반 업무 지시 흐름
1. Dashboard 또는 Command Chat 진입
2. 프로젝트 선택
3. 자연어 지시 입력
4. Task 생성
5. Workflow Live 이동
6. 승인 필요 시 Approval Center 또는 팝업 처리
7. 결과 보고서 확인
8. Logs에 자동 저장

### 5.2 채널 기반 외부 지시 흐름
1. 외부 사용자가 채널로 명령 전송
2. Channel Hub 수신
3. 내부 Task 생성
4. Workflow Live 반영
5. 결과 요약 채널 회신

---

## 6. MVP 화면 우선순위

### 필수
- Dashboard
- Command Chat
- Workflow Live
- Approval Center
- Logs / Work Journal
- Settings(Provider 연결)

### 2차
- Projects
- Knowledge Library
- Channel Hub
- Departments

