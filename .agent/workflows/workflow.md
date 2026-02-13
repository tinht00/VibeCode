---
description: Tài liệu này định nghĩa cách thức tư duy, quy trình phát triển và cách giao tiếp với AI để đạt hiệu quả cao nhất.
---

# /workflow - Quy trình phát triển Zero-G

Nhắc AI áp dụng đúng quy trình tư duy Zero-G cho tác vụ hiện tại.

## Quy trình Zero-G (3 giai đoạn)

### Giai đoạn 1: Analysis (Phân tích - 30%)
1. **I/O Definition**: Xác định rõ Input/Output.
2. **Location Strategy**: Logic thuộc Frontend, Backend hay AI?
3. **Edge Cases**: Mất mạng? Dữ liệu rỗng? Tràn bộ nhớ?
4. **Dependencies**: Module cần gì để chạy?

### Giai đoạn 2: Implementation (Triển khai - 40%)
1. **Interface First**: Viết Interface trước.
2. **Core Logic & Test**: Viết Unit Test cho logic cốt lõi.
3. **Coding**: Viết code thực thi.
4. **Instant Refactor**: Hàm > 50 dòng → Tách ngay.

### Giai đoạn 3: Review (Kiểm tra - 30%)
- **Vue/Flutter/React**: Kiểm tra re-render không cần thiết.
- **Go/C++**: Kiểm tra memory footprint.
- **Python**: Profile thời gian thực thi.

## Cấu trúc phản hồi
1. **Phân tích**: Giải thích giải pháp (Tiếng Việt).
2. **Code**: Code đầy đủ, có comment.
3. **Lưu ý**: Cảnh báo lỗi tiềm ẩn, cách tối ưu.
