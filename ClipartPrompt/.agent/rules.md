# PROJECT LUMINA: Rules & Guidelines

Tài liệu này chứa các quy tắc cốt lõi và hướng dẫn style cho dự án **Project Lumina: The Primal Saga**.

## 1. Core Philosophy (Triết lý Cốt lõi)

- **Ecosystem Thinking**: Mọi tài sản tạo ra đều phải phục vụ 3 mục đích: Bán (Etsy) -> Kéo Traffic (YouTube) -> Game Asset (App).
- **Quality over Quantity**: Tập trung vào chất lượng "Premium Watercolor & Gold Ink". Ít nhưng chất.
- **Consistent Lore**: Tất cả nội dung phải tuân thủ cốt truyện "Kỷ Nguyên Bạc" và tính cách nhân vật đã định nghĩa.

## 2. Art Style Guidelines (Quy chuẩn Nghệ thuật)

Mọi hình ảnh sinh ra cho dự án **BẮT BUỘC** phải tuân thủ Master Style:

> **Master Style Prompt Segment:**
> `Watercolor illustration style with colored pencil details, distinct gold ink outlines, textured paper grain visible, soft pastel colors, whimsical storybook aesthetic, clean edges, flat design elements, isolated on white background, 2D art.`

- **Không dùng**: Photorealistic, 3D render quá bóng bẩy, Dark horror, Neon cyberpunk (trừ khi là Clank/Ignis nhưng vẫn phải giữ nét watercolor).
- **Màu sắc chủ đạo**: Pastel, Galaxy Blue (Poki), Red/Orange (Ignis), Ice/Purple (Lumi).

## 3. Character Consistency (Nhất quán Nhân vật)

Khi tạo hình nhân vật, phải đảm bảo các đặc điểm nhận diện:

| Nhân vật | Đặc điểm Bắt buộc |
|---|---|
| **Poki** | Da trắng sứ (không vảy), 1 sừng vàng nhỏ, hoa văn xanh phát sáng, mắt galaxy to. |
| **Ignis** | Rồng lửa, vảy đỏ cam/đen, dáng chiến binh. |
| **Lumi** | Cáo tuyết, lông trắng/bạc/tím, sang trọng, thông thái. |
| **Bramble**| Hươu, sừng cây/hoa, tông màu rêu/đất. |
| **Clank** | Cú máy, chi tiết đồng/bánh răng, hơi nước. |

## 4. Workflow Rules (Quy tắc Làm việc)

- **File Naming**: `[Character]_[Level]_[Pose]_[Date].png` (Ví dụ: `Poki_Lvl1_Sitting_20231027.png`)
- **Folder Structure**:
    - `Assets/Raw`: Ảnh gốc từ Dreamina.
    - `Assets/Processed`: Ảnh đã xóa nền & Upscale.
    - `Assets/Final`: Ảnh đã đóng gói (thêm watermark/metadata) để bán.
- **Platform Specifics**:
    - **Etsy**: Ảnh PNG nền trong suốt, 300 DPI.
    - **YouTube**: Tỉ lệ 9:16 (Shorts), dùng Style Frame kể chuyện.
    - **Game**: Sprite sheet hoặc tách lớp (Layered).

## 5. Technical Constraints

- **Upscale**: Luôn upscale lên ít nhất 4K cho sản phẩm thương mại.
- **Background Removal**: Kiểm tra kỹ viền (edge) sau khi xóa nền, đảm bảo không bị jagged (răng cưa) hoặc mất chi tiết gold ink.
