# story-tts

Project local để quản lý thư mục truyện TXT, mở chương để đọc trực tiếp trong web app và phát `realtime TTS` theo từng chương mà không cần tạo file audio trung gian.

## Trạng thái hiện tại
- Đã scaffold backend `Go + Gin + SQLite`.
- Đã scaffold frontend `Vue 3 + Vite`.
- Đã có notebook canonical: [story-tts - Governance & Docs](https://notebooklm.google.com/notebook/04b036e8-540b-43f7-999a-3d3e1dd8a747).
- Đây là dự án độc lập, không thuộc domain `Andon`; `andon-tts-web-api` chỉ là repo tham chiếu kỹ thuật.
- Luồng chính hiện tại là `folder picker -> import TXT -> đọc chương -> realtime TTS -> lưu tiến độ`.

## Định hướng v1
- Dạng project: `API + web app`
- Repo tham chiếu kỹ thuật: `D:\Tinht00_Workspace\Projects\Andon\andon-tts-web-api`
- Provider ưu tiên hiện tại: `RealtimeTTS + EdgeEngine`
- Input chuẩn: `1 thư mục gốc`, mỗi thư mục con là một truyện, các file `.txt` bên trong là các chương
- Output chuẩn: `đọc text trong app + stream audio realtime + tự chuyển chương`

## Stack hiện tại
- `Go + Gin` cho backend import thư viện, chapter content và reader progress
- `Vue 3 + Vite` cho frontend reader 3 cột, voice control và realtime player
- `FastAPI + RealtimeTTS + EdgeEngine` cho service Python stream audio qua WebSocket
- `NotebookLM` cho governance, research và tri thức dự án

## Cấu trúc hiện tại
- `backend/`: API reader/import, storage SQLite, parser TXT, progress và phần TTS cũ ở trạng thái legacy
- `frontend/`: giao diện local reader với folder picker, danh sách truyện/chương, voice control và realtime stream player
- `tts_service/`: service Python realtime TTS dùng `FastAPI + RealtimeTTS`
- `docs/architecture-v1.md`: kiến trúc v1
- `docs/prosody-presets.md`: preset prosody
- `docs/decision-log.md`: decision log của dự án

## Chạy local
### Backend
```powershell
cd D:\Tinht00_Workspace\Projects\story-tts\backend
Copy-Item .env.example .env
go run ./cmd/api
```

### Realtime TTS Service
```powershell
cd D:\Tinht00_Workspace\Projects\story-tts
D:\Tinht00_Workspace\Projects\story-tts\data\run\tts-venv\Scripts\python.exe -m uvicorn tts_service.app:app --host 127.0.0.1 --port 8010
```

### Frontend
```powershell
cd D:\Tinht00_Workspace\Projects\story-tts\frontend
npm install
npm run dev
```

## Lưu ý vận hành
- Backend Go mặc định chạy ở `:18080`, realtime TTS service chạy ở `http://127.0.0.1:8010`, frontend dev mặc định ở `:5173`.
- Dữ liệu runtime mặc định nằm tại `data/` và thư viện truyện nằm tại `library/`.
- Trên `Chrome/Edge`, app ưu tiên `showDirectoryPicker` để nhớ quyền truy cập thư mục; khi đó nút `Làm mới thư viện` sẽ quét lại đúng thư mục cũ và nhận chương mới vừa thêm.
- Khi import từ folder picker, backend lưu `sourcePath` theo dạng `thu_muc_cha/truyen`, để `Làm mới thư viện` luôn bám theo đúng thư mục cha chứa các truyện con.
- Nếu trình duyệt chỉ hỗ trợ fallback `webkitdirectory`, cần chọn lại thư mục khi muốn nạp thay đổi từ ổ đĩa.
- Mỗi truyện hiển thị dưới dạng card gọn, có tổng số chương, tiến độ chương đang đọc và nút `Đọc tiếp`.
- Reader sẽ tự format nội dung theo nhịp khoảng `3-4 câu/đoạn` để dễ đọc hơn.
- Frontend gọi trực tiếp realtime service bằng `HTTP + WebSocket`, nhận chunk `audio/mpeg` và phát liền mạch qua `MediaSource`.
- Khi đọc xong một chương, session realtime sẽ tự chuyển sang chương kế tiếp cho tới hết truyện.
- Người dùng có thể chọn giọng, chỉnh tốc độ và cao độ trước khi bắt đầu phiên đọc; mặc định hiện tại là `vi-VN-NamMinhNeural`.
- `STORY_TTS_REALTIME_TTS_BASE_URL` phải trỏ đúng về service Python nếu đổi port hoặc host.

## Tài liệu điều hướng
- [AGENTS.md](D:/Tinht00_Workspace/Projects/story-tts/AGENTS.md)
- [.agent/HOW_TO_USE.md](D:/Tinht00_Workspace/Projects/story-tts/.agent/HOW_TO_USE.md)
- [.agent/project_settings.md](D:/Tinht00_Workspace/Projects/story-tts/.agent/project_settings.md)
- [.agent/rules/project_rules.md](D:/Tinht00_Workspace/Projects/story-tts/.agent/rules/project_rules.md)
- [docs/ai-digest.md](D:/Tinht00_Workspace/Projects/story-tts/docs/ai-digest.md)
- [docs/TODO.md](D:/Tinht00_Workspace/Projects/story-tts/docs/TODO.md)
