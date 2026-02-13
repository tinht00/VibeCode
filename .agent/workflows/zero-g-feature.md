---
description: zero-g_feature
---

# /zero-g-feature - Phát triển tính năng mới theo Zero-G

Quy trình đầy đủ để phát triển một tính năng mới từ A đến Z.

## Quy trình

### Bước 1: Thu thập ngữ cảnh
// turbo
1. Đọc `.agent/rules.md` và `.agent/project_settings.md`.
2. Đọc skills liên quan đến tech stack.
3. Đọc docs/README dự án hiện tại.

### Bước 2: Phân tích tính năng (Zero-G Analysis)
1. **I/O Definition**: Tính năng nhận gì? Trả về gì?
2. **Location Strategy**: Tính năng nằm ở đâu trong kiến trúc?
3. **Edge Cases**: Liệt kê ít nhất 3 tình huống lỗi.
4. **Dependencies**: Cần cài thêm package nào không?

### Bước 3: Tra cứu Context7
1. Resolve library ID cho các thư viện liên quan.
2. Query docs để tìm pattern/API phù hợp nhất.

### Bước 4: Lên kế hoạch (Implementation Plan)
1. Tạo `implementation_plan.md` chi tiết.
2. Liệt kê files cần tạo mới, chỉnh sửa, hoặc xóa.
3. Xin user review trước khi code.

### Bước 5: Triển khai (Atomic Implementation)
1. Tạo Interface/Type trước.
2. Viết logic + tests.
3. Refactor nếu hàm > 50 dòng.

### Bước 6: Kiểm tra & Tối ưu
1. Chạy tests.
2. Kiểm tra performance theo tech stack:
   - Vue/React/Flutter: Re-render check
   - Go/C++: Memory footprint
   - Python: Execution profiling
3. Cập nhật docs & comments.

### Bước 7: Walkthrough
1. Tạo `walkthrough.md` tóm tắt thay đổi.
2. Ghi lại kết quả tests.
