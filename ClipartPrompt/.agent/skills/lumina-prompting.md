---
name: lumina-prompting
description: Skill chuyên biệt để sinh prompt tạo hình ảnh cho dự án Project Lumina. Sử dụng khi user muốn tạo Character, Scene, hoặc Item cho dự án này. Tự động áp dụng Master Style và thông tin nhân vật chuẩn.
---

# Lumina Prompting Skill

Skill này giúp tạo ra các prompt nhất quán với art style của Project Lumina: **Watercolor & Gold Ink**.

## 1. Master Style (Luôn áp dụng)

Mọi prompt sinh ra BẮT BUỘC phải kết thúc bằng cụm style này:

```text
Watercolor illustration style with colored pencil details, distinct gold ink outlines, visible textured paper grain, soft pastel colors, whimsical storybook aesthetic, clean edges, flat design elements, isolated on white background, 2D art, high resolution
```

## 2. Character Prompt Structure

Công thức chuẩn cho nhân vật:

```text
[Subject Description] + [Action/Pose] + [Outfit/Accessories] + [Master Style] + --ar [Ratio]
```

### Prompt mẫu cho các nhân vật chính:

**Poki (Baby Form - Cấp 1):**
> Cute baby Primal Dragon named Poki, smooth milky-white porcelain skin, single small pale gold crystal horn on forehead, glowing cyan-blue runic patterns along spine, wingless, large mesmerizing galaxy-blue eyes with stars inside.

**Ignis (Cấp 1):**
> Agile Fire Dragon hatchling named Ignis, vibrant orange-red scales with charcoal black accents, small flame tip on tail, sharp amber eyes, playful warrior pose.

**Lumi (Cấp 1):**
> Elegant Frost Fox kit named Lumi, pure white fur with soft lavender tips, wearing a tiny crystal pendant, ice-blue intelligent eyes, sitting gracefully.

**Clank (Cấp 1):**
> Steampunk Owl construct named Clank, made of polished brass and oak wood, camera lens eyes zooming out, steam puffing from small vents, gears visible in chest.

## 3. Scene Prompt Structure

Công thức chuẩn cho bối cảnh:

```text
[Scene Name] + [Key Elements] + [Atmosphere/Lighting] + [Master Style] + --ar 16:9
```

**Ví dụ - Hồ Gương Vỡ:**
> The Frozen Galaxy Lake at night, jagged waves made of transparent blue crystal ice, reflecting purple stars from the sky, a dimensional rift in the clouds, magical and ethereal atmosphere.

## 4. Helper Functions (Quy tắc bổ sung)

- **Emotion:** Luôn thêm 1 từ chỉ cảm xúc (e.g., *curious, happy, determined, sleepy*) để nhân vật có hồn.
- **Background:** Mặc định là `isolated on white background` cho Clipart. Nếu làm Wallpaper/Scene thì bỏ cụm này và thay bằng mô tả background cụ thể.
- **Ratio:**
    - Clipart/Sticker: `--ar 1:1`
    - YouTube Shorts/Phone Wallpaper: `--ar 9:16`
    - PC Wallpaper/Video thumbnails: `--ar 16:9`

## 5. Workflow Tự động hóa

Khi user yêu cầu: *"Tạo bộ ảnh Poki đang ăn"*, hãy thực hiện:
1.  Xác định Subject: Poki (lấy description chuẩn).
2.  Xác định Action: Eating (thêm chi tiết: *eating a glowing star fruit*).
3.  Ghép với Master Style.
4.  Đề xuất 3-4 variations khác nhau (e.g., eating happily, messy eating, holding fruit).
