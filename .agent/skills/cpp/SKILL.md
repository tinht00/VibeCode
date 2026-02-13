---
name: cpp
description: Best practices for high-performance C++ development (C++17/20). Sử dụng khi cần viết, review, hoặc tối ưu code C++. Bao gồm Modern C++ standard, Memory management (Smart Pointers, RAII), Concurrency patterns, và Performance tooling.
---

# C++ Skill

## 1. Modern C++ Standard (C++17/20)
*   **Structured Binding**: `auto [x, y] = point;`
*   **FileSystem**: Sử dụng `std::filesystem` thay vì thư viện OS-specific.
*   **Concepts (C++20)**: Sử dụng Concepts để ràng buộc template parameters thay vì SFINAE khó đọc.

## 2. Memory Management (Rule of Zero/Five)
*   **Smart Pointers**: `std::unique_ptr` (default), `std::shared_ptr` (only when shared ownership needed).
*   **Rule of Zero**: Nếu class chỉ chứa các member tự quản lý memory (std::string, std::vector), không cần viết Destructor/Copy/Move.
*   **Rule of Five**: Nếu viết Destructor, phải viết đủ Copy Ctor, Copy Assignment, Move Ctor, Move Assignment.

## 3. Concurrency Patterns
*   **std::thread** vs **std::async**: Ưu tiên `std::async(std::launch::async, ...)` để lấy kết quả qua `std::future` an toàn hơn quản lý thread thủ công.
*   **Mutex/Lock**: Sử dụng `std::lock_guard` hoặc `std::scoped_lock` (C++17) để tránh deadlock và quên unlock.
*   **Atomics**: Sử dụng `std::atomic<T>` cho biến đếm hoặc flags đơn giản thay vì mutex nặng nề.

## 4. Performance & Tooling
*   **Build System**: CMake là tiêu chuẩn. Học cách dùng `FetchContent` hoặc package manager `Conan`/`Vcpkg`.
*   **Static Analysis**: Tích hợp `Clang-tidy` và `Cppcheck`.
*   **Dynamic Analysis**: Chạy `Valgrind` (Linux) hoặc Application Verifier (Windows) để tìm mem leak.
*   **Optimization**:
    *   Tránh copy: `const T&` cho input params.
    *   Reserve vector: `v.reserve(n)` trước khi push_back nhiều phần tử.

## 5. Safety Checklist
*   Check bounds: `vec.at(i)` safer than `vec[i]` if unsure.
*   Initialize variables: Luôn khởi tạo biến `int x = 0;`.
*   Avoid `undefined behavior`: Không dereference null ptr, không chia cho 0, không signed integer overflow.
