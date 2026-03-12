# AGENTS.md

## Mục tiêu dự án

Đây là dự án thuần thư mục để quản lý clipart theo từng chủ đề. Mỗi chủ đề là một hồ sơ riêng, chứa brief, prompt, ảnh và toàn bộ gói bán hàng cho Etsy cùng Pinterest trong cùng một nơi.

## Nguyên tắc nền

- Dự án này là một `prompt factory` tổng quát cho clipart theo chủ đề.
- Mặc định tối ưu cho `digital clipart bundle` bán trên Etsy và marketing trên Pinterest.
- Nội dung bán hàng mặc định là `English only` để phù hợp thị trường quốc tế.
- Không mặc định bó buộc vào Lumina hay bất kỳ universe nào.
- Nếu brief hoặc `_topic.md` có chỉ định preset, lore pack, style pack hoặc brand pack thì mới áp dụng.
- Ảnh tạo ra sau này cũng phải được lưu trong đúng thư mục chủ đề để quản lý xuyên suốt.

## Nguồn ngữ cảnh

Luôn đọc:

1. `AGENTS.md`
2. File `_topic.md` của chủ đề đang làm
3. File brief trong `01_briefs`
4. Ghi chú policy trong thư mục `marketplaces`

Chỉ đọc `.agent/*` khi xảy ra một trong các trường hợp sau:

1. Người dùng yêu cầu dùng Lumina
2. `_topic.md` ghi rõ preset là `Lumina`
3. Brief yêu cầu bám một lore/style pack nằm trong `.agent`

Hiện tại `.agent` đang là bộ preset mẫu cho Lumina, không phải luật bắt buộc cho mọi chủ đề.

Nếu có xung đột, ưu tiên theo thứ tự:

1. Yêu cầu mới nhất của người dùng
2. `AGENTS.md`
3. `_topic.md`
4. Brief đang xử lý
5. Preset hoặc lore pack được chỉ định
6. Notes trong `marketplaces`

## Workflow chuẩn

1. Tìm chủ đề trong thư mục `topics`.
2. Nếu chưa có chủ đề, tạo mới một thư mục chủ đề theo `kebab-case`.
3. Mỗi chủ đề phải có cấu trúc:
   - `_topic.md`
   - `01_briefs`
   - `02_prompts`
   - `03_images_raw`
   - `04_images_selected`
   - `05_images_final`
   - `06_notes`
   - `07_etsy`
   - `08_pinterest`
4. Đọc `_topic.md`, brief cần xử lý, và notes policy marketplace.
5. Xác định có dùng preset/lore pack hay không.
6. Sinh mặc định 4 lớp đầu ra:
   - prompt set trong `02_prompts`
   - Etsy listing pack trong `07_etsy`
   - Etsy asset plan trong `07_etsy`
   - Pinterest pin pack trong `08_pinterest`
7. Khi có ảnh mới, lưu hoặc sắp xếp ảnh vào đúng thư mục ảnh của chủ đề.
8. Nếu có hơn 20 ảnh final, chỉ chọn tối đa 20 ảnh tốt nhất cho Etsy listing; phần dư đẩy sang Pinterest queue.
9. Cập nhật lại brief và `_topic.md` khi phù hợp.

## Quy tắc sinh đầu ra

- Nội dung mô tả, ghi chú, docs và comment viết bằng tiếng Việt có dấu.
- Prompt có thể dùng tiếng Anh để tối ưu cho công cụ tạo ảnh.
- Etsy title, description và tags mặc định viết bằng tiếng Anh.
- Pinterest pin copy mặc định viết bằng tiếng Anh.
- Nếu brief có preset rõ ràng thì phải bám đúng preset đó.
- Nếu brief không có preset thì chủ động đề xuất hướng style hợp lý theo chủ đề.
- Với clipart, mặc định nền trắng hoặc nền trong suốt và tỉ lệ `1:1`, trừ khi brief ghi khác.
- Với digital bundle, description phải nói rõ file type, số lượng file, mục đích sử dụng, và không có sản phẩm vật lý được gửi.
- Nếu sản phẩm có AI-generated imagery, Etsy description phải có dòng disclosure phù hợp.
- Mỗi Etsy listing pack mặc định phải có:
  - 3 title options
  - 3 full descriptions
  - 3 tag sets, mỗi set đúng 13 tags
- Mỗi Pinterest pin pack mặc định phải có 10 copy sets với angle khác nhau.

## Cấu trúc thư mục

- `topics`: nơi chứa toàn bộ chủ đề
- `03_templates`: mẫu file để tạo nhanh
- `marketplaces`: ghi chú policy và best practice cho Etsy/Pinterest
- `.agent`: bộ preset mẫu, hiện đang chứa preset Lumina

## Tiêu chuẩn chất lượng

- Không được làm lệch đặc điểm nhận diện nếu brief có mô tả nhân vật hoặc IP riêng.
- Không tự áp preset Lumina khi brief không yêu cầu.
- Ưu tiên prompt rõ ràng, ít mơ hồ, có pose, cảm xúc, đạo cụ và bối cảnh ngắn gọn.
- Etsy title phải front-load keyword chính khi hợp lý, tránh adjective rỗng và tránh nhồi keyword.
- Etsy tags phải là cụm tự nhiên, tránh lặp nguyên văn trong cùng set, và theo logic tối đa 20 ký tự/tag.
- Pinterest copy không làm theo kiểu hashtag-heavy; ưu tiên topic-led và use-case-led.
- Nếu brief thiếu dữ liệu, tự điền giả định hợp lý nhưng phải ghi rõ ở phần `Giả định triển khai`.

## Quy ước quản lý chủ đề

- Tên thư mục chủ đề dùng `kebab-case`, ví dụ: `cute-garden-animals`, `poki-spring-picnic`.
- Mỗi chủ đề có file `_topic.md` để theo dõi:
  - tên chủ đề
  - preset đang dùng
  - trạng thái
  - kênh bán chính
  - ngôn ngữ listing
  - danh sách brief
  - danh sách prompt
  - trạng thái Etsy SEO
  - trạng thái Pinterest pack
  - link listing Etsy
  - link board hoặc URL Pinterest
  - ghi chú về ảnh đã tạo
- Không trộn ảnh của nhiều chủ đề vào cùng một thư mục.
