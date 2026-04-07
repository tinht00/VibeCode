# Luồng OAuth, sync và audit

## Luồng chuẩn

1. Người dùng bấm `Kết nối Etsy`.
2. Backend sinh URL OAuth với `state + PKCE`.
3. Etsy callback về backend.
4. Backend đổi `code` lấy token.
5. Backend lấy danh sách shop thuộc tài khoản.
6. Backend sync thông tin shop và listings.
7. Frontend mở dashboard listing.
8. Người dùng chạy audit theo listing cụ thể.
9. Người dùng nhập `seed keyword` để benchmark.

## Ghi chú

- Audit không ghi ngược thay đổi lên Etsy.
- Benchmark chỉ hỗ trợ đối chiếu mặt bằng, chưa phải competitor module hoàn chỉnh.
- Mọi thông báo lỗi nên hiển thị bằng tiếng Việt rõ ràng.
