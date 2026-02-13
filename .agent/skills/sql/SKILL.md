---
name: sql
description: Best practices for SQL database interaction and design. Sử dụng khi cần viết query, tối ưu performance, thiết kế schema, hoặc xử lý transaction. Bao gồm query optimization, indexing, CTEs, window functions, ACID, và security.
---

# SQL Skill

## 1. Query Optimization (Performance)
*   **EXPLAIN / ANALYZE**: Luôn check execution plan cho các slow query. Tìm kiếm `Seq Scan` (quét toàn bộ bảng) -> Nếu thấy, cần thêm Index.
*   **Index Strategy**:
    *   Đánh index cột trong `WHERE`, `JOIN`, `ORDER BY`.
    *   Composite Index: Chú ý thứ tự cột (Leftmost prefix rule).
*   **Limit**: Luôn `LIMIT` số lượng bản ghi trả về khi query danh sách/search.
*   **Avoid N+1**: Sử dụng `JOIN` hoặc `Eager Loading` (trong ORM) thay vì query loop.

## 2. Advanced Techniques
*   **SARGable (Search ARGument ABLE)**:
    *   ❌ `WHERE YEAR(date_col) = 2023` (Không dùng index được).
    *   ✅ `WHERE date_col >= '2023-01-01' AND date_col < '2024-01-01'`.
*   **CTEs (Common Table Expressions)**: Dùng `WITH cte_name AS (...)` để làm rõ logic, thay thế subquery lồng nhau khó đọc.
*   **Window Functions**: `ROW_NUMBER()`, `RANK()`, `LEAD()`, `LAG()` cho các bài toán thống kê/phân trang phức tạp.

## 3. Transaction & ACID
*   **Atomicity**: Đảm bảo `BEGIN ... COMMIT/ROLLBACK` cho các cụm thao tác (vd: Chuyển tiền = Trừ A + Cộng B).
*   **Isolation Levels**: Hiểu rõ `Read Committed` (default thường gặp) vs `Serializable`. Cẩn thận Dirty Read, Phantom Read.
*   **Deadlock**: Khi update nhiều bảng, luôn access theo cùng một thứ tự định trước để tránh deadlock.

## 4. Database Design
*   **Normalization**: 3NF là tiêu chuẩn.
*   **Denormalization**: Chỉ dùng cho Reporting/Analytics tables (Data Warehouse) hoặc khi tối ưu Read cực gắt (cache counts).
*   **Data Types**: Chọn kiểu dữ liệu nhỏ nhất đủ dùng (`INT` vs `BIGINT`, `VARCHAR` vs `TEXT`, `TIMESTAMP` vs `DATETIME`).

## 5. Security
*   **SQL Injection**: 100% sử dụng **Parameterized Queries** / Prepared Statements. Không bao giờ cộng chuỗi trực tiếp.
