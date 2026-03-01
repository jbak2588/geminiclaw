# 

> **점검 대상**: 백엔드 
> 
> functions-v2/index.js (3,148줄) + 프런트엔드 Dart 전체  
> **점검 일시**: 2026-02-26

---

## 🔴 CRITICAL (앱 중단 가능성 / 보안 위험)

### 1. `confirmAccountDeletion` 관리자 권한 검증 미적용 — _보안 취약점_

**파일**: 

index.js

js

// 1. 관리자 권한 확인 (선택 사항, 보안 강화 시 필요)

// if (!request.auth.token.admin) throw new HttpsError('permission-denied', 'Admin required.');

CAUTION

관리자 권한 확인이 **주석 처리**되어 있습니다. **인증된 아무 사용자라도** `targetUid`만 알면 다른 사용자의 Auth 계정 + Firestore 문서 + Storage 파일을 완전히 삭제할 수 있습니다.

**수정 방안**: Custom Claims 기반 admin 검증을 활성화하거나, Firestore에서 role 확인:

js

const callerDoc = await db.collection("users").doc(request.auth.uid).get();

if (callerDoc.data()?.role !== "admin") throw new HttpsError('permission-denied', 'Admin only.');

---

### 2. `calculateTrustScore` ↔ `autoSuspendUser` 무한 트리거 루프 위험

**파일**: 

index.js

두 함수 모두 `users/{userId}` 문서의 `onDocumentUpdated`에 바인딩되어 있습니다:

|함수|변경하는 필드|
|---|---|
|`calculateTrustScore`|`trustScore`, `trustLevel`, `currentMannerScore`|
|`autoSuspendUser`|`userStatus`, `suspendedAt`, `suspensionReason`|

현재 가드 조건으로 무한 루프는 대부분 차단되지만, `autoSuspendUser`가 `userStatus`를 `suspended`로 변경할 때:

1. `calculateTrustScore`가 다시 트리거됨 (불필요한 재계산)
2. `autoSuspendUser`가 다시 트리거됨 (
    
    hideAllUserContent 재실행 가능)

WARNING

hideAllUserContent 함수에서 다수 문서를 batch 업데이트하므로, 대량 데이터 보유 사용자에서 Cloud Functions 타임아웃(60초 기본)이 발생할 수 있습니다.

**수정 방안**:

- `autoSuspendUser`의 콘텐츠 숨김 로직에 `status: "hidden_by_admin"` 체크 외에 **이미 처리 완료 플래그**(`contentHiddenAt` 등) 추가
- 또는 두 함수를 하나로 합치고 변경 감지를 통합

---

### 3. `NotificationService.init()` 에서 `rethrow` — _앱 시작 시 크래시_

**파일**: 

notification_service.dart

dart

} catch (e, st) {

  Logger.error('FCM init failed during startup', error: e, stackTrace: st);

  rethrow; // ← 이 rethrow로 앱이 시작 자체가 실패할 수 있음

}

CAUTION

FCM 권한 거부, APNS 토큰 실패, 네트워크 오류 시 **앱이 아예 시작되지 않습니다**.

**수정 방안**: `rethrow` 제거하고 에러를 graceful하게 처리:

dart

} catch (e, st) {

  Logger.error('FCM init failed during startup', error: e, stackTrace: st);

  // FCM 초기화 실패는 앱 기능에 치명적이지 않으므로 계속 진행

}

---

### 4. 

_handleDeepLink 비동기 Timer 내 네비게이션 — _크래시 가능_

**파일**: 

main.dart

dart

Timer.periodic(const Duration(milliseconds: 500), (timer) async {

  ...

  final postDoc = await FirebaseFirestore.instance.collection('posts').doc(postId).get();

  ...

  navState.push(MaterialPageRoute(...));

  ...

  if (!navigated && attempts >= 10) { timer.cancel(); }

});

문제점:

- Timer 콜백 내 async 호출이 **에러를 제대로 전파하지 않음** (try-catch가 Timer를 감싸므로 내부 async 에러를 잡지 못함)
- `navigated` 변수가 콜백 내부에서만 사용되어 외부 timer 취소 조건과 분리됨
- 네비게이터 `push` 성공 여부와 무관하게 timer가 취소됨

**수정 방안**: Timer 대신 재귀적 delayed Future 사용, 또는 `WidgetsBinding.instance.addPostFrameCallback` 활용

---

## 🟠 HIGH (기능 오작동 / 데이터 비동기 문제)

### 5. 이미지 다운로드 코드 3회 중복

**파일**: 

index.js

urlToGenerativePart() 함수가 이미 존재함에도, `initialproductanalysis`(L1075-1119)와 `generatefinalreport`(L1463-1507)에 **동일한 인라인 코드**가 남아 있습니다.

**영향**:

- 하나를 수정하면 나머지를 빠뜨리기 쉬움 (이미 
    
    urlToGenerativePart에는 `finally { clearTimeout(to) }` 패턴이 있지만 인라인 버전에는 없음)
- `AbortController` 사용 패턴이 미묘하게 다름

**수정 방안**: `initialproductanalysis`와 `generatefinalreport`의 인라인 이미지 다운로드를 

urlToGenerativePart() 호출로 교체

---

### 6. `startFriendChat` 일일 한도 검증 — _Race Condition_

**파일**: 

index.js

js

const chatLimits = userDoc.data()?.chatLimits || {};

const currentCount = chatLimits.findFriendCount || 0;

// ... count 확인 후 FieldValue.increment(1) 사용

`userDoc.get()`으로 현재 카운트를 읽고, 별도 

update()로 증가시키므로 두 동시 요청이 모두 `count=4`를 읽고 둘 다 통과할 수 있습니다.

**수정 방안**: Firestore 트랜잭션(`db.runTransaction`)으로 읽기+쓰기를 원자적으로 처리

---

### 7. FCM 토큰 누적 — _Stale 토큰으로 인한 전송 실패_

**파일**: 

notification_service.dart

dart

await _db.collection('users').doc(user.uid).set({

  'fcmTokens': FieldValue.arrayUnion([token])

}, SetOptions(merge: true));

토큰은 **추가만** 되고 **삭제되지 않습니다**. 사용자가 앱을 재설치하거나 기기를 변경하면 이전 토큰이 무효화되지만 배열에 남습니다.

**영향**:

- `sendEachForMulticast` 호출 시 무효 토큰이 포함되어 Firebase Messaging API 오류 증가
- `fcmTokens` 배열이 무한히 커짐

**수정 방안**:

- 토큰 저장 시 기존 토큰을 교체하는 로직 추가 (`arrayRemove` + `arrayUnion`)
- 또는 `sendEachForMulticast` 결과에서 실패한 토큰을 정리

---

### 8. 백엔드-프런트엔드 필드 불일치 (sellerId vs userId)

**파일**: 

index.js

js

sellerId: productData.userId || productData.sellerId || "unknown",

백엔드 코드에서 `userId`와 `sellerId`를 혼용합니다:

- `onProductStatusPending` (L353): `const sellerId = after.userId;`
- `onProductStatusResolved` (L641): `const sellerId = after.userId;`
- `enhanceProductWithAi` (L1751): `sellerId: productData.sellerId || request.auth.uid`
- `verifyProductOnSite` (L2596): `sellerId: productData.userId || productData.sellerId || "unknown"`

IMPORTANT

products 컬렉션에서 판매자 ID 필드가 `userId`인지 `sellerId`인지 통일되지 않으면 `ai_cases` 문서의 `sellerId`가 `undefined`가 될 수 있습니다.

---

### 9. `onProductStatusPending`이 `onDocumentWritten` 사용 — 과도한 트리거

**파일**: 

index.js

js

exports.onProductStatusPending = onDocumentWritten(

    {document: "products/{productId}", region: "asia-southeast2"},

`onDocumentWritten`은 create, update, delete **모두** 트리거됩니다. 이 함수는 status가 "pending"으로 **변경**될 때만 동작하므로 `onDocumentUpdated`로 충분합니다. 불필요한 Cold Start와 실행 비용이 발생합니다.

---

## 🟡 MEDIUM (성능 최적화 / 코드 품질)

### 10. Cloud Functions 메모리 과할당

**파일**: 

index.js

js

const CALL_OPTS = {

  memory: "1GiB",

  timeoutSeconds: 300,

};

모든 onCall 함수가 동일한 `CALL_OPTS`(1GiB, 300초)를 사용합니다:

- `startFriendChat`: 단순 Firestore 읽기/쓰기 → **256MB, 30초**로 충분
- `confirmAccountDeletion`: Storage 삭제 + Auth 삭제 → **512MB, 60초**로 충분
- AI 함수(`initialproductanalysis`, `generatefinalreport` 등): 이미지 처리 → 1GiB 적절

TIP

함수별 개별 옵션을 지정하면 Cold Start가 빨라지고 비용이 절감됩니다.

---

### 11. 

main.dart — `_subAppLinks` 메모리 누수

**파일**: 

main.dart

dart

final AppLinks _appLinks = AppLinks();

StreamSubscription<Uri>? _subAppLinks; // ignore: unused_element

`_subAppLinks`가 전역 변수이고 `cancel()`이 호출되지 않습니다. 앱 수명 동안 유지되므로 실질적 누수는 아니지만, **테스트 환경이나 Hot Restart 시 이전 구독이 남아** 중복 네비게이션이 발생할 수 있습니다.

---

### 12. 

_uploadFeedbackToFirebase — BuildContext 비동기 사용

**파일**: 

main.dart

`context.mounted` 체크가 있어 대부분 안전하지만, `BuildContext`를 비동기 함수의 파라미터로 받는 패턴 자체가 Flutter 권장 사항에 어긋납니다.

---

### 13. `enforceAppCheck: false` — 모든 함수에서 App Check 미적용

**파일**: 

index.js

js

enforceAppCheck: false,

WARNING

프로덕션에서는 `enforceAppCheck: true`로 변경해야 합니다. 현재 상태에서는 누구나 직접 HTTP 요청으로 Cloud Functions를 호출할 수 있습니다.

---

### 14. 

product_detail_screen.dart — 1,657줄의 거대 위젯

**파일**: 

product_detail_screen.dart

단일 파일에 1,657줄, 32개 메서드가 포함되어 있습니다. 주요 메서드들:

- build(), 
    
    _showMarkAsSoldDialog(), 
    
    _executeReservation(), `_buildFloatingActionButton()` 등

유지보수와 테스트가 극히 어렵고, **rebuild 성능에 영향**을 줍니다.

**권장**: 하위 위젯(예: `ProductImageGallery`, `SellerInfoSection`, `AiReportSection`)으로 분리

---

### 15. 

_increaseViewCount() — 조회수 중복 증가

**파일**: 

product_detail_screen.dart

initState()에서 

_increaseViewCount()를 호출하는데, 화면을 push/pop/push 하면 **동일 사용자가 조회수를 무한히 올릴 수** 있습니다.

---

## 🟢 LOW (개선 권장)

### 16. `JSON.stringify` 비교 (Deep Equality)

index.js L870, 

L1878, 

L1950

Firestore 객체를 `JSON.stringify`로 비교합니다. 키 순서가 다르면 같은 값도 다르다고 판단될 수 있습니다. `lodash.isEqual` 등 deep comparison 유틸리티 사용 권장.

---

### 17. 하드코딩된 리전 중복

index.js: `setGlobalOptions({region: "asia-southeast2"})` 설정에도 불구하고, 각 함수 정의마다 `region: "asia-southeast2"`를 반복합니다. 전역 설정으로 충분하므로 개별 지정 제거 가능.

---

### 18. Dart 분석 미실행 경고 가능성

analysis_options.yaml이 존재하지만, 

main.dart에 `// ignore: unused_element`, `// ignore: unused_field` 주석이 있어 lint 억제가 남용되고 있습니다.

---

## 📊 백엔드-프런트엔드 동기화 현황

|도메인|백엔드 필드|프런트엔드 사용|동기화 상태|
|---|---|---|---|
|상품 AI 리포트|`aiReport` (V3 JSON)|product_detail_screen.dart|✅ 호환|
|FCM 토큰 저장|`fcmTokens` (Array)|notification_service.dart|⚠️ 삭제 없음|
|알림 하위 컬렉션|`/users/{uid}/notifications`|notification_service.dart|✅ 일치|
|판매자 ID|`userId` / `sellerId` 혼용|`product_model.dart`|❌ 불일치|
|Trust Score|`trustScore`, `trustLevel`|Dart 위젯에서 읽기|✅ 일치|
|PushPrefs|`pushPrefs.subscribedTopics`|프런트 설정 화면|✅ 일치|
|AI Case|`lastAiCaseId`, `lastAiVerdict`|프런트 표시|✅ 일치|
|채팅 한도|`chatLimits.findFriendCount`|Dart에서 결과 표시|⚠️ 비원자적|
|App Check|`enforceAppCheck: false`|Flutter에서 활성화됨|⚠️ 서버 미적용|

---

## 🎯 우선순위별 액션 플랜

|우선순위|항목|예상 영향도|작업 난이도|
|---|---|---|---|
|🔴 P0|#1 관리자 권한 검증 활성화|보안|⭐ 쉬움|
|🔴 P0|#3 NotificationService rethrow 제거|앱 시작 보장|⭐ 쉬움|
|🔴 P0|#13 enforceAppCheck: true 활성화|보안|⭐⭐ 보통|
|🔴 P1|#2 트리거 루프 위험 제거|안정성|⭐⭐ 보통|
|🔴 P1|#4 딥링크 Timer 개선|크래시 방지|⭐⭐ 보통|
|🟠 P2|#6 채팅 한도 Race Condition|기능 정확성|⭐⭐ 보통|
|🟠 P2|#7 FCM 토큰 정리|알림 안정성|⭐⭐ 보통|
|🟠 P2|#8 sellerId/userId 통일|데이터 정합성|⭐⭐⭐ 까다로움|
|🟡 P3|#5, #9, #10, #11 최적화|비용 절감|⭐ 쉬움|
|🟢 P4|#14, #15, #16, #17, #18|코드 품질|⭐⭐ 보통|

CommentCtrl+Alt+M