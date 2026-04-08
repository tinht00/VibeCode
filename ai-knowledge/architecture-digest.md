# Architecture Digest

## Mục tiêu

Tóm tắt kiến trúc của workspace `VibeCode` để Codex và NotebookLM định vị nhanh dự án con, luồng dữ liệu và ranh giới hệ thống trước khi đọc code chi tiết.

## Cấu trúc tổng quan

- Workspace này là monorepo nhẹ theo kiểu nhiều dự án con cùng tồn tại ở top level.
- Mỗi dự án con có thể dùng tech stack khác nhau và có vòng đời độc lập.
- `.agent/` chứa rules, workflows và skills dùng chung cho toàn workspace.

## Dự án con hiện có

- `BackgroundRemover`: ứng dụng tách nền, có backend Python và frontend web.
- `clipart_ops`: công cụ Python cho pipeline clipart.
- `ClipartPrompt`: nội dung và dữ liệu cho prompt/listing clipart.
- `EtsyResearchMVP`: hệ thống nghiên cứu và đồng bộ dữ liệu Etsy với backend/frontend riêng.
- `FlowBatchExtension`: extension phục vụ batch flow.
- `Secrets`: thư mục nhạy cảm, không dùng làm nguồn NotebookLM.

## Nguyên tắc điều hướng

- Bắt đầu bằng `module-map.md` để xác định entrypoint và khu vực cần đọc.
- Chỉ mở docs hoặc workflow của dự án con đang làm.
- Không quét toàn bộ workspace nếu task chỉ thuộc một dự án con.

## Cần cập nhật thêm

- Mô tả luồng dữ liệu giữa các dự án con nếu có tích hợp thật sự.
- Ghi rõ dự án nào đang active, dự án nào chỉ là thư viện hoặc tài nguyên nội dung.
