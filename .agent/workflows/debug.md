---
description: Quy trình debug chuẩn - Thu thập context, phân tích lỗi, và sửa chữa có hệ thống.
---

# /debug - Quy trình Debug Chuẩn

## Quy trình

### Bước 1: Thu thập thông tin lỗi
1. Đọc **error log** hoặc thông báo lỗi chính xác.
2. Xác định **file và dòng code** gây lỗi.
3. Kiểm tra **stack trace** (nếu có).

### Bước 2: Đọc Rules & Context
// turbo
1. Đọc `.agent/rules.md` để đảm bảo tuân thủ quy chuẩn khi sửa.
2. Đọc skill phù hợp với tech stack đang debug.

### Bước 3: Phân tích nguyên nhân gốc (Root Cause Analysis)
1. **Reproduce**: Tái hiện lỗi.
2. **Isolate**: Thu hẹp phạm vi - file nào, function nào, dòng nào?
3. **Trace**: Theo dõi luồng dữ liệu từ input đến chỗ lỗi.

### Bước 4: Tra cứu Context7 (nếu cần)
Nếu lỗi liên quan đến thư viện/framework, tra cứu Context7 để kiểm tra:
- API có thay đổi không?
- Best practice xử lý lỗi tương tự?

### Bước 5: Sửa lỗi & Kiểm tra
1. Sửa lỗi theo nguyên tắc **Atomic** - chỉ sửa đúng chỗ cần sửa.
2. Kiểm tra không gây **regression** (lỗi liên quan).
3. Cập nhật comment/docs nếu cần.

## Cấu trúc báo cáo debug

```
🔴 Lỗi: [Mô tả lỗi]
📍 Vị trí: [File:Line]
🔍 Nguyên nhân: [Root cause]
✅ Giải pháp: [Cách sửa]
⚠️ Lưu ý: [Side effects nếu có]
```