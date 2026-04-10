# AGENTS - VibeCode Workspace

## 1. Mục tiêu làm việc
- Giữ giao tiếp tiếng Việt rõ ràng, có dấu.
- Tập trung vào chất lượng triển khai, tài liệu, và khả năng debug dài hạn.

## 2. Trình tự bắt buộc trước khi thực thi
1. Đọc [`project_settings.md`](./project_settings.md).
2. Đọc [`rules.md`](./rules.md).
3. Xác định skill phù hợp trong thư mục `.agent/skills/` và áp dụng khi cần.

## 3. Quy ước ngôn ngữ và plan
- Trả lời người dùng bằng tiếng Việt có dấu.
- Khi tạo plan để trình bày, dùng tiếng Việt.
- Khi người dùng duyệt plan, chuyển plan sang tiếng Anh ở bước nội bộ, rà soát lại nhiều lần rồi mới triển khai.

## 4. Quy ước tài liệu
- Mỗi thay đổi về chức năng, logic, hoặc luồng phải cập nhật docs trong cùng phiên làm việc.
- Mỗi lỗi quan trọng cần được ghi lại kèm:
  - Triệu chứng.
  - Nguyên nhân gốc.
  - Cách khắc phục.
  - Cách phòng ngừa tái diễn (nếu có).
- Nội dung docs xuất cho người dùng là tiếng Việt có dấu.

## 5. Tuân thủ cấu trúc dự án
- Ưu tiên sử dụng `.agent` làm nguồn quy tắc chính cho workspace này.
- Nếu một module con chưa có `.agent/AGENTS.md` hoặc `.codex/AGENTS.md`, tạo file hướng dẫn tương ứng theo chuẩn dự án trước khi mở rộng thay đổi lớn.

## 6. Thứ tự ưu tiên
- Khi có xung đột, tuân theo thứ tự: System/Developer instruction > AGENTS workspace > tài liệu nội bộ khác.

## 7. Chuẩn vận hành Codex + NotebookLM
- Mục tiêu: dùng NotebookLM để giữ “bộ nhớ dự án” bên ngoài context trực tiếp của Codex, giúp giảm token/context mà vẫn nắm đúng rule.
- Khi task cần research hoặc cần hiểu nhanh quy định dự án:
  1. Chạy preflight (xác thực, notebook, quyền truy cập nguồn).
  2. Query theo phạm vi hẹp (chỉ lấy phần liên quan trực tiếp đến task).
  3. Interrogate sau import/research (so khớp, mâu thuẫn, thiếu dữ liệu).
  4. Chỉ generate/chỉnh code sau khi vượt quality gate.
- Quy tắc curation nguồn:
  - Một notebook chỉ phục vụ một mục tiêu nghiên cứu.
  - Ưu tiên Markdown/Google Docs có heading; hạn chế PDF thô nguyên khối.
  - Nạp nguồn theo đợt nhỏ và kiểm tra chất lượng sau mỗi đợt.
  - Có glossary/source-map cho dự án dài hạn.
- Quality gate:
  - Claim quan trọng phải có dẫn chứng từ nguồn.
  - Nếu nguồn không đủ, bắt buộc ghi rõ thiếu bằng chứng.
  - Luôn ghi chú mức tự tin của kết luận trước khi chốt hướng triển khai.
