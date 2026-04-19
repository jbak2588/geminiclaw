# GeminiClaw / AI Team OS 백엔드 API 명세 초안

## 1. 설계 목적
- Flutter 대시보드와 백엔드 오케스트레이터 간 통신 규약 정의
- REST는 설정/조회/승인/문서 관리 중심
- WebSocket은 실시간 진행상황, 노드 이벤트, 승인 요청 푸시 중심
- 외부 채널 입력도 동일 Task 흐름으로 연결

---

## 2. 베이스 규칙

### Base URL
```text
http://localhost:8001/api
ws://localhost:8001/ws/{clientId}
```

### 공통 응답 형식
```json
{
  "success": true,
  "message": "ok",
  "data": {}
}
```

### 공통 오류 형식
```json
{
  "success": false,
  "error_code": "TASK_NOT_FOUND",
  "message": "Task not found"
}
```

### 인증
초기 MVP:
- 로컬 또는 내부망 사용 전제
- 간단한 Bearer Token 또는 Session Token

향후:
- 사용자 인증 및 역할 기반 권한

---

## 3. REST API 목록

## 3.1 Provider 설정

### GET /settings/provider
현재 활성 AI Provider 조회

#### Response
```json
{
  "success": true,
  "data": {
    "provider_type": "gemini",
    "label": "Main Gemini Provider",
    "model_name": "gemini-2.5-pro",
    "is_active": true
  }
}
```

### POST /settings/provider
Provider 및 API Key 저장

#### Request
```json
{
  "provider_type": "gpt",
  "label": "Main GPT Provider",
  "api_key": "***",
  "model_name": "gpt-5"
}
```

---

## 3.2 Projects

### GET /projects
프로젝트 목록 조회

### POST /projects
프로젝트 생성

#### Request
```json
{
  "name": "Bling Team OS",
  "description": "Internal AI team operating system"
}
```

### GET /projects/{projectId}
프로젝트 상세 조회

### PATCH /projects/{projectId}
프로젝트 수정

---

## 3.3 Tasks

### POST /tasks
대시보드 또는 외부 채널에서 Task 생성

#### Request
```json
{
  "project_id": "uuid-or-null",
  "source_type": "dashboard",
  "instruction_text": "이번 주 고객 문의를 정리해서 운영 보고서로 만들어줘",
  "priority": "high"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "task_id": "task-uuid",
    "status": "pending",
    "title": "고객 문의 운영 보고서 작성"
  }
}
```

### GET /tasks
Task 목록 조회

쿼리 파라미터:
- `project_id`
- `status`
- `source_type`
- `keyword`
- `page`
- `limit`

### GET /tasks/{taskId}
Task 상세 조회

### POST /tasks/{taskId}/execute
Task 실행 시작

#### Request
```json
{
  "team_preset": "default_ops_team",
  "requested_by": "user-id"
}
```

### POST /tasks/{taskId}/cancel
작업 취소

---

## 3.4 Workflow

### GET /workflow-runs/{runId}
워크플로 실행 상세 조회

### GET /tasks/{taskId}/workflow
Task에 연결된 워크플로 실행 조회

### GET /workflow-runs/{runId}/nodes
노드 실행 목록 조회

#### Response
```json
{
  "success": true,
  "data": {
    "run_id": "run-uuid",
    "nodes": [
      {
        "node_key": "control_agent",
        "department": "Control Agent",
        "status": "completed",
        "sequence_no": 1
      },
      {
        "node_key": "pm_agent",
        "department": "PM Agent",
        "status": "running",
        "sequence_no": 2
      }
    ]
  }
}
```

---

## 3.5 Approvals

### GET /approvals
승인 요청 목록 조회

쿼리 파라미터:
- `status=pending`
- `severity=high`
- `project_id`

### GET /approvals/{approvalId}
승인 상세 조회

### POST /approvals/{approvalId}/approve
승인 처리

#### Request
```json
{
  "user_id": "owner-user-id",
  "decision_note": "진행하세요",
  "decided_via": "dashboard"
}
```

### POST /approvals/{approvalId}/reject
반려 처리

#### Request
```json
{
  "user_id": "owner-user-id",
  "decision_note": "고객 발송 문구 수정 후 다시 요청",
  "decided_via": "telegram"
}
```

---

## 3.6 Knowledge

### GET /knowledge
전체 또는 프로젝트별 문서 목록 조회

쿼리 파라미터:
- `project_id`
- `keyword`
- `document_type`

### POST /projects/{projectId}/knowledge
문서 업로드

Form-data:
- `file`
- `title` (optional)
- `tags` (optional)

### GET /knowledge/{documentId}
문서 상세 조회

### POST /knowledge/{documentId}/summarize
문서 AI 요약 요청

### GET /knowledge/{documentId}/chunks
문서 청크 조회

---

## 3.7 Logs / Journal

### GET /logs
전체 로그 파일 또는 감사 로그 요약 조회

### GET /tasks/{taskId}/journal
Task 일지 조회

#### Response
```json
{
  "success": true,
  "data": {
    "task_id": "task-uuid",
    "entries": [
      {
        "timestamp": "2026-04-18T10:00:00Z",
        "actor_type": "agent",
        "actor_ref": "pm_agent",
        "event_type": "task_interpreted",
        "summary": "업무를 4단계로 분해했습니다."
      }
    ]
  }
}
```

### GET /logs/{logId}
로그 상세 조회

---

## 3.8 Departments

### GET /departments
부서 목록 조회

### POST /departments
부서 생성

### PATCH /departments/{departmentId}
부서 설정 수정

### PATCH /departments/{departmentId}/rules
부서 권한/승인 규칙 수정

---

## 3.9 Channels

### GET /channels
연결된 채널 목록

### POST /channels
채널 연결 생성

#### Request
```json
{
  "channel_type": "telegram",
  "account_name": "Founder Telegram",
  "auth_meta": {
    "bot_token": "***"
  }
}
```

### GET /channels/{channelId}/messages
채널 메시지 목록

### POST /channels/{channelId}/send
채널 메시지 발송

#### Request
```json
{
  "task_id": "task-uuid",
  "message_text": "작업이 완료되었습니다. 보고서를 확인해주세요."
}
```

### POST /channels/webhook/{channelType}
외부 채널 Webhook 수신 엔드포인트

---

## 4. WebSocket 명세

## 4.1 연결
```text
ws://localhost:8001/ws/{clientId}
```

### 연결 후 기본 메시지
```json
{
  "type": "hello",
  "client_id": "dashboard_123",
  "client_role": "dashboard"
}
```

---

## 4.2 클라이언트 → 서버 이벤트

### command.submit
채팅창에서 새 작업 제출
```json
{
  "type": "command.submit",
  "project_id": "project-uuid",
  "instruction_text": "신규 기능 기획안 작성해줘",
  "priority": "normal"
}
```

### workflow.subscribe
특정 run 구독
```json
{
  "type": "workflow.subscribe",
  "run_id": "run-uuid"
}
```

### approval.respond
실시간 승인 응답
```json
{
  "type": "approval.respond",
  "approval_id": "approval-uuid",
  "decision": "approved",
  "decision_note": "진행하세요",
  "decided_via": "dashboard"
}
```

### org_chart.request
회사 설명 기반 부서 구조 생성
```json
{
  "type": "org_chart.request",
  "project_id": "project-uuid",
  "company_description": "우리는 하이퍼로컬 슈퍼앱을 운영하는 스타트업입니다."
}
```

---

## 4.3 서버 → 클라이언트 이벤트

### task.created
```json
{
  "type": "task.created",
  "task_id": "task-uuid",
  "title": "신규 기능 기획안 작성",
  "status": "pending"
}
```

### workflow.started
```json
{
  "type": "workflow.started",
  "run_id": "run-uuid",
  "task_id": "task-uuid"
}
```

### workflow.node.updated
```json
{
  "type": "workflow.node.updated",
  "run_id": "run-uuid",
  "node": {
    "node_key": "planning_agent",
    "department": "Planning Agent",
    "status": "running",
    "sequence_no": 3
  }
}
```

### workflow.graph.snapshot
그래프 렌더링용 전체 스냅샷
```json
{
  "type": "workflow.graph.snapshot",
  "run_id": "run-uuid",
  "nodes": [],
  "edges": []
}
```

### approval.requested
```json
{
  "type": "approval.requested",
  "approval": {
    "approval_id": "approval-uuid",
    "task_id": "task-uuid",
    "request_title": "외부 고객 발송 승인 필요",
    "severity": "high",
    "proposed_action": "고객 응답 초안을 발송합니다."
  }
}
```

### task.report.generated
```json
{
  "type": "task.report.generated",
  "task_id": "task-uuid",
  "report_id": "report-uuid",
  "title": "최종 운영 보고서"
}
```

### task.completed
```json
{
  "type": "task.completed",
  "task_id": "task-uuid",
  "run_id": "run-uuid",
  "status": "completed"
}
```

### task.failed
```json
{
  "type": "task.failed",
  "task_id": "task-uuid",
  "reason": "Knowledge document missing"
}
```

---

## 5. 외부 채널 처리 규칙

### 인바운드 메시지 처리 순서
1. 채널 Webhook 수신
2. 메시지 저장
3. 사용자/권한 확인
4. 기존 Task 연결 여부 판단
5. 새 Task 생성 또는 기존 Task 업데이트
6. 오케스트레이터에 전달
7. 결과 회신 필요 여부 판단

### 승인 메시지 처리 규칙
채널에서 아래 형식을 허용:
- `APPROVE {approval_id}`
- `REJECT {approval_id} 사유`
- 버튼형 승인 링크

---

## 6. MVP 필수 API 세트
- Provider: GET/POST `/settings/provider`
- Projects: GET/POST `/projects`
- Tasks: POST `/tasks`, GET `/tasks/{id}`, POST `/tasks/{id}/execute`
- Workflow: GET `/tasks/{id}/workflow`
- Approvals: GET `/approvals`, POST `/approvals/{id}/approve`, POST `/approvals/{id}/reject`
- Knowledge: POST `/projects/{id}/knowledge`, GET `/knowledge`
- Logs: GET `/tasks/{id}/journal`
- Channels: GET `/channels`, POST `/channels`, POST `/channels/webhook/{channelType}`
- WebSocket: submit / subscribe / approval events

