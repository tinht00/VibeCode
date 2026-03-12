# ClipartPrompt

Workspace này được thiết kế theo mô hình `folder-only` để quản lý clipart theo từng chủ đề và sinh luôn gói bán hàng cho Etsy cùng Pinterest.

Bạn không cần chạy ứng dụng hay script. Quy trình làm việc chỉ gồm:

1. Tạo hoặc chọn một chủ đề trong `topics`.
2. Thêm brief vào `01_briefs` của chủ đề đó từ mẫu ở `03_templates/brief-template.md`.
3. Gọi Codex và nói rõ chủ đề hoặc brief nào cần xử lý.
4. Codex sinh mặc định 4 lớp đầu ra:
   - `02_prompts`: prompt set
   - `07_etsy`: listing pack và asset plan
   - `08_pinterest`: pin copy pack
5. Khi tạo ảnh, bạn tiếp tục lưu ảnh vào đúng thư mục ảnh của chủ đề đó để quản lý.

## Cấu trúc chính

- `topics`: mỗi thư mục con là một chủ đề riêng
- `03_templates`: mẫu file đầu vào, đầu ra và metadata chủ đề
- `marketplaces`: ghi chú policy và SEO notes cho Etsy/Pinterest
- `.agent`: bộ preset mẫu, hiện đang chứa preset Lumina

## Cấu trúc chuẩn của một chủ đề

```text
topics/
  cute-garden-animals/
    _topic.md
    01_briefs/
    02_prompts/
    03_images_raw/
    04_images_selected/
    05_images_final/
    06_notes/
    07_etsy/
    08_pinterest/
```

## Ý nghĩa từng thư mục

- `01_briefs`: ý tưởng đầu vào, yêu cầu mới, revision
- `02_prompts`: bộ prompt final theo từng brief hoặc từng đợt
- `03_images_raw`: ảnh vừa tạo từ AI, chưa lọc
- `04_images_selected`: ảnh đã duyệt để giữ lại
- `05_images_final`: ảnh đã xử lý xong để bán hoặc đóng gói
- `06_notes`: ghi chú sản xuất, keyword, listing, review
- `07_etsy`: title, description, tag sets, asset plan
- `08_pinterest`: pin title, description, board/topic keywords, content angles

## Cách dùng ngắn gọn

Ví dụ:

1. Tạo chủ đề `topics/cute-garden-animals`
2. Tạo brief `topics/cute-garden-animals/01_briefs/2026-03-11_brief.md`
3. Nhắn Codex:

```text
Hãy đọc brief của chủ đề cute-garden-animals và tạo đủ prompt, Etsy pack, asset plan, và Pinterest pack.
```

## Nguyên tắc vận hành

- Bạn chỉ cần nêu ý tưởng theo từng chủ đề.
- Codex tự chuẩn hóa brief, thêm giả định hợp lý, và sinh prompt theo đúng chủ đề bạn yêu cầu.
- Nếu bạn muốn dùng một preset như Lumina, hãy ghi rõ trong `_topic.md` hoặc trong brief.
- Output ưu tiên phục vụ digital clipart bundle cho Etsy và marketing trên Pinterest.
- Ảnh tạo sau này nên được bỏ đúng vào thư mục ảnh của chủ đề tương ứng để quản lý xuyên suốt.
