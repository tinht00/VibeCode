---
name: clipart-prompt
description: Hướng dẫn tạo prompt chuyên nghiệp để sinh hình clipart bằng AI (generate_image tool). Sử dụng skill này khi cần tạo clipart, icon, illustration, sticker, hoặc hình minh họa phong cách vector/flat/cartoon cho website, app, presentation, tài liệu. Trigger khi user yêu cầu tạo hình ảnh dạng clipart, icon set, illustration, hoặc bất kỳ hình minh họa nào có phong cách đồ họa (không phải ảnh chụp thực tế).
---

# Clipart Prompt Skill

Skill này cung cấp framework để sinh prompt tạo clipart chất lượng cao bằng tool `generate_image`. Bao gồm các prompt formula, phong cách clipart, và best practices.

## Prompt Formula (Công thức Prompt)

Mọi clipart prompt đều tuân theo công thức 6 thành phần:

```
[Phong cách] + [Chủ thể] + [Hành động/Trạng thái] + [Màu sắc] + [Nền] + [Chất lượng]
```

### Giải thích từng thành phần

| Thành phần | Mô tả | Ví dụ |
|---|---|---|
| **Phong cách** | Loại clipart (flat, vector, cartoon...) | `flat design vector illustration` |
| **Chủ thể** | Đối tượng chính cần vẽ | `a friendly robot mascot` |
| **Hành động/Trạng thái** | Chủ thể đang làm gì | `waving hello, smiling` |
| **Màu sắc** | Bảng màu mong muốn | `pastel color palette, soft blue and pink` |
| **Nền** | Kiểu nền (trong suốt, đơn sắc...) | `on a white background, isolated` |
| **Chất lượng** | Từ khóa nâng chất lượng | `clean lines, high detail, professional` |

## Phong cách Clipart (Styles)

### 1. Flat Design (Thiết kế phẳng)
- **Đặc điểm**: Không bóng, không gradient phức tạp, hình học đơn giản
- **Prompt keywords**: `flat design, minimal, geometric shapes, solid colors, no shadows, clean`
- **Phù hợp**: Website, app UI, infographic, presentation

```
Ví dụ: "Flat design vector illustration of a laptop with code on screen,
minimal geometric style, solid blue and purple colors, no shadows,
white background, clean lines, professional clipart"
```

### 2. Cartoon / Cute Style (Phong cách hoạt hình)
- **Đặc điểm**: Dễ thương, bo tròn, biểu cảm vui vẻ
- **Prompt keywords**: `cute cartoon style, kawaii, rounded shapes, cheerful, adorable, chibi`
- **Phù hợp**: Sticker, children's content, social media, mascot

```
Ví dụ: "Cute cartoon style clipart of a happy cat holding a coffee cup,
kawaii, rounded shapes, pastel colors, cheerful expression,
white background, adorable illustration"
```

### 3. Line Art / Outline (Nét vẽ)
- **Đặc điểm**: Chỉ có đường nét, tối giản, elegant
- **Prompt keywords**: `line art, outline only, single color stroke, minimalist, thin lines, hand-drawn`
- **Phù hợp**: Logo, icon, tài liệu, coloring pages

```
Ví dụ: "Line art clipart of a mountain landscape with sun,
single color black outline, minimalist, thin clean lines,
white background, simple elegant illustration"
```

### 4. Isometric / 3D Style (Phong cách đẳng cự)
- **Đặc điểm**: Góc nhìn isometric, chiều sâu, hiện đại
- **Prompt keywords**: `isometric view, 3D style, isometric perspective, modern, tech style`
- **Phù hợp**: Tech illustration, infographic, landing page

```
Ví dụ: "Isometric view illustration of a modern office workspace
with desk, computer and plant, 3D style, vibrant gradient colors,
soft shadows, white background, tech clipart"
```

### 5. Icon Style (Biểu tượng)
- **Đặc điểm**: Nhỏ gọn, dễ nhận diện, đồng nhất
- **Prompt keywords**: `icon style, simple icon, glyph, filled icon, symbol, uniform stroke`
- **Phù hợp**: App icon, UI icon set, navigation

```
Ví dụ: "Simple flat icon of a shopping cart, filled style,
rounded corners, single color blue, 64x64 pixel style,
white background, UI icon clipart"
```

### 6. Watercolor / Hand-painted (Màu nước)
- **Đặc điểm**: Mềm mại, nghệ thuật, tự nhiên
- **Prompt keywords**: `watercolor style, hand-painted, soft edges, artistic, brush strokes, delicate`
- **Phù hợp**: Thiệp mời, đồ họa nghệ thuật, trang trí

```
Ví dụ: "Watercolor style clipart of a bouquet of wildflowers,
hand-painted look, soft pastel colors, delicate brush strokes,
white background, artistic botanical illustration"
```

### 7. Retro / Vintage (Cổ điển)
- **Đặc điểm**: Phong cách thập niên cũ, hoài cổ, texture
- **Prompt keywords**: `retro style, vintage, 1950s, halftone dots, muted colors, nostalgic, aged`
- **Phù hợp**: Poster, branding retro, merchandise

```
Ví dụ: "Retro vintage clipart of a rocket ship,
1960s space age style, muted orange and teal colors,
halftone texture, cream background, nostalgic illustration"
```

## Bảng màu theo chủ đề (Color Palettes)

| Chủ đề | Từ khóa màu sắc |
|---|---|
| **Business** | `navy blue, slate gray, white, gold accents` |
| **Nature** | `forest green, earth brown, sky blue, warm yellow` |
| **Tech** | `electric blue, dark purple, neon cyan, black` |
| **Kids** | `bright red, sunny yellow, sky blue, lime green` |
| **Pastel** | `soft pink, baby blue, lavender, mint green, peach` |
| **Dark Mode** | `deep charcoal, muted teal, dim purple, off-white` |
| **Healthcare** | `clean white, light blue, soft green, gentle teal` |
| **Food** | `warm orange, tomato red, fresh green, golden yellow` |

## Từ khóa nâng cao chất lượng (Quality Boosters)

Thêm vào cuối prompt để tăng chất lượng output:

- **Độ sắc nét**: `sharp edges, crisp lines, high resolution, pixel perfect`
- **Chuyên nghiệp**: `professional quality, commercial use, premium clipart, polished`
- **Tính nhất quán**: `consistent style, uniform line weight, cohesive design`
- **Nền sạch**: `isolated on white background, no background, transparent style, clean cutout`

## Workflow tạo Clipart

1. **Xác định mục đích**: Clipart dùng ở đâu? (web, app, print, social media)
2. **Chọn phong cách**: Tham khảo mục "Phong cách Clipart" ở trên
3. **Xây dựng prompt**: Áp dụng công thức 6 thành phần
4. **Thêm Quality Boosters**: Chọn từ khóa phù hợp
5. **Gọi `generate_image`**: Dùng prompt đã xây dựng
6. **Đánh giá & lặp lại**: Tinh chỉnh prompt nếu cần

## Lưu ý quan trọng (Caveats)

- **Luôn chỉ định nền**: Thêm `white background` hoặc `transparent background` để clipart dễ sử dụng
- **Tránh prompt quá dài**: Giữ prompt dưới 75 từ, tập trung vào yếu tố chính
- **Tránh mô tả mơ hồ**: `a nice picture` → thay bằng `flat design vector illustration of a smiling sun`
- **Tính nhất quán trong bộ**: Khi tạo nhiều clipart cùng bộ, giữ nguyên phong cách và bảng màu trong prompt
- **Negative concepts**: Tránh dùng từ phủ định (no, don't, without), thay bằng mô tả tích cực
  - ❌ `no text on the image`
  - ✅ `clean illustration without any text or lettering`

## Prompt Templates nâng cao

Xem chi tiết các template prompt cho từng use case tại [prompt_templates.md](references/prompt_templates.md).
