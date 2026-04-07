# Hướng dẫn thiết lập Etsy OAuth

## Mục tiêu

Kết nối shop Etsy theo cơ chế OAuth chính thức, chỉ dùng scope đọc dữ liệu ở bản MVP.

## Các bước

1. Tạo ứng dụng trong Etsy Developer Portal.
2. Khai báo `redirect_uri` chính xác:
   - `http://localhost:8000/api/auth/etsy/callback`
3. Sao chép `API key` và `client id`.
4. Điền vào file môi trường:
   - `ETSY_API_KEY`
   - `ETSY_CLIENT_ID`
   - `ETSY_REDIRECT_URI`
   - `ETSY_SCOPES`

## Scope tối thiểu khuyến nghị

- `shops_r`
- `listings_r`
- `transactions_r` chỉ khi bạn thực sự cần dữ liệu giao dịch phục vụ phân tích

## Checklist compliance

- Chỉ xin scope đọc ở MVP.
- Không dùng scraping làm lõi sản phẩm.
- Không tự động sửa listing từ app ở giai đoạn đầu.
- Lưu token có mã hóa.
- Chuẩn bị nút ngắt kết nối ở phase sau.
