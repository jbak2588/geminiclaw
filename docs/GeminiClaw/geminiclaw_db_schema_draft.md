# GeminiClaw / AI Team OS DB 스키마 초안

## 1. 설계 원칙
- 모든 입력은 `task` 중심으로 정규화한다.
- 채팅, 채널, 승인, 문서, 로그를 각각 분리하되 `task_id`로 연결한다.
- AI Provider는 처음에는 1개만 사용하지만, 스키마는 추후 멀티 Provider 확장 가능하게 설계한다.
- 프로젝트와 부서 구조를 별도 관리하여 재사용성을 확보한다.

---

## 2. 핵심 엔티티 목록
- users
- workspaces
- ai_providers
- departments
- department_rules
- projects
- tasks
- workflow_runs
- workflow_nodes
- approvals
- channel_accounts
- channel_messages
- knowledge_documents
- knowledge_chunks
- attachments
- audit_logs
- task_reports

---

## 3. 테이블 정의

## 3.1 users
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 사용자 ID |
| email | varchar(255) unique | 로그인 이메일 |
| name | varchar(120) | 표시 이름 |
| role | varchar(50) | owner, manager, operator, viewer |
| status | varchar(30) | active, suspended |
| created_at | timestamptz | 생성일 |
| updated_at | timestamptz | 수정일 |

인덱스:
- unique(email)
- index(role)

---

## 3.2 workspaces
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 회사/조직 단위 워크스페이스 |
| name | varchar(150) | 워크스페이스 이름 |
| description | text | 설명 |
| owner_user_id | uuid FK users.id | 소유자 |
| created_at | timestamptz | 생성일 |
| updated_at | timestamptz | 수정일 |

---

## 3.3 ai_providers
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | Provider 설정 ID |
| workspace_id | uuid FK workspaces.id | 소속 워크스페이스 |
| provider_type | varchar(50) | gpt, gemini |
| label | varchar(100) | 화면 표시명 |
| api_key_encrypted | text | 암호화된 API Key |
| model_name | varchar(120) | 기본 모델명 |
| is_active | boolean | 현재 활성 Provider 여부 |
| created_at | timestamptz | 생성일 |
| updated_at | timestamptz | 수정일 |

제약:
- 초기 운영에서는 workspace당 active provider 1개

---

## 3.4 departments
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 부서 ID |
| workspace_id | uuid FK workspaces.id | 워크스페이스 |
| key | varchar(50) unique | control, pm, planning 등 |
| name | varchar(120) | 표시명 |
| description | text | 역할 설명 |
| prompt_template | text | 시스템 프롬프트 템플릿 |
| is_enabled | boolean | 활성화 여부 |
| display_order | int | UI 순서 |
| created_at | timestamptz | 생성일 |
| updated_at | timestamptz | 수정일 |

---

## 3.5 department_rules
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 규칙 ID |
| department_id | uuid FK departments.id | 대상 부서 |
| requires_approval | boolean | 기본 승인 필요 여부 |
| approval_level | varchar(30) | none, manager, owner |
| allowed_tools | jsonb | 허용 도구 목록 |
| blocked_actions | jsonb | 금지 액션 목록 |
| sop_document_id | uuid nullable | 연결된 SOP 문서 |
| created_at | timestamptz | 생성일 |
| updated_at | timestamptz | 수정일 |

---

## 3.6 projects
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 프로젝트 ID |
| workspace_id | uuid FK workspaces.id | 소속 |
| code | varchar(50) | 프로젝트 코드 |
| name | varchar(150) | 프로젝트명 |
| description | text | 설명 |
| status | varchar(30) | active, archived |
| created_by | uuid FK users.id | 생성자 |
| created_at | timestamptz | 생성일 |
| updated_at | timestamptz | 수정일 |

인덱스:
- index(workspace_id, status)
- unique(workspace_id, code)

---

## 3.7 tasks
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | Task ID |
| workspace_id | uuid FK workspaces.id | 소속 |
| project_id | uuid FK projects.id nullable | 프로젝트 |
| source_type | varchar(30) | dashboard, telegram, whatsapp, slack, email, api |
| source_ref | varchar(255) nullable | 외부 메시지/채널 참조값 |
| title | varchar(255) | 작업 제목 |
| instruction_text | text | 원본 지시문 |
| interpreted_goal | text | 시스템 해석 결과 |
| priority | varchar(20) | low, normal, high, urgent |
| status | varchar(30) | pending, running, waiting_approval, completed, failed, canceled |
| created_by_user_id | uuid FK users.id nullable | 사람 생성자 |
| assigned_control_department_id | uuid FK departments.id | 시작 부서 |
| started_at | timestamptz nullable | 시작일 |
| completed_at | timestamptz nullable | 완료일 |
| created_at | timestamptz | 생성일 |
| updated_at | timestamptz | 수정일 |

인덱스:
- index(project_id, status)
- index(source_type)
- index(created_at desc)

---

## 3.8 workflow_runs
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 실행 세션 ID |
| task_id | uuid FK tasks.id | 대상 Task |
| provider_id | uuid FK ai_providers.id | 사용 Provider |
| run_status | varchar(30) | created, running, waiting_approval, completed, failed |
| started_at | timestamptz | 시작일 |
| ended_at | timestamptz nullable | 종료일 |
| total_tokens | int nullable | 총 토큰 |
| estimated_cost | numeric(12,4) nullable | 예상 비용 |
| created_at | timestamptz | 생성일 |

---

## 3.9 workflow_nodes
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 노드 실행 ID |
| workflow_run_id | uuid FK workflow_runs.id | 실행 세션 |
| department_id | uuid FK departments.id | 담당 부서 |
| node_key | varchar(100) | unique node key |
| parent_node_id | uuid nullable FK workflow_nodes.id | 이전 노드 |
| sequence_no | int | 순서 |
| node_status | varchar(30) | queued, running, waiting_approval, completed, failed, skipped |
| input_summary | text | 입력 요약 |
| output_summary | text | 출력 요약 |
| raw_output | jsonb nullable | 원본 응답 일부 |
| started_at | timestamptz nullable | 시작일 |
| ended_at | timestamptz nullable | 종료일 |
| created_at | timestamptz | 생성일 |

인덱스:
- index(workflow_run_id, sequence_no)
- index(node_status)

---

## 3.10 approvals
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 승인 요청 ID |
| task_id | uuid FK tasks.id | 연결 Task |
| workflow_node_id | uuid FK workflow_nodes.id | 요청 노드 |
| requested_by_department_id | uuid FK departments.id | 요청 부서 |
| approval_type | varchar(50) | command_execution, external_send, deployment, document_release |
| severity | varchar(20) | low, medium, high, critical |
| request_title | varchar(255) | 제목 |
| request_reason | text | 요청 사유 |
| proposed_action | text | 실행 예정 내용 |
| status | varchar(30) | pending, approved, rejected, expired |
| decided_by_user_id | uuid nullable FK users.id | 결정자 |
| decided_via | varchar(30) nullable | dashboard, telegram, whatsapp, slack |
| decision_note | text nullable | 메모 |
| requested_at | timestamptz | 요청 시각 |
| decided_at | timestamptz nullable | 결정 시각 |

인덱스:
- index(status, severity)
- index(task_id)

---

## 3.11 channel_accounts
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 채널 연결 ID |
| workspace_id | uuid FK workspaces.id | 워크스페이스 |
| channel_type | varchar(30) | telegram, whatsapp, slack, email |
| account_name | varchar(150) | 표시명 |
| external_account_id | varchar(255) | 외부 계정 식별자 |
| auth_meta | jsonb | 토큰/설정 메타 |
| is_active | boolean | 활성화 여부 |
| created_at | timestamptz | 생성일 |
| updated_at | timestamptz | 수정일 |

---

## 3.12 channel_messages
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 메시지 ID |
| channel_account_id | uuid FK channel_accounts.id | 채널 연결 |
| task_id | uuid nullable FK tasks.id | 연결 Task |
| direction | varchar(20) | inbound, outbound |
| external_message_id | varchar(255) | 외부 메시지 ID |
| sender_name | varchar(150) nullable | 발신자 |
| sender_ref | varchar(255) nullable | 발신자 참조값 |
| message_text | text | 본문 |
| message_type | varchar(30) | text, image, file, command, approval |
| received_at | timestamptz nullable | 수신 시각 |
| sent_at | timestamptz nullable | 발송 시각 |
| created_at | timestamptz | 생성일 |

---

## 3.13 knowledge_documents
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 문서 ID |
| workspace_id | uuid FK workspaces.id | 워크스페이스 |
| project_id | uuid nullable FK projects.id | 프로젝트 |
| source_type | varchar(30) | upload, task_result, channel_file, generated |
| title | varchar(255) | 제목 |
| document_type | varchar(30) | pdf, image, markdown, note, report |
| storage_url | text | 파일 저장 경로 |
| summary | text nullable | 요약 |
| toc | text nullable | 목차 |
| tags | jsonb nullable | 태그 |
| uploaded_by_user_id | uuid nullable FK users.id | 업로드 사용자 |
| created_from_task_id | uuid nullable FK tasks.id | 생성 Task |
| created_at | timestamptz | 생성일 |
| updated_at | timestamptz | 수정일 |

---

## 3.14 knowledge_chunks
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 청크 ID |
| document_id | uuid FK knowledge_documents.id | 원본 문서 |
| chunk_index | int | 순서 |
| content | text | 청크 내용 |
| embedding_ref | varchar(255) nullable | 임베딩 참조값 |
| created_at | timestamptz | 생성일 |

---

## 3.15 attachments
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 첨부파일 ID |
| task_id | uuid nullable FK tasks.id | 연결 Task |
| channel_message_id | uuid nullable FK channel_messages.id | 연결 메시지 |
| file_name | varchar(255) | 원본 파일명 |
| mime_type | varchar(120) | MIME |
| storage_url | text | 저장 경로 |
| size_bytes | bigint | 크기 |
| uploaded_at | timestamptz | 업로드 시각 |

---

## 3.16 task_reports
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 결과 보고서 ID |
| task_id | uuid FK tasks.id | 대상 Task |
| report_type | varchar(30) | summary, final, failure, approval_context |
| title | varchar(255) | 제목 |
| body_markdown | text | 본문 |
| generated_by_department_id | uuid nullable FK departments.id | 생성 부서 |
| created_at | timestamptz | 생성일 |

---

## 3.17 audit_logs
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | 감사 로그 ID |
| workspace_id | uuid FK workspaces.id | 워크스페이스 |
| actor_type | varchar(20) | user, agent, system |
| actor_ref | varchar(255) | 사용자/부서/시스템 식별값 |
| event_type | varchar(80) | task_created, approval_requested, approval_approved 등 |
| task_id | uuid nullable FK tasks.id | 연결 Task |
| related_id | uuid nullable | 관련 리소스 ID |
| metadata | jsonb | 상세 메타 |
| created_at | timestamptz | 발생 시각 |

인덱스:
- index(event_type)
- index(task_id)
- index(created_at desc)

---

## 4. 관계 요약
```text
workspace
 ├─ users
 ├─ ai_providers
 ├─ departments ─ department_rules
 ├─ projects
 │   ├─ tasks
 │   │   ├─ workflow_runs ─ workflow_nodes
 │   │   ├─ approvals
 │   │   ├─ attachments
 │   │   ├─ channel_messages
 │   │   └─ task_reports
 │   └─ knowledge_documents ─ knowledge_chunks
 └─ audit_logs
```

---

## 5. 상태 Enum 초안

### task.status
- pending
- running
- waiting_approval
- completed
- failed
- canceled

### workflow_nodes.node_status
- queued
- running
- waiting_approval
- completed
- failed
- skipped

### approvals.status
- pending
- approved
- rejected
- expired

---

## 6. MVP 필수 테이블
초기 MVP에서 반드시 필요한 테이블:
- users
- workspaces
- ai_providers
- departments
- projects
- tasks
- workflow_runs
- workflow_nodes
- approvals
- channel_accounts
- channel_messages
- knowledge_documents
- audit_logs

