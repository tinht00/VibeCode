---
description: Sử dụng Context7 để tra cứu tài liệu mới nhất cho bất kỳ thư viện/framework nào.
---

# /ct7 - Tra cứu Context7

Sử dụng Context7 để tra cứu tài liệu mới nhất cho bất kỳ thư viện/framework nào.

## Quy trình

### Bước 1: Xác định thư viện cần tra cứu
Từ yêu cầu của user, xác định thư viện hoặc framework cần tìm tài liệu.

### Bước 2: Resolve Library ID
Gọi `resolve-library-id` với tên thư viện để lấy Context7-compatible library ID.

### Bước 3: Query Documentation
Gọi `query-docs` với library ID vừa lấy được và câu hỏi cụ thể.

### Lưu ý
- Tối đa **3 lần** gọi `query-docs` cho mỗi câu hỏi.
- Nếu không tìm được kết quả sau 3 lần, dùng thông tin tốt nhất hiện có.
- Ưu tiên các library có **Benchmark Score** cao và **Source Reputation: High**.