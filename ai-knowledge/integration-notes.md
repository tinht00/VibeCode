# Integration Notes

## Mục tiêu

Ghi lại các tích hợp ngoài repo hoặc giữa các dự án con để Codex biết khi nào nên tra NotebookLM, khi nào phải mở code.

## Gợi ý vận hành

- Dùng file này để ghi các dịch vụ ngoài như Etsy API, OpenAI API, NotebookLM, storage, auth hoặc webhook.
- Mỗi tích hợp nên có:
  - mục đích
  - entrypoint chính trong repo
  - biến môi trường liên quan
  - nơi chứa docs chính thức
  - rủi ro hoặc lưu ý khi debug

## Tích hợp nên bổ sung tiếp

- NotebookLM MCP
- Etsy API trong `EtsyResearchMVP`
- OpenAI API hoặc các service AI dùng trong các dự án con

## NotebookLM mặc định của workspace

- notebook canonical: `VibeCode - Governance & Docs`
- notebook alias: `vibecode-governance`
- nguồn mapping: `AGENTS.md` ở root workspace
- mục đích: chứa docs nội bộ, workflow, architecture, vendor docs dùng lặp lại
- không dùng notebook này để thay thế việc kiểm chứng implementation trong code
