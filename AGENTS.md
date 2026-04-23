# Điều Hướng Context Cho VibeCode

Mục tiêu của file này là giảm việc Codex đọc lặp lại toàn bộ `.agent`, `README` và docs khi không cần thiết, nhưng vẫn giữ đúng nguồn sự thật cho implementation.

## Thứ tự đọc ưu tiên

1. Nếu task nhỏ và chỉ tác động đến một vài file code, đọc trực tiếp file mục tiêu rồi làm việc.
2. Nếu task cần hiểu bối cảnh rộng, đọc `ai-knowledge/module-map.md` trước để xác định phạm vi.
3. Nếu task cần rules hoặc workflow của workspace, đọc `.agent/project_settings.md` rồi `.agent/rules.md`.
4. Chỉ mở thêm workflow hoặc skill trong `.agent/` khi task thực sự liên quan.
5. Khi tài liệu đã được đưa vào NotebookLM, ưu tiên hỏi NotebookLM trước thay vì đọc lại nhiều file markdown.

## NotebookLM

- `default_notebook`: `VibeCode - Governance & Docs`
- `notebook_alias`: `vibecode-governance`
- `notebook_purpose`: docs nội bộ, workflow, architecture, vendor docs của workspace và các dự án con
- `use_nlm_by_default_for`:
  - rules
  - workflow
  - architecture
  - vendor_docs
  - project_overview
- `skip_nlm_for`:
  - bugfix_nho
  - task_1_2_files
  - implementation_verification
  - debug_cuc_bo

Khi prompt có `use nlm` mà không chỉ rõ notebook, dùng notebook mặc định ở section này.

## Nguồn sự thật

- `src`, `backend`, `frontend`, code dự án con: nguồn sự thật cho implementation hiện tại.
- `.agent/rules.md`: nguồn sự thật cho quy tắc kỹ thuật và quy trình chung của workspace.
- `ai-knowledge/*.md`: bản tóm tắt để định vị nhanh, không thay thế code.

## Nguyên tắc hành vi khi triển khai
- Nghĩ trước khi code:
  - nêu rõ giả định, điểm chưa chắc và rủi ro chính trước khi sửa
  - nếu có nhiều cách hiểu, phải làm rõ thay vì chọn ngầm
- Ưu tiên đơn giản:
  - chỉ thêm đúng lượng code, docs và rule cần thiết cho yêu cầu hiện tại
  - tránh abstraction, config hoặc ceremony chưa có nhu cầu thật
- Chỉnh sửa đúng phạm vi:
  - chỉ chạm file và đoạn liên quan trực tiếp
  - không tiện tay refactor hoặc dọn dẹp phần ngoài task
- Làm việc theo tiêu chí kiểm chứng được:
  - với task nhiều bước phải nêu rõ cách verify
  - trước khi kết luận xong việc phải có bằng chứng kiểm tra phù hợp

## Quy tắc giữ context gọn

- Không quét toàn bộ `.agent`, `docs`, `README` theo mặc định.
- Không đọc lại cùng một bộ tài liệu nếu trong phiên hiện tại đã có đủ kết luận làm việc.
- Khi cần nghiên cứu tài liệu lặp lại, ưu tiên dùng NotebookLM với manifest ở `ai-knowledge/notebooklm-source-manifest.md`.
- Khi đổi hẳn dự án con hoặc domain lớn, ưu tiên thread mới thay vì kéo dài hội thoại cũ.

