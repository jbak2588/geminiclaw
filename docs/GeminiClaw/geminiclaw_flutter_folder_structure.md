# GeminiClaw / AI Team OS Flutter 폴더 구조 제안

## 1. 구조 설계 목표
- 대시보드형 데스크톱/웹 앱에 적합한 구조
- 기능별 분리(Feature-first)
- Provider, WebSocket, REST, 상태관리, UI를 분리
- `geminiclaw`의 현재 Team OS 방향을 유지하면서 확장 가능하게 설계

---

## 2. 최상위 구조

```text
lib/
├─ app/
│  ├─ app.dart
│  ├─ bootstrap.dart
│  ├─ router/
│  │  ├─ app_router.dart
│  │  └─ route_names.dart
│  ├─ theme/
│  │  ├─ app_theme.dart
│  │  ├─ app_colors.dart
│  │  └─ app_text_styles.dart
│  └─ layout/
│     ├─ shell_frame.dart
│     ├─ left_sidebar.dart
│     ├─ top_bar.dart
│     └─ right_live_feed.dart
│
├─ core/
│  ├─ config/
│  │  ├─ env.dart
│  │  ├─ api_config.dart
│  │  └─ channel_config.dart
│  ├─ constants/
│  │  ├─ app_constants.dart
│  │  ├─ task_status.dart
│  │  └─ approval_levels.dart
│  ├─ models/
│  │  ├─ api_result.dart
│  │  ├─ paged_response.dart
│  │  └─ app_notification.dart
│  ├─ network/
│  │  ├─ http_client.dart
│  │  ├─ websocket_client.dart
│  │  ├─ api_exception.dart
│  │  └─ auth_interceptor.dart
│  ├─ services/
│  │  ├─ provider_service.dart
│  │  ├─ notification_service.dart
│  │  ├─ file_upload_service.dart
│  │  └─ approval_bridge_service.dart
│  ├─ storage/
│  │  ├─ secure_storage.dart
│  │  ├─ local_cache.dart
│  │  └─ session_store.dart
│  ├─ utils/
│  │  ├─ date_formatter.dart
│  │  ├─ json_utils.dart
│  │  └─ color_utils.dart
│  └─ widgets/
│     ├─ app_card.dart
│     ├─ loading_indicator.dart
│     ├─ empty_state.dart
│     ├─ status_chip.dart
│     └─ confirm_dialog.dart
│
├─ features/
│  ├─ dashboard/
│  │  ├─ data/
│  │  │  ├─ dashboard_repository.dart
│  │  │  └─ dashboard_remote_source.dart
│  │  ├─ domain/
│  │  │  ├─ dashboard_summary.dart
│  │  │  └─ recent_activity.dart
│  │  ├─ presentation/
│  │  │  ├─ dashboard_screen.dart
│  │  │  ├─ dashboard_controller.dart
│  │  │  └─ widgets/
│  │  │     ├─ summary_cards.dart
│  │  │     ├─ pending_approvals_panel.dart
│  │  │     └─ recent_tasks_list.dart
│  │
│  ├─ command_center/
│  │  ├─ data/
│  │  │  ├─ command_repository.dart
│  │  │  └─ command_remote_source.dart
│  │  ├─ domain/
│  │  │  ├─ command_message.dart
│  │  │  └─ command_session.dart
│  │  ├─ presentation/
│  │  │  ├─ command_chat_screen.dart
│  │  │  ├─ command_controller.dart
│  │  │  └─ widgets/
│  │  │     ├─ command_timeline.dart
│  │  │     ├─ command_input_bar.dart
│  │  │     └─ provider_status_header.dart
│  │
│  ├─ workflow/
│  │  ├─ data/
│  │  │  ├─ workflow_repository.dart
│  │  │  └─ workflow_ws_source.dart
│  │  ├─ domain/
│  │  │  ├─ workflow_run.dart
│  │  │  ├─ workflow_node.dart
│  │  │  └─ node_edge.dart
│  │  ├─ presentation/
│  │  │  ├─ workflow_live_screen.dart
│  │  │  ├─ workflow_controller.dart
│  │  │  └─ widgets/
│  │  │     ├─ workflow_graph_canvas.dart
│  │  │     ├─ node_detail_panel.dart
│  │  │     └─ run_status_header.dart
│  │
│  ├─ approvals/
│  │  ├─ data/
│  │  │  ├─ approval_repository.dart
│  │  │  └─ approval_remote_source.dart
│  │  ├─ domain/
│  │  │  └─ approval_request.dart
│  │  ├─ presentation/
│  │  │  ├─ approval_center_screen.dart
│  │  │  ├─ approval_controller.dart
│  │  │  └─ widgets/
│  │  │     ├─ approval_list.dart
│  │  │     ├─ approval_detail_panel.dart
│  │  │     └─ approval_popup_listener.dart
│  │
│  ├─ projects/
│  │  ├─ data/
│  │  │  ├─ projects_repository.dart
│  │  │  └─ projects_remote_source.dart
│  │  ├─ domain/
│  │  │  └─ project.dart
│  │  ├─ presentation/
│  │  │  ├─ projects_screen.dart
│  │  │  ├─ project_detail_screen.dart
│  │  │  ├─ projects_controller.dart
│  │  │  └─ widgets/
│  │  │     ├─ project_card.dart
│  │  │     └─ project_tabs.dart
│  │
│  ├─ knowledge/
│  │  ├─ data/
│  │  │  ├─ knowledge_repository.dart
│  │  │  └─ knowledge_remote_source.dart
│  │  ├─ domain/
│  │  │  └─ knowledge_document.dart
│  │  ├─ presentation/
│  │  │  ├─ knowledge_library_screen.dart
│  │  │  ├─ knowledge_controller.dart
│  │  │  └─ widgets/
│  │  │     ├─ document_card.dart
│  │  │     ├─ upload_dialog.dart
│  │  │     └─ document_detail_panel.dart
│  │
│  ├─ logs/
│  │  ├─ data/
│  │  │  ├─ logs_repository.dart
│  │  │  └─ logs_remote_source.dart
│  │  ├─ domain/
│  │  │  ├─ audit_log.dart
│  │  │  └─ task_journal_entry.dart
│  │  ├─ presentation/
│  │  │  ├─ logs_screen.dart
│  │  │  ├─ logs_controller.dart
│  │  │  └─ widgets/
│  │  │     ├─ journal_timeline.dart
│  │  │     ├─ log_filter_bar.dart
│  │  │     └─ log_detail_view.dart
│  │
│  ├─ channels/
│  │  ├─ data/
│  │  │  ├─ channels_repository.dart
│  │  │  └─ channels_remote_source.dart
│  │  ├─ domain/
│  │  │  ├─ channel_account.dart
│  │  │  └─ channel_message.dart
│  │  ├─ presentation/
│  │  │  ├─ channel_hub_screen.dart
│  │  │  ├─ channels_controller.dart
│  │  │  └─ widgets/
│  │  │     ├─ channel_status_card.dart
│  │  │     ├─ inbound_message_list.dart
│  │  │     └─ outbound_result_panel.dart
│  │
│  ├─ departments/
│  │  ├─ data/
│  │  │  ├─ departments_repository.dart
│  │  │  └─ departments_remote_source.dart
│  │  ├─ domain/
│  │  │  ├─ department.dart
│  │  │  └─ department_rule.dart
│  │  ├─ presentation/
│  │  │  ├─ departments_screen.dart
│  │  │  ├─ departments_controller.dart
│  │  │  └─ widgets/
│  │  │     ├─ department_list.dart
│  │  │     ├─ department_editor.dart
│  │  │     └─ sop_editor.dart
│  │
│  └─ settings/
│     ├─ data/
│     │  ├─ settings_repository.dart
│     │  └─ settings_remote_source.dart
│     ├─ domain/
│     │  └─ provider_config.dart
│     ├─ presentation/
│     │  ├─ settings_screen.dart
│     │  ├─ settings_controller.dart
│     │  └─ widgets/
│     │     ├─ provider_form.dart
│     │     ├─ channel_form.dart
│     │     └─ security_policy_form.dart
│
└─ main.dart
```

---

## 3. 상태관리 제안
권장:
- `Riverpod` 또는 `Bloc` 중 하나로 통일
- 현재 데스크톱 대시보드형 앱에는 **Riverpod + StateNotifier/AsyncNotifier**가 관리와 테스트 측면에서 편리

### 상태 분리 원칙
- 화면 상태: 각 feature controller
- 전역 상태: 세션, 사용자, 알림, 실시간 연결 상태
- 실시간 이벤트: WebSocket stream → feature controller 분배

---

## 4. 주요 공통 모델 위치
`core/models`는 진짜 공통만 두고, 기능 전용 모델은 feature 내부에 둔다.

예:
- `Task`, `WorkflowRun`, `ApprovalRequest`는 서로 연관이 크므로 해당 feature domain에 둔다.
- `AppNotification`, `ApiResult` 같은 범용 타입만 core로 둔다.

---

## 5. 추천 라우팅 구조

### route_names.dart
- `/dashboard`
- `/command`
- `/workflow`
- `/approvals`
- `/projects`
- `/projects/:id`
- `/knowledge`
- `/logs`
- `/channels`
- `/departments`
- `/settings`

### shell_frame.dart 역할
- 사이드바
- 탑바
- 우측 Live Feed
- 본문 child 교체

---

## 6. 현재 `geminiclaw`에서 우선 분리해야 할 파일
현재 `main.dart`에 너무 많은 기능이 모여 있으므로 최소한 아래로 먼저 분리한다.

### 1차 분리 대상
- `PiChatView` → `features/command_center/presentation/command_chat_screen.dart`
- `TeamOrchestratorView` → `features/workflow/presentation/workflow_live_screen.dart`
- `KanbanTask` → `features/workflow/domain/workflow_task.dart`
- 승인 팝업 로직 → `features/approvals/presentation/widgets/approval_popup_listener.dart`
- 공통 WebSocket 연결 → `core/network/websocket_client.dart`

---

## 7. MVP 우선 구현 순서
1. `app/layout` 셸 분리
2. `command_center` 분리
3. `workflow` 분리
4. `approvals` 분리
5. `logs`/`knowledge` 연결
6. `channels` 추가
7. `departments`/`settings` 고도화

---

## 8. Planner용 쉬운 설명
이 구조의 핵심은 “화면마다 파일을 나누고, 네트워크/상태/화면을 분리해서 나중에 기능이 늘어나도 무너지지 않게 만드는 것”입니다.
즉 지금의 큰 `main.dart`를 회사 조직처럼 부서별 폴더로 나누는 방식입니다.

