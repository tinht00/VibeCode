# Hướng Dẫn Vận Hành Agent (Project Instructions)

Chào mừng bạn tham gia dự án Antigravity. Đây là các hướng dẫn vận hành bắt buộc để đảm bảo sự thống nhất và hiệu quả trong công việc.

## 1. Ưu Tiên Hàng Đầu
Trước khi thực hiện **BẤT KỲ** hành động nào (phân tích, viết code, sửa code), bạn **BẮT BUỘC** phải:
1.  Đọc và hiểu tệp tin cấu hình tại `.agent/rules.md`.
2.  Kiểm tra xem có Skill (Kỹ năng) nào trong `.agent/skills/` phù hợp với tác vụ hiện tại không. Nếu có, hãy đọc nó.

## 2. Ngôn Ngữ Giao Tiếp
*   **Tiếng Việt** là ngôn ngữ bắt buộc cho mọi phản hồi, giải thích, và kế hoạch (Implementation Plan).
*   Các thuật ngữ kỹ thuật tiếng Anh có thể được giữ nguyên nếu phổ biến (vd: Database, Frontend, Backend) hoặc kèm chú thích tiếng Việt.

## 3. Quy Trình Tư Duy & Thực Thi
Tuân thủ nghiêm ngặt quy trình "Zero-G" đã định nghĩa trong `rules.md`:
*   **Analysis**: Phân tích kỹ đầu vào, đầu ra, và các trường hợp lỗi trước khi code.
*   **Implementation**: Code từng phần nhỏ (Atomic), rõ ràng, tường minh.
*   **Review**: Tự kiểm tra lại code về mặt hiệu năng và logic trước khi báo cáo hoàn thành.

## 4. Cấu Trúc Phản Hồi
Luôn tuân thủ cấu trúc:
1.  **Phân tích**: Cách tiếp cận vấn đề (bằng Tiếng Việt).
2.  **Code/Hành động**: Nội dung chính.
3.  **Lưu ý**: Các cảnh báo hoặc điểm cần tối ưu.

Hãy làm việc một cách **Strict & Explicit** (Chặt chẽ & Tường minh).

## 5. Personalization Cho Research Bằng NotebookLM
- Khi tác vụ có yếu tố nghiên cứu/tổng hợp bối cảnh lớn, ưu tiên truy xuất theo nhịp thay vì nạp toàn bộ tài liệu vào context.
- Nhịp truy xuất chuẩn:
  1. Preflight (auth, notebook, khả năng truy cập nguồn).
  2. Query hẹp theo mục tiêu task.
  3. Interrogate (mâu thuẫn, khoảng trống, độ tin cậy).
  4. Generate output sau quality gate.
- Quality gate bắt buộc trước khi kết luận:
  - Có dẫn chứng cho các nhận định chính.
  - Nêu rõ phần chưa đủ bằng chứng.
  - Có mức tự tin và rủi ro còn lại.
