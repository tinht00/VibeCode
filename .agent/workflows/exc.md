---
description: Quy trình thực thi toàn diện - Đọc rules, skills, docs liên quan và sử dụng Context7 trước khi hành động.
---

# /exc - Execute with Full Context (Thực thi với đầy đủ ngữ cảnh)

Workflow này đảm bảo AI nắm đầy đủ ngữ cảnh trước khi thực hiện bất kỳ hành động nào.

## Quy trình thực hiện

### Bước 1: Đọc Rules & Project Settings
// turbo
1. Đọc file `.agent/rules.md` để nắm toàn bộ quy tắc kỹ thuật và quy trình làm việc.
2. Đọc file `.agent/project_settings.md` để hiểu hướng dẫn vận hành dự án.

### Bước 2: Quét Skills liên quan
// turbo
1. Liệt kê toàn bộ skills trong `.agent/skills/`.
2. Xác định skill nào phù hợp với tác vụ hiện tại dựa trên tên và mô tả.
3. Đọc `SKILL.md` của các skill phù hợp để lấy hướng dẫn chi tiết.

**Danh sách Skills hiện có:**
- `background-remover` - Xóa nền ảnh
- `clipart-prompt` - Tạo prompt sinh clipart
- `code-documentation` - Viết tài liệu code
- `frontend-design` - Thiết kế frontend chất lượng cao
- `image-enhancer` - Nâng cao chất lượng ảnh
- `python-development` - Phát triển Python hiện đại
- `skill-creator` - Tạo skill mới
- `video-downloader` - Tải video
- Các skill đơn lẻ: `cpp_skill.md`, `css_design_skill.md`, `documentation_skill.md`, `flutter_skill.md`, `golang_skill.md`, `python_skill.md`, `reactjs_skill.md`, `sql_skill.md`, `vue3_skill.md`

### Bước 3: Quét Docs dự án (nếu có)
// turbo
1. Tìm thư mục `docs/` hoặc `README.md` trong dự án đang làm việc.
2. Đọc các tài liệu API, kiến trúc, hoặc hướng dẫn liên quan đến tác vụ.
3. Nếu dự án có file `package.json`, `go.mod`, `requirements.txt`, hoặc `pubspec.yaml` → đọc để xác định tech stack.

### Bước 4: Tra cứu Context7
1. Sử dụng `resolve-library-id` của Context7 để tìm library ID cho công nghệ đang dùng.
2. Sử dụng `query-docs` để tra cứu tài liệu mới nhất về pattern/API cần dùng.
3. **Lưu ý**: Chỉ gọi tối đa 3 lần `query-docs` cho mỗi câu hỏi.

### Bước 5: Phân tích theo Zero-G
Sau khi đã thu thập đủ ngữ cảnh, áp dụng quy trình Zero-G:
1. **I/O Definition**: Input là gì? Output mong đợi là gì?
2. **Location Strategy**: Logic thuộc về đâu? (Frontend/Backend/AI)
3. **Edge Cases**: Dự đoán tình huống lỗi.
4. **Dependencies**: Module cần gì để chạy?

### Bước 6: Thực thi
1. Tạo Implementation Plan nếu tác vụ phức tạp.
2. Code theo nguyên tắc Atomic Commits.
3. Tuân thủ cấu trúc phản hồi: **Phân tích → Code → Lưu ý**.

## Checklist nhanh

```
☐ Đã đọc .agent/rules.md
☐ Đã đọc .agent/project_settings.md
☐ Đã quét và đọc skills liên quan
☐ Đã đọc docs dự án (nếu có)
☐ Đã tra cứu Context7 cho tech stack đang dùng
☐ Đã phân tích I/O, Edge Cases, Dependencies
☐ Sẵn sàng thực thi
```
