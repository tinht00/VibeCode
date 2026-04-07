# Workflow: Development

## Mục tiêu
Ghi nhanh cách chạy local và các lệnh kiểm tra cơ bản của dự án.

## Mẫu cần điền
- Cách cài dependency:
  - Backend: `go mod tidy`
  - Frontend: `npm install`
- Cách chạy local:
  - Backend: `go run ./cmd/api`
  - Frontend: `npm run dev`
- Cách chạy test:
  - Backend: chưa có unit test
  - Frontend: chưa có test runner
- Cách build:
  - Backend: `go build ./...`
  - Frontend: `npm run build`
- Cổng mặc định:
  - Backend: `18080`
  - Frontend: `5173`
- Env quan trọng:
  - `STORY_TTS_LIBRARY_DIR`
  - `STORY_TTS_FFMPEG_PATH`
  - `STORY_TTS_EDGE_BINARY`
  - `STORY_TTS_EDGE_VOICE`
  - `STORY_TTS_TELEGRAM_APP_ID`
  - `STORY_TTS_TELEGRAM_APP_HASH`

## Lưu ý
- Sau khi bootstrap, nên điền file này sớm để các phiên làm việc sau không phải dò lại command cơ bản.
- Nếu dự án có FE và BE riêng, ghi rõ command cho từng phần.
- Khi cần verify end-to-end audio, phải có `ffmpeg` và `edge-tts` thật trên máy.
