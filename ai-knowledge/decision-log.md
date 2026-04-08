# Decision Log

## Mục tiêu

Lưu lại các quyết định kiến trúc hoặc vận hành có tính lâu dài để giảm phụ thuộc vào lịch sử chat.

## Quy ước ghi chép

- Mỗi quyết định nên có ngày, phạm vi ảnh hưởng, lý do và tradeoff.
- Chỉ ghi những quyết định có khả năng ảnh hưởng đến cách tổ chức code, workflow hoặc context strategy.

## Quyết định hiện có

### 2026-03-16: Áp dụng lớp `ai-knowledge/` cho workspace

- Lý do: giảm việc Codex đọc lặp lại `.agent`, `README` và docs khi làm việc trên nhiều dự án con.
- Tác động:
  - thêm root `AGENTS.md` để định tuyến context
  - thêm `module-map.md` và `notebooklm-source-manifest.md`
  - dùng NotebookLM cho tri thức ổn định, repo cho implementation truth

### 2026-03-16: Giữ `.agent/` làm nguồn rule chính

- Lý do: workspace đã có rules và workflows rõ ràng trong `.agent/`.
- Tác động: root `AGENTS.md` chỉ đóng vai trò điều hướng, không thay thế rules hiện có.

### 2026-03-16: Dùng notebook mặc định theo project

- Lý do: giảm việc phải nêu tên notebook đầy đủ ở mọi prompt và tạo một canonical mapping cho workspace.
- Tác động:
  - notebook mặc định của workspace là `VibeCode - Governance & Docs`
  - alias CLI của notebook là `vibecode-governance`
  - mapping notebook được lưu trong `AGENTS.md` cục bộ
  - prompt `use nlm` sẽ ngầm dùng notebook mặc định nếu không override tên notebook
