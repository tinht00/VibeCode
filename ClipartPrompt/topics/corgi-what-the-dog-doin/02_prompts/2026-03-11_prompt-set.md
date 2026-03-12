# Bộ prompt theo chủ đề

## Thông tin đầu vào

- Chủ đề: `corgi-what-the-dog-doin`
- File brief: `topics/corgi-what-the-dog-doin/01_briefs/2026-03-11_brief.md`
- Ngày xử lý: 2026-03-11

## Tóm tắt brief

- Chủ đề: Corgi anime chibi kawaii với reaction meme và bubble graffiti "What the dog doin?"
- Nhân vật: một chú Corgi cam-trắng thống nhất nhận diện
- Mục tiêu: bộ clipart Etsy dùng cho sticker, planner, printable bundle và reaction-style digital art
- Định dạng: 20 prompt, canvas 19:6, toàn bộ chi tiết chính nằm trong safe square 1:1 ở giữa, nền trắng
- Preset hoặc universe: none

## Giả định triển khai

- Batch này ưu tiên meme đậm nhưng vẫn ở ngưỡng commercial-safe, tránh biểu cảm xấu hoặc khó bán đại trà.
- Chữ graffiti luôn là accent nhỏ phụ trợ, không bao giờ lớn hơn khuôn mặt Corgi.
- Khoảng trống ngoài safe square chỉ dùng làm vùng đệm của canvas 19:6, không chứa thông tin thiết yếu.
- Nếu engine có xu hướng kéo dài thân chó theo canvas ngang, cần nhấn mạnh chibi compact body và centered safe-square composition ở mọi prompt.

## Creative direction

- Tạo cảm giác một gói reaction sticker của Corgi vừa đáng yêu vừa hơi mất kiểm soát theo kiểu meme sạch.
- Giữ nhận diện ổn định bằng màu cam-trắng, tai dựng to, chân ngắn, thân compact, mắt lớn và má hồng nhẹ.
- Mỗi biến thể chỉ đổi một trục cảm xúc và một trục hành động để batch đa dạng nhưng vẫn đồng bộ.
- Chữ bubble graffiti phải tròn, vui, hơi ngổ ngáo, đặt trong vùng crop vuông và đọc rõ sau khi crop 1:1.

## Framework prompt áp dụng

- Thứ tự module: Core subject -> Identity anchors -> Primary emotion -> Primary action/pose -> Outfit -> Accessories/props -> Composition and background constraints -> Style block -> Negative prompt
- Nguyên tắc tiết giảm: mỗi prompt chỉ giữ 1 cảm xúc chính, 1 hành động chính, tối đa 1 đạo cụ chính, không thêm background kể chuyện dài
- Nguyên tắc đa dạng: giữ cố định identity anchors, chỉ xoay vòng emotion, action, props và text placement trong biên an toàn
- Text treatment: luôn dùng đúng câu `What the dog doin?`, bubble graffiti nhỏ, bo tròn, nằm phía trên đầu hoặc cạnh vai nhưng vẫn trong safe square

## Style áp dụng

```text
Cute anime chibi kawaii corgi clipart, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, soft warm orange and cream palette, tiny blush cheeks, expressive oversized eyes, isolated on white background, high readability at small size, ultra-wide 19:6 canvas with all essential content centered inside a perfect 1:1 safe square crop zone
```

## Safe-square crop rules

- Dùng canvas siêu ngang `19:6` cho ảnh gốc.
- Toàn bộ đầu, tai, chân, thân, đạo cụ chính và câu chữ phải nằm trọn trong một `safe square 1:1` đặt chính giữa khung hình.
- Không để tai, chân, chữ hoặc motion lines quan trọng chạm mép safe square.
- Chữ `What the dog doin?` phải đọc được sau khi crop chính giữa sang `1:1`.
- Vùng ngoài safe square chỉ được là khoảng trắng hoặc splash trang trí rất nhẹ, không chứa ý chính.

## Variation matrix

| Biến thể | Identity anchors | Biểu cảm / cảm xúc | Hành động / pose | Trang phục | Phụ kiện / đạo cụ |
|---|---|---|---|---|---|
| 1 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | confused side-eye | ngồi khựng | không | không |
| 2 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | shocked | ngẩng đầu nhìn snack | không | snack |
| 3 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | deadpan | loaf | khăn choàng nhỏ | không |
| 4 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | feral excited | trượt zoomies | không | motion lines |
| 5 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | suspicious | nghiêng đầu | kính lệch | không |
| 6 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | blank stare | đứng đơ | không | bát ăn |
| 7 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | tiny panic | giơ chân trước | khăn choàng nhỏ | không |
| 8 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | smug | quay nửa người | không | kính lệch |
| 9 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | chaotic laugh | nhảy bật | không | snack |
| 10 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | guilty | ngậm dép | không | dép |
| 11 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | sleepy confusion | nằm bệt | khăn choàng nhỏ | không |
| 12 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | dramatic scream | lùi nhẹ | không | motion lines |
| 13 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | proud | đứng dạng chân | không | huy hiệu ngôi sao |
| 14 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | derpy | lè lưỡi | không | bong bóng nhỏ |
| 15 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | sneaky | tiptoe | khăn choàng nhỏ | snack |
| 16 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | overworked | úp mặt xuống bàn mini | kính lệch | con dấu |
| 17 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | overconfident | chống nạnh | không | vương miện giấy |
| 18 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | dizzy | ngồi xoay tròn | không | sao quay quanh đầu |
| 19 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | clingy | ôm gối mini | khăn choàng nhỏ | gối mini |
| 20 | Corgi cam-trắng chibi, tai lớn dựng, mắt to, má hồng | goblin joy | kéo hộp carton | không | hộp carton |

## Danh sách prompt

```json
[
  {
    "id": 1,
    "theme": "Side-Eye Freeze",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, confused side-eye expression, abruptly sitting as if frozen mid-thought, compact body proportions, small bubble graffiti text saying \"What the dog doin?\" tucked above the head on the upper left, text smaller than the face, ultra-wide 19:6 canvas, keep the entire corgi and all text fully centered inside a perfect 1:1 safe square crop zone, leave the outer sides mostly empty white space, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-left inside the centered safe square, secondary to the character."
  },
  {
    "id": 2,
    "theme": "Snack Shock",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, shocked open-mouth expression, looking upward dramatically at a tiny floating snack piece, neck lifted and paws planted, small bubble graffiti text saying \"What the dog doin?\" arched above the head, text smaller than the face, ultra-wide 19:6 canvas, keep the corgi, snack, and text fully centered inside a perfect 1:1 safe square crop zone, keep both horizontal sides mostly empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti centered above the character inside the safe square, readable after a 1:1 center crop."
  },
  {
    "id": 3,
    "theme": "Deadpan Loaf",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs tucked under the body, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, deadpan unimpressed stare, loaf pose with a tiny loose scarf around the neck, calm compact silhouette, small bubble graffiti text saying \"What the dog doin?\" placed on the upper right inside the composition, text smaller than the face, ultra-wide 19:6 canvas, keep the entire corgi and all text fully centered inside a perfect 1:1 safe square crop zone, leave the side wings mostly blank, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-right inside the centered safe square, secondary to the character."
  },
  {
    "id": 4,
    "theme": "Zoomies Slide",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, feral excited grin, sliding sideways in a chaotic zoomies pose with a few simple motion lines, compact energetic silhouette, small bubble graffiti text saying \"What the dog doin?\" near the upper left of the body, text smaller than the face, ultra-wide 19:6 canvas, keep the full corgi, motion lines, and text fully centered inside a perfect 1:1 safe square crop zone, keep the far left and right mostly empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-left inside the centered safe square, secondary to the character."
  },
  {
    "id": 5,
    "theme": "Suspicious Tilt",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, suspicious squint expression, head tilted to one side, one tiny crooked pair of glasses slipping slightly, compact chibi posture, small bubble graffiti text saying \"What the dog doin?\" hovering above the tilted ears, text smaller than the face, ultra-wide 19:6 canvas, keep the full corgi, glasses, and text entirely inside a centered perfect 1:1 safe square crop zone, side areas mostly empty white space, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti centered above the character inside the safe square, readable after a 1:1 center crop."
  },
  {
    "id": 6,
    "theme": "Brain-Empty Bowl",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, blank brain-empty stare, standing completely still with tiny paws near a small food bowl, rigid simple pose, small bubble graffiti text saying \"What the dog doin?\" placed on the upper right, text smaller than the face, ultra-wide 19:6 canvas, keep the corgi, bowl, and text fully inside a centered perfect 1:1 safe square crop zone, leave outer canvas edges empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-right inside the centered safe square, secondary to the character."
  },
  {
    "id": 7,
    "theme": "Tiny Panic Paw",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, tiny panic expression, lifting one front paw in a startled freeze, small soft scarf around the neck, compact rounded silhouette, small bubble graffiti text saying \"What the dog doin?\" tucked above the raised paw side, text smaller than the face, ultra-wide 19:6 canvas, keep the entire corgi and all text centered inside a perfect 1:1 safe square crop zone, keep side margins mostly empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-left inside the centered safe square, secondary to the character."
  },
  {
    "id": 8,
    "theme": "Smug Half-Turn",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, smug little menace grin, sitting while turning half the body back toward the viewer, a tiny crooked pair of glasses adding a mischievous touch, rounded compact silhouette, small bubble graffiti text saying \"What the dog doin?\" near the upper right shoulder area, text smaller than the face, ultra-wide 19:6 canvas, keep the corgi, glasses, and text fully centered inside a perfect 1:1 safe square crop zone, leave the horizontal sides mostly empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-right inside the centered safe square, secondary to the character."
  },
  {
    "id": 9,
    "theme": "Chaotic Jump",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, chaotic laughing face, bouncing upward in a tiny jump with a small snack piece nearby, compact airborne pose, small bubble graffiti text saying \"What the dog doin?\" above the jump arc, text smaller than the face, ultra-wide 19:6 canvas, keep the entire corgi, snack, and text fully centered inside a perfect 1:1 safe square crop zone, leave the far side panels mostly blank, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti centered above the character inside the safe square, readable after a 1:1 center crop."
  },
  {
    "id": 10,
    "theme": "Guilty Slipper",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, caught-in-the-act guilty expression, holding a tiny house slipper in the mouth, frozen compact stance, small bubble graffiti text saying \"What the dog doin?\" tucked above the ears on the upper left, text smaller than the face, ultra-wide 19:6 canvas, keep the full corgi, slipper, and text entirely centered inside a perfect 1:1 safe square crop zone, keep the outer horizontal space empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-left inside the centered safe square, secondary to the character."
  },
  {
    "id": 11,
    "theme": "Sleepy Sprawl",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, sleepy confused expression with heavy eyelids, flopped down in a relaxed sprawl pose, tiny soft scarf around the neck, compact rounded silhouette, small bubble graffiti text saying \"What the dog doin?\" on the upper right of the composition, text smaller than the face, ultra-wide 19:6 canvas, keep the whole corgi and all text fully centered inside a perfect 1:1 safe square crop zone, leave side areas mostly blank, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-right inside the centered safe square, secondary to the character."
  },
  {
    "id": 12,
    "theme": "Dramatic Backstep",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, dramatic scream face in a funny non-scary way, leaning back slightly with the back legs braced and a tiny backward step, a few simple motion lines around the body, compact exaggerated silhouette, small bubble graffiti text saying \"What the dog doin?\" above the head, text smaller than the face, ultra-wide 19:6 canvas, keep the full corgi, motion lines, and text entirely centered inside a perfect 1:1 safe square crop zone, keep the side panels mostly empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti centered above the character inside the safe square, readable after a 1:1 center crop."
  },
  {
    "id": 13,
    "theme": "Tiny Boss Stance",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, proud bossy expression, standing wide with chest puffed out and a tiny paper star badge near the body, compact strong silhouette, small bubble graffiti text saying \"What the dog doin?\" hovering above the ears, text smaller than the face, ultra-wide 19:6 canvas, keep the whole corgi, badge, and text fully centered inside a perfect 1:1 safe square crop zone, leave the side space mostly blank, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti centered above the character inside the safe square, readable after a 1:1 center crop."
  },
  {
    "id": 14,
    "theme": "Derpy Tongue Out",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, derpy silly face with tongue sticking out, slightly cross-eyed playful pose, a tiny speech bubble accent near one cheek, compact rounded silhouette, small bubble graffiti text saying \"What the dog doin?\" on the upper left, text smaller than the face, ultra-wide 19:6 canvas, keep the entire corgi and all text fully centered inside a perfect 1:1 safe square crop zone, outer sides mostly empty white space, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-left inside the centered safe square, secondary to the character."
  },
  {
    "id": 15,
    "theme": "Snack Sneak Tiptoe",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, sneaky mischievous expression, tiptoeing carefully with a tiny snack held close and a small scarf fluttering slightly, compact stealthy silhouette, small bubble graffiti text saying \"What the dog doin?\" on the upper right, text smaller than the face, ultra-wide 19:6 canvas, keep the full corgi, snack, and text centered inside a perfect 1:1 safe square crop zone, keep outer sides mostly empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-right inside the centered safe square, secondary to the character."
  },
  {
    "id": 16,
    "theme": "Office Meltdown",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, overworked exhausted expression, face planted onto a tiny desk with a crooked pair of glasses and a mini stamp prop, compact frustrated silhouette, small bubble graffiti text saying \"What the dog doin?\" angled above the desk area, text smaller than the face, ultra-wide 19:6 canvas, keep the corgi, desk, and text fully centered inside a perfect 1:1 safe square crop zone, keep both sides mostly blank, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti angled above the prop cluster but fully contained inside the centered safe square."
  },
  {
    "id": 17,
    "theme": "Paper Crown King",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, overconfident smug royal expression, standing with tiny paws on the hips while wearing a small paper crown, compact confident silhouette, small bubble graffiti text saying \"What the dog doin?\" arched above the crown, text smaller than the face, ultra-wide 19:6 canvas, keep the entire corgi, crown, and text fully centered inside a perfect 1:1 safe square crop zone, side panels mostly empty white space, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti arched above the crown inside the safe square, readable after a 1:1 center crop."
  },
  {
    "id": 18,
    "theme": "Dizzy Spinout",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, dizzy expression with spiraling pupils, seated in a spinout pose with tiny stars circling the head, compact whirling silhouette, small bubble graffiti text saying \"What the dog doin?\" floating above the spinning stars, text smaller than the face, ultra-wide 19:6 canvas, keep the corgi, stars, and text fully centered inside a perfect 1:1 safe square crop zone, leave outer sides mostly empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti centered above the spinning head accents inside the safe square."
  },
  {
    "id": 19,
    "theme": "Clingy Pillow Hug",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, clingy sleepy-soft expression, hugging a tiny pillow close to the chest while wearing a soft scarf, compact cozy silhouette, small bubble graffiti text saying \"What the dog doin?\" placed on the upper right of the composition, text smaller than the face, ultra-wide 19:6 canvas, keep the full corgi, pillow, and text fully centered inside a perfect 1:1 safe square crop zone, side areas mostly blank, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-right inside the centered safe square, secondary to the character."
  },
  {
    "id": 20,
    "theme": "Cardboard Goblin Drag",
    "prompt": "Cute anime chibi kawaii corgi clipart, orange-and-cream corgi with a big head, short legs, fluffy butt, oversized upright ears, tiny blush cheeks, large expressive eyes, goblin-like joyful chaos expression, dragging a tiny cardboard box with exaggerated determination, compact scrappy silhouette, small bubble graffiti text saying \"What the dog doin?\" on the upper left near the ear line, text smaller than the face, ultra-wide 19:6 canvas, keep the corgi, box, and text fully centered inside a perfect 1:1 safe square crop zone, leave the horizontal sides mostly empty, clean commercial sticker aesthetic, bright flat lighting, crisp silhouette, smooth cel-shaded illustration, isolated on white background, high resolution",
    "typography_layout": "Small bubble graffiti tucked into the upper-left inside the centered safe square, secondary to the character."
  }
]
```

## Prompt QA

- Prompt đã rõ chủ thể chính: Có, toàn bộ prompt đều khóa một chú Corgi chibi cam-trắng với identity anchors cố định.
- Prompt không dư thừa chi tiết: Có, mỗi prompt chỉ giữ một hành động chính và tối đa một đạo cụ nhỏ.
- Action và pose không chồng chéo: Có, variation matrix tách riêng từng combo cảm xúc và hành động.
- Outfit và props không quá tải: Có, chỉ dùng khăn choàng, kính lệch, snack, bát ăn, dép, hộp carton, desk mini hoặc motion lines khi thật sự cần.
- Các biến thể đủ khác nhau: Có, 20 biến thể không lặp tổ hợp `emotion + action + prop`.
- Silhouette vẫn rõ cho clipart: Có, mọi prompt đều nhấn mạnh compact silhouette, nền trắng và safe square crop.
- Chữ không lấn át nhân vật: Có, mọi prompt đều khóa bubble graffiti nhỏ hơn khuôn mặt Corgi.
- Crop giữa vẫn giữ đủ ý: Có, mọi prompt đều yêu cầu toàn bộ nhân vật và text nằm trong safe square 1:1 ở giữa.

## Ghi chú đóng gói

- Batch này hiện chỉ tạo prompt, chưa cập nhật Etsy hoặc Pinterest pack theo số lượng 20 biến thể.
- Khi hậu kỳ, nên xuất PNG nền trong suốt từ vùng crop 1:1 để tối ưu cho sticker và planner.
- Nếu cần mở rộng batch sau, chỉ nên thêm biến thể mới mà không thay đổi câu chữ chính hoặc identity anchors.
