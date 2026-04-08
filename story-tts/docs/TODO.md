# TODO

Danh sách này chỉ giữ các hạng mục chưa xong, đang bị chặn hoặc còn thiếu bước verify.

## Mẫu ghi
### [Tiêu đề ngắn]
- Bối cảnh: `[mô tả ngắn]`
- Trạng thái hiện tại: `[đã làm tới đâu]`
- Việc còn thiếu: `[phần còn lại]`
- Cách verify: `[cách kiểm tra sau khi hoàn tất]`

## Hạng mục hiện tại
### Verify end-to-end realtime trong trình duyệt
- Bối cảnh: Luồng chính đã chuyển sang `frontend -> Python realtime TTS service -> WebSocket audio stream`.
- Trạng thái hiện tại: `go build`, `npm run build`, `py_compile` đều pass; smoke test service đã tạo session và nhận được binary audio qua WebSocket.
- Việc còn thiếu: Mở UI trên Chrome/Edge, import một truyện thật, bấm `Nghe chương`, xác nhận audio phát trực tiếp trong player và chapter tự chuyển khi đọc xong.
- Cách verify: Trong UI, trạng thái đổi từ `connecting/buffering` sang `reading`, audio phát không cần file trung gian, chapter kế tiếp tự mở sau khi chapter hiện tại hoàn tất.

### Làm sạch code TTS legacy sau khi ổn định
- Bối cảnh: Backend Go vẫn còn route và runtime `DirectTTSSession` từ luồng `edge-tts` cũ để tránh refactor quá gấp.
- Trạng thái hiện tại: Frontend đã không còn dùng các route này, nhưng code backend legacy vẫn còn tồn tại.
- Việc còn thiếu: Sau khi verify realtime UI ổn định, dọn bớt route/model/service cũ không còn dùng và cập nhật schema/docs tương ứng nếu cần.
- Cách verify: Tìm trong frontend không còn route cũ, backend giảm code dư mà không làm gãy import, content và progress.
