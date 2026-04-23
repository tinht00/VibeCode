# FlowBatch Extension

## Nhịp chạy prompt tự động
- Mặc định mỗi prompt nghỉ `15 giây`.
- Cứ mỗi `5 prompt` sẽ nghỉ dài `25 giây`.
- Runtime áp dụng `Math.max(delayMs, longPauseMs)` để bảo đảm mốc nghỉ dài không bao giờ ngắn hơn nhịp mặc định.
- Logic áp dụng trong luồng `FLOW_AUTOFILL_PROMPTS`.

## Composer resolver mới
- Extension không còn phụ thuộc vào quyền `debugger` của Chrome để gõ prompt hoặc click cưỡng bức.
- Luồng mới ưu tiên nhớ đúng composer mà người dùng vừa focus/tương tác, sau đó chọn prompt và nút submit trong cùng composer đó.
- Resolver thuần nằm ở `composerResolver.js` để có thể test độc lập trước khi nối vào `content.js`.
- Strategy ghi prompt nằm ở `editorStrategy.js`; editor kiểu rich text sẽ ưu tiên `insertText` thay vì gán `textContent` trực tiếp.

## Giao diện và tải ảnh
- Side panel chia thành 3 vùng: Prompt Queue, Download và Gallery.
- Gallery có thao tác nhanh: chọn tất cả ảnh đang hiển thị, bỏ chọn, xóa gallery và mở thư mục tải.
- Khi tải ảnh, popup mặc định dùng URL trực tiếp như luồng ban đầu nhưng đặt đuôi `.jpg` thay vì `.jfif`.
- Có thể chọn định dạng tải trực tiếp `JPG`, `PNG` hoặc `WebP`; `PNG/WebP` sẽ convert ảnh trong popup trước khi tải.
- Vẫn có thể chuyển sang cách tải bằng menu Flow và chọn chất lượng `1K Original` hoặc `2K Upscaled`.
- `downloadStrategy.js` giữ các helper nhỏ cho chuẩn hóa cách tải, định dạng và chất lượng.
- Luồng crop tự động đã được loại bỏ khỏi message handler và giao diện chính.

## Kiểm tra nhanh
- Chạy test resolver: `node --test tests/composerResolver.test.js`
- Chạy test download strategy: `node --test tests/downloadStrategy.test.js`
- Sau khi sửa mã extension, vẫn cần reload lại extension trong `chrome://extensions` và refresh lại tab Flow đang mở.

## Ghi chú debug nhanh
### Case 1: Thấy extension vẫn chạy nhịp cũ
- Dấu hiệu nhận biết: popup hiển thị nhịp cũ hoặc log chạy không đúng pattern `15 giây/prompt`, `25 giây` sau mỗi cụm `5 prompt`.
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
