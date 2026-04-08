# FlowBatch Extension

## Nhịp chạy prompt tự động
- Mặc định mỗi prompt nghỉ `25 giây`.
- Mốc nghỉ theo cụm `5 prompt` vẫn giữ cấu hình `20 giây`, nhưng runtime áp dụng `Math.max(delayMs, longPauseMs)` nên nhịp thực tế vẫn `25 giây/prompt`.
- Logic áp dụng trong luồng `FLOW_AUTOFILL_PROMPTS`.

## Ghi chú debug nhanh
### Case 1: Thấy extension vẫn chạy nhịp cũ (10 giây)
- Dấu hiệu nhận biết: popup hiển thị nhịp cũ hoặc log chạy nhanh hơn 25 giây mỗi vòng.
- Nguyên nhân: Chrome chưa nạp bản extension mới sau khi sửa mã.
- Cách khắc phục:
  1. Vào `chrome://extensions`.
  2. Bật `Developer mode`.
  3. Nhấn `Reload` cho extension `FlowBatchExtension`.
  4. Mở lại popup và chạy thử một batch ngắn.
- Cách phòng ngừa tái diễn: luôn reload extension sau mỗi lần thay đổi `content.js` hoặc `popup.js`.

### Case 2: Prompt không chạy tiếp sau một vòng
- Dấu hiệu nhận biết: chỉ chạy 1 prompt rồi dừng, không chuyển prompt tiếp theo.
- Nguyên nhân khả dĩ:
  1. Trang Flow không còn thấy ô nhập prompt hoặc nút Generate.
  2. Batch bị dừng thủ công (`stopRequested`).
- Cách khắc phục:
  1. Refresh tab Flow.
  2. Mở popup và chạy lại batch.
  3. Kiểm tra thông báo lỗi trong popup để xác định selector bị thiếu.
- Cách phòng ngừa tái diễn: giữ tab Flow ổn định, hạn chế đổi layout hoặc đóng/mở panel giữa lúc batch đang chạy.
