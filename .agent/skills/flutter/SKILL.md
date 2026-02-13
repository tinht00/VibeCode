---
name: flutter
description: Best practices for Flutter mobile app development. Sử dụng khi cần viết, review, hoặc tối ưu Flutter/Dart code. Bao gồm Clean Architecture, BLoC state management, performance tuning, platform channels, và testing.
---

# Flutter Skill

## 1. Clean Architecture
*   **Presenation Layer**: Widgets, BLoC/Cubit. Chỉ lo hiển thị và nhận event.
*   **Domain Layer**: Entities, Usecases, Repository Interfaces. Pure Dart code, không phụ thuộc UI hay API framework.
*   **Data Layer**: Repositories Implementations, Data Sources (API, Local DB), DTOs (Models).

## 2. Advanced State Management (BLoC)
*   **Events**: Định nghĩa event rõ ràng (`LoadUser`, `UpdateName`).
*   **States**: Các trạng thái UI (`UserLoading`, `UserLoaded`, `UserError`).
*   **BlocObserver**: Logging toàn bộ transition state để debug dễ dàng.

## 3. Performance Tuning
*   **RepaintBoundary**: Bọc các animation complex hoặc widget cập nhật liên tục để tránh repaint lại toàn bộ cây cha.
*   **const Widgets**: Tối đa hóa việc dùng `const` constructor.
*   **ListView.builder**: Dùng cho list dài, không dùng `ListView` thường (sẽ render all items).

## 4. Native Integration (Platform Channels)
*   **MethodChannel**: Gọi hàm native từ Dart.
    *   *Android (Kotlin)*: Handle MethodCall trả về Result.
    *   *iOS (Swift)*: Handle FlutterMethodCall.
*   **Type Safety**: Cẩn thận kiểu dữ liệu khi truyền qua bridge (Map, List, String).

## 5. Asynchronous & Networking
*   **Dio vs Http**: Ưu tiên **Dio** vì support interceptors, cancellation, file download tốt hơn.
*   **Serialization**: Sử dụng `json_serializable` và `freezed` để generate code parse JSON an toàn, support immutable models.

## 6. CI/CD & Tooling
*   **FVM**: Sử dụng Flutter Version Management để quản lý SDK version cho team.
*   **Linter**: `flutter_lints` (strict mode).
*   **Testing**:
    *   Unit Test: logic BLoC/Usecase.
    *   Widget Test: render UI nhỏ.
    *   Integration Test: `patrol` hoặc `flutter_driver` cho luồng E2E.
