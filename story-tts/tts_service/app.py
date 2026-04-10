from __future__ import annotations

import asyncio
import logging
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from RealtimeTTS import TextToAudioStream, EdgeEngine

logger = logging.getLogger("story_tts_realtime")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="story-tts-realtime", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Models ───────────────────────────────────────────────────────────────────


class RealtimeVoice(BaseModel):
    id: str
    name: str
    locale: str
    gender: str
    friendlyName: str


class RealtimeChapterPayload(BaseModel):
    chapterId: int
    chapterIndex: int
    title: str
    text: str


class CreateSessionRequest(BaseModel):
    storyId: int
    chapterId: int
    chapters: list[RealtimeChapterPayload]
    voice: str = "vi-VN-NamMinhNeural"
    speed: int = 0
    pitch: int = 0
    autoNext: bool = True


class UpdateSessionControlsRequest(BaseModel):
    voice: str | None = None
    speed: int | None = None
    pitch: int | None = None
    autoNext: bool | None = None


class SessionResponse(BaseModel):
    id: str
    storyId: int
    chapterId: int
    currentChapterIndex: int
    status: str
    voice: str
    speed: int
    pitch: int
    autoNext: bool


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


# ─── Text Processing ──────────────────────────────────────────────────────────


def normalize_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[-=_*~]{5,}", "\n\n", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = "\n".join(part.strip() for part in cleaned.split("\n"))
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def split_chapter_into_chunks(text: str, num_chunks: int = 20) -> list[str]:
    """Chia chapter thành nhiều đoạn nhỏ để tổng hợp tuần tự."""
    normalized = normalize_text(text)
    if not normalized:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n{2,}", normalized) if part.strip()]
    if not paragraphs:
        return []

    total_chars = sum(len(p) for p in paragraphs)
    chars_per_chunk = total_chars // num_chunks

    if chars_per_chunk < 200:
        return ['\n\n'.join(paragraphs)]

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        current_chunk.append(para)
        current_length += len(para)

        if current_length >= chars_per_chunk and len(chunks) < num_chunks - 1:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
            current_length = 0

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    logger.info("Chapter split into %d chunks (target: %d, avg %d chars each)",
               len(chunks), num_chunks, total_chars // max(len(chunks), 1))
    return chunks


def split_into_segments(text: str, max_chars: int = 600) -> list[str]:
    """Chia text thành các đoạn nhỏ cho highlighting."""
    normalized = normalize_text(text)
    if not normalized:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n{2,}", normalized) if part.strip()]
    if not paragraphs:
        return []

    segments = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            segments.append(paragraph)
        else:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            current = ""
            for sentence in sentences:
                if len(current) + len(sentence) <= max_chars:
                    current += (" " if current else "") + sentence
                else:
                    if current:
                        segments.append(current)
                    current = sentence
            if current:
                segments.append(current)

    return segments


def prepare_tts_segment(text: str) -> str:
    return normalize_text(text)


# ─── RealtimeTTS Synthesis ────────────────────────────────────────────────────


def synthesize_chunk_realtime(
    text: str,
    voice: str,
    speed: int,
    pitch: int,
    session: "RuntimeSession",
    on_chunk_callback,
    max_retries: int = 5,
) -> tuple[int, float]:
    """
    Sử dụng RealtimeTTS để tổng hợp và stream audio real-time.
    Trả về (total_bytes, estimated_duration_seconds).
    """
    if not text.strip():
        return 0, 0.0

    last_error = None
    rate_percent = speed  # RealtimeTTS dùng -100 đến 100
    pitch_hz = pitch      # RealtimeTTS dùng -100 đến 100

    for attempt in range(1, max_retries + 1):
        try:
            # Tạo EdgeEngine với voice được chỉ định
            engine = EdgeEngine(voice=voice)

            # Tạo TextToAudioStream
            stream = TextToAudioStream(engine)
            stream.feed(text)

            # Stream audio real-time với callback
            total_bytes = 0
            chunk_count = 0

            def on_audio_chunk(chunk: bytes):
                nonlocal total_bytes, chunk_count
                total_bytes += len(chunk)
                chunk_count += 1
                on_chunk_callback(chunk)

            # Synthesize và stream real-time
            # muted=True để không play ra loa, chỉ callback
            stream.play(
                on_audio_chunk=on_audio_chunk,
                muted=True,
                rate=rate_percent,
                pitch=pitch_hz,
            )

            if total_bytes > 0:
                # Ước lượng thời lượng: PCM/WAV ~16KB/s cho voice 16kHz mono
                # RealtimeTTS output là PCM format
                speed_factor = 1.0 + (speed / 100.0)
                BYTES_PER_SECOND = 16000  # ~16KB/s cho PCM 16kHz mono
                estimated_duration = total_bytes / (BYTES_PER_SECOND * speed_factor)

                logger.debug("Synthesized chunk: %d bytes (%d chunks), estimated %.1fs",
                           total_bytes, chunk_count, estimated_duration)
                return total_bytes, estimated_duration
            else:
                raise RuntimeError("RealtimeTTS không tạo được audio")

        except Exception as e:
            last_error = e
            logger.warning("RealtimeTTS attempt %d failed: %s", attempt, e)
            if attempt < max_retries:
                wait_time = min(60, 30 + (attempt * 5))
                logger.warning("Waiting %ds before next retry...", wait_time)
                time.sleep(wait_time)
            continue

    raise RuntimeError(f"RealtimeTTS lỗi sau {max_retries} lần thử: {last_error}")


# ─── Session Management ───────────────────────────────────────────────────────


@dataclass
class RuntimeSession:
    id: str
    story_id: int
    chapters: list[RealtimeChapterPayload]
    current_index: int
    voice: str
    speed: int
    pitch: int
    auto_next: bool
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    status: str = "pending"
    last_error: str = ""
    pending_index: int | None = None
    loop: Any = None
    outbox: Any = None
    worker: threading.Thread | None = None
    stop_requested: threading.Event = field(default_factory=threading.Event)
    current_stream: Any = None
    lock: threading.RLock = field(default_factory=threading.RLock)
    closed: threading.Event = field(default_factory=threading.Event)

    def to_response(self) -> SessionResponse:
        chapter = self.chapters[self.current_index]
        return SessionResponse(
            id=self.id,
            storyId=self.story_id,
            chapterId=chapter.chapterId,
            currentChapterIndex=chapter.chapterIndex,
            status=self.status,
            voice=self.voice,
            speed=self.speed,
            pitch=self.pitch,
            autoNext=self.auto_next,
        )

    def attach(self, loop, outbox) -> None:
        with self.lock:
            self.loop = loop
            self.outbox = outbox

    def start(self) -> None:
        with self.lock:
            if self.worker and self.worker.is_alive():
                return
            self.worker = threading.Thread(
                target=self._run,
                daemon=True,
                name=f"tts-session-{self.id}"
            )
            self.worker.start()
            logger.info("Worker thread started for session %s", self.id)

    def stop(self) -> None:
        self.stop_requested.set()
        self._stop_stream()

    def skip(self, delta: int) -> None:
        with self.lock:
            target_index = max(0, min(self.current_index + delta, len(self.chapters) - 1))
            self.pending_index = target_index
        self._stop_stream()

    def update_controls(self, controls: UpdateSessionControlsRequest) -> SessionResponse:
        with self.lock:
            if controls.voice is not None and controls.voice.strip():
                self.voice = controls.voice.strip()
            if controls.speed is not None:
                self.speed = max(-100, min(100, controls.speed))
            if controls.pitch is not None:
                self.pitch = max(-120, min(120, controls.pitch))
            if controls.autoNext is not None:
                self.auto_next = controls.autoNext

            payload = {
                "type": "controls_updated",
                "sessionId": self.id,
                "voice": self.voice,
                "speed": self.speed,
                "pitch": self.pitch,
                "autoNext": self.auto_next,
            }

        self.emit_event(payload)
        return self.to_response()

    def _stop_stream(self) -> None:
        stream = self.current_stream
        if stream is not None:
            try:
                stop = getattr(stream, "stop", None)
                if callable(stop):
                    stop()
            except Exception:
                logger.exception("Không dừng được realtime stream")

    def emit_event(self, payload: dict[str, Any]) -> None:
        self.updated_at = now_iso()
        if not self.loop or not self.outbox:
            logger.warning("Cannot emit event %s: loop=%s, outbox=%s",
                         payload.get("type"), self.loop is not None, self.outbox is not None)
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.outbox.put({"kind": "event", "payload": payload}),
                self.loop
            )
        except Exception as e:
            logger.error("Failed to emit event %s: %s", payload.get("type"), e)

    def emit_audio(self, payload: bytes) -> None:
        if not payload or not self.loop or not self.outbox:
            return
        asyncio.run_coroutine_threadsafe(
            self.outbox.put({"kind": "audio", "payload": payload}),
            self.loop,
        )

    def _run(self) -> None:
        logger.info("Worker thread started for session %s", self.id)
        try:
            self.status = "streaming"
            logger.info("Emitting session_started event for session %s", self.id)
            self.emit_event({
                "type": "session_started",
                "sessionId": self.id,
                "storyId": self.story_id,
                "chapterId": self.chapters[self.current_index].chapterId,
                "chapterIndex": self.chapters[self.current_index].chapterIndex,
                "voice": self.voice,
                "speed": self.speed,
                "pitch": self.pitch,
                "autoNext": self.auto_next,
            })
            self.emit_event({"type": "audio_format", "mime": "audio/wav"})
            logger.info("Session %s setup complete, starting chapter loop", self.id)

            chapter_index = self.current_index
            while chapter_index < len(self.chapters):
                if self.stop_requested.is_set():
                    self.status = "stopped"
                    self.emit_event({"type": "stopped", "sessionId": self.id})
                    break

                with self.lock:
                    if self.pending_index is not None:
                        chapter_index = self.pending_index
                        self.pending_index = None
                    self.current_index = chapter_index

                chapter = self.chapters[chapter_index]
                logger.info("Starting chapter %d: %s", chapter.chapterIndex, chapter.title)
                self.emit_event({
                    "type": "chapter_started",
                    "sessionId": self.id,
                    "storyId": self.story_id,
                    "chapterId": chapter.chapterId,
                    "chapterIndex": chapter.chapterIndex,
                    "chapterTitle": chapter.title,
                })

                interrupted = self._stream_chapter(chapter)
                if self.stop_requested.is_set():
                    self.status = "stopped"
                    self.emit_event({"type": "stopped", "sessionId": self.id})
                    break

                with self.lock:
                    if self.pending_index is not None:
                        self.emit_event({
                            "type": "chapter_transition",
                            "sessionId": self.id,
                            "fromChapterId": chapter.chapterId,
                            "toChapterId": self.chapters[self.pending_index].chapterId,
                            "reason": "skip",
                        })
                        chapter_index = self.pending_index
                        self.pending_index = None
                        continue

                if interrupted:
                    continue

                self.emit_event({
                    "type": "chapter_finished",
                    "sessionId": self.id,
                    "chapterId": chapter.chapterId,
                    "chapterIndex": chapter.chapterIndex,
                })
                if not self.auto_next:
                    self.status = "stopped"
                    self.emit_event({"type": "stopped", "sessionId": self.id})
                    break

                if chapter_index >= len(self.chapters) - 1:
                    self.status = "completed"
                    self.emit_event({
                        "type": "story_finished",
                        "sessionId": self.id,
                        "storyId": self.story_id,
                    })
                    break

                next_chapter = self.chapters[chapter_index + 1]
                self.emit_event({
                    "type": "chapter_transition",
                    "sessionId": self.id,
                    "fromChapterId": chapter.chapterId,
                    "toChapterId": next_chapter.chapterId,
                    "reason": "auto_next",
                })
                chapter_index += 1

        except Exception as exc:
            logger.exception("RealtimeTTS session lỗi")
            self.status = "failed"
            self.last_error = str(exc)
            self.emit_event({"type": "error", "sessionId": self.id, "message": str(exc)})
        finally:
            self.closed.set()
            self.emit_event({"type": "stream_closed", "sessionId": self.id, "status": self.status})

    def _stream_chapter(self, chapter: RealtimeChapterPayload) -> bool:
        # Chia chapter thành nhiều đoạn nhỏ
        large_chunks = split_chapter_into_chunks(chapter.text, num_chunks=20)
        if not large_chunks:
            return False

        logger.info("Chapter %d split into %d chunks for sequential synthesis",
                   chapter.chapterIndex, len(large_chunks))

        chunk_failures = 0
        max_chunk_failures = max(3, len(large_chunks) // 3)

        interrupted = False
        chunk_index = 0
        successful_chunks = 0

        for chunk in large_chunks:
            prepared_chunk = prepare_tts_segment(chunk)
            if not prepared_chunk:
                chunk_index += 1
                continue

            with self.lock:
                current_voice = self.voice
                current_speed = self.speed
                current_pitch = self.pitch
                pending_index = self.pending_index

            if self.stop_requested.is_set() or pending_index is not None:
                interrupted = True
                break

            # Chia chunk thành sub-segments cho highlighting
            sub_segments = split_into_segments(prepared_chunk, max_chars=600)

            logger.info("Synthesizing chunk %d/%d (%d chars, %d segments)",
                       chunk_index + 1, len(large_chunks), len(prepared_chunk), len(sub_segments))

            self.emit_event({
                "type": "chunk_started",
                "sessionId": self.id,
                "chunkIndex": chunk_index,
                "totalChunks": len(large_chunks),
            })

            # Tổng hợp chunk với RealtimeTTS (stream real-time)
            total_bytes = 0
            estimated_duration = 0.0
            retry_count = 0

            while total_bytes == 0:
                if retry_count > 0:
                    wait_time = min(60, 30 + (retry_count * 3))
                    logger.warning("Chunk %d failed (attempt #%d), waiting %ds before retry...",
                                 chunk_index, retry_count, wait_time)

                    wait_start = time.time()
                    while time.time() - wait_start < wait_time:
                        if self.stop_requested.is_set():
                            logger.info("Stop requested during retry wait for chunk %d", chunk_index)
                            interrupted = True
                            break
                        with self.lock:
                            if self.pending_index is not None:
                                logger.info("Pending index changed during retry wait for chunk %d", chunk_index)
                                interrupted = True
                                break
                        time.sleep(1)

                    if interrupted:
                        break

                try:
                    def on_audio_chunk_callback(chunk: bytes):
                        nonlocal total_bytes
                        total_bytes += len(chunk)
                        self.emit_audio(chunk)

                    total_bytes, estimated_duration = synthesize_chunk_realtime(
                        prepared_chunk,
                        current_voice,
                        current_speed,
                        current_pitch,
                        self,
                        on_audio_chunk_callback,
                        max_retries=3,
                    )
                except Exception as e:
                    retry_count += 1
                    logger.error("Chunk %d synthesis failed (retry #%d): %s", chunk_index, retry_count, e)
                    continue

            if interrupted:
                break

            if total_bytes == 0:
                logger.warning("Chunk %d synthesis returned empty audio", chunk_index)
                chunk_failures += 1
                chunk_index += 1
                continue

            successful_chunks += 1
            logger.info("Chunk %d synthesized successfully (%d bytes, %.1fs) after %d retries",
                       chunk_index, total_bytes, estimated_duration, retry_count)

            # Tính timing cho segment events
            seconds_per_sub = estimated_duration / max(len(sub_segments), 1)
            BUFFER_DELAY_SEC = 1.0  # RealtimeTTS stream real-time nên buffer ít hơn
            effective_start_time = time.time() + BUFFER_DELAY_SEC

            logger.info("Chunk %d: %d bytes, estimated %.1fs (%.2fs per segment, speed=%.0f%%)",
                       chunk_index, total_bytes, estimated_duration, seconds_per_sub, current_speed)

            # Emit segment events với delay đồng bộ playback
            sub_index = 0
            for sub_idx in range(len(sub_segments)):
                emit_time = effective_start_time + (sub_idx * seconds_per_sub)
                wait_sec = emit_time - time.time()

                if wait_sec > 0:
                    time.sleep(wait_sec)

                if self.stop_requested.is_set():
                    interrupted = True
                    break
                with self.lock:
                    if self.pending_index is not None:
                        interrupted = True
                        break

                sub_index = sub_idx
                self.emit_event({
                    "type": "segment_started",
                    "sessionId": self.id,
                    "segmentIndex": sub_index,
                    "totalSegments": len(sub_segments),
                    "chunkIndex": chunk_index,
                    "segmentText": sub_segments[sub_index][:200],
                })

            if interrupted:
                break

            with self.lock:
                self.current_stream = None

            self.emit_event({
                "type": "chunk_finished",
                "sessionId": self.id,
                "chunkIndex": chunk_index,
            })

            chunk_index += 1

        logger.info("Chapter %d finished: %d/%d chunks successful, %d failed",
                   chapter.chapterIndex, successful_chunks, len(large_chunks), chunk_failures)
        return interrupted


class SessionRegistry:
    def __init__(self) -> None:
        self._items: dict[str, RuntimeSession] = {}
        self._lock = threading.RLock()

    def create(self, request: CreateSessionRequest) -> RuntimeSession:
        if not request.chapters:
            raise HTTPException(status_code=400, detail="Danh sách chương trống")

        try:
            current_index = next(
                index for index, item in enumerate(request.chapters)
                if item.chapterId == request.chapterId
            )
        except StopIteration as exc:
            raise HTTPException(status_code=400, detail="Không tìm thấy chapterId trong danh sách chương") from exc

        session = RuntimeSession(
            id=uuid.uuid4().hex,
            story_id=request.storyId,
            chapters=request.chapters,
            current_index=current_index,
            voice=request.voice or "vi-VN-NamMinhNeural",
            speed=request.speed,
            pitch=request.pitch,
            auto_next=request.autoNext,
        )
        with self._lock:
            self._items[session.id] = session
        return session

    def get(self, session_id: str) -> RuntimeSession:
        with self._lock:
            session = self._items.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy session realtime")
        return session

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            total = len(self._items)
            active = sum(1 for item in self._items.values() if item.status in {"pending", "streaming"})
            items = [item.to_response() for item in self._items.values()]
        return {"total": total, "active": active, "items": items}

    def remove(self, session_id: str) -> None:
        with self._lock:
            session = self._items.pop(session_id, None)
        if session:
            session.stop()


# ─── App State ────────────────────────────────────────────────────────────────


registry = SessionRegistry()

DEFAULT_VOICE = "vi-VN-NamMinhNeural"

VIETNAMESE_VOICES = [
    RealtimeVoice(id="vi-VN-HoaiMyNeural", name="vi-VN-HoaiMyNeural", locale="vi-VN", gender="Female", friendlyName="Microsoft HoaiMy Online (Natural) - Vietnamese"),
    RealtimeVoice(id="vi-VN-NamMinhNeural", name="vi-VN-NamMinhNeural", locale="vi-VN", gender="Male", friendlyName="Microsoft NamMinh Online (Natural) - Vietnamese"),
]


# ─── API Routes ───────────────────────────────────────────────────────────────


@app.get("/voices")
def list_voices() -> dict[str, Any]:
    return {"items": VIETNAMESE_VOICES, "defaultVoice": DEFAULT_VOICE}


@app.post("/sessions")
def create_session(request: CreateSessionRequest) -> SessionResponse:
    session = registry.create(request)
    return session.to_response()


@app.get("/sessions")
def list_sessions() -> dict[str, Any]:
    return registry.snapshot()


@app.websocket("/sessions/{session_id}/stream")
async def stream_session(session_id: str, websocket: WebSocket):
    await websocket.accept()
    session = registry.get(session_id)

    outbox: asyncio.Queue = asyncio.Queue()
    session.attach(asyncio.get_running_loop(), outbox)
    session.start()

    try:
        while True:
            message = await outbox.get()
            if message["kind"] == "event":
                await websocket.send_json(message["payload"])
            elif message["kind"] == "audio":
                await websocket.send_bytes(message["payload"])
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
    except Exception as e:
        logger.exception("WebSocket error for session %s: %s", session_id, e)
    finally:
        session.stop()


@app.post("/sessions/{session_id}/stop")
def stop_session(session_id: str) -> dict[str, str]:
    session = registry.get(session_id)
    session.stop()
    return {"status": "stopped", "id": session_id}


@app.post("/sessions/{session_id}/skip-next")
def skip_next(session_id: str) -> dict[str, str]:
    session = registry.get(session_id)
    session.skip(1)
    return {"status": "skipped", "id": session_id}


@app.post("/sessions/{session_id}/skip-prev")
def skip_prev(session_id: str) -> dict[str, str]:
    session = registry.get(session_id)
    session.skip(-1)
    return {"status": "skipped", "id": session_id}


@app.post("/sessions/{session_id}/controls")
def update_controls(session_id: str, controls: UpdateSessionControlsRequest) -> SessionResponse:
    session = registry.get(session_id)
    return session.update_controls(controls)


# ─── Main ────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010, log_level="info")
