from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import re
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import edge_tts


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("story_tts_realtime")

DEFAULT_HOST = os.getenv("STORY_TTS_REALTIME_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("STORY_TTS_REALTIME_PORT", "8010"))
DEFAULT_VOICE = os.getenv("STORY_TTS_REALTIME_TTS_VOICE", "vi-VN-HoaiMyNeural")
DEFAULT_SPEED = int(os.getenv("STORY_TTS_REALTIME_TTS_SPEED", "0"))
DEFAULT_PITCH = int(os.getenv("STORY_TTS_REALTIME_TTS_PITCH", "0"))


def resolve_default_edge_binary() -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_venv_binary = os.path.join(
        repo_root,
        "data",
        "run",
        "tts-venv",
        "Scripts",
        "edge-tts.exe",
    )
    if os.path.exists(local_venv_binary):
        return local_venv_binary
    return os.path.expandvars(r"%AppData%\Python\Python313\Scripts\edge-tts.exe")


DEFAULT_EDGE_BINARY = os.getenv("STORY_TTS_EDGE_BINARY", resolve_default_edge_binary())


class ChapterPayload(BaseModel):
    chapterId: int
    chapterIndex: int
    title: str
    text: str


class CreateSessionRequest(BaseModel):
    storyId: int
    chapterId: int
    chapters: list[ChapterPayload] = Field(default_factory=list)
    voice: str | None = None
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


def normalize_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[-=_*~]{5,}", "\n\n", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = "\n".join(part.strip() for part in cleaned.split("\n"))
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def split_hard_segment(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]

    out: list[str] = []
    current = ""

    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > limit:
            out.append(current)
            current = word
            continue
        current = candidate

    if current:
        out.append(current)
    return out


def split_stream_segments(text: str, max_chars: int = 900) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n{2,}", normalized) if part.strip()]
    if not paragraphs:
        return []

    segments: list[str] = []

    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            segments.append(paragraph)
            continue
        segments.extend(split_hard_segment(paragraph, max_chars))

    return segments


def prepare_tts_segment(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return ""
    if normalized[-1] not in ".!?…:;":
        normalized = f"{normalized}."
    return normalized


def synthesize_segment_with_edge_cli(
    text: str,
    voice: str,
    speed: int,
    pitch: int,
    session: "RuntimeSession",
) -> bytes:
    if not text.strip():
        return b""

    edge_binary = DEFAULT_EDGE_BINARY
    if not os.path.exists(edge_binary):
        raise RuntimeError(f"Không tìm thấy edge-tts binary tại {edge_binary}")

    with tempfile.TemporaryDirectory(prefix="story-tts-realtime-") as temp_dir:
        text_path = os.path.join(temp_dir, "segment.txt")
        audio_path = os.path.join(temp_dir, "segment.mp3")
        with open(text_path, "w", encoding="utf-8") as handle:
            handle.write(text)

        base_cmd = [
            edge_binary,
            "--voice",
            voice,
            "--file",
            text_path,
            "--write-media",
            audio_path,
        ]

        command_variants: list[list[str]] = []
        if speed != 0 or pitch != 0:
            variant = [*base_cmd]
            if speed != 0:
                variant.append(f"--rate={format_rate(speed)}")
            if pitch != 0:
                variant.append(f"--pitch={format_pitch(pitch)}")
            command_variants.append(variant)
        command_variants.append(base_cmd)

        last_error = "edge-tts lỗi"
        for cmd in command_variants:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            session.current_stream = process

            while process.poll() is None:
                if session.stop_requested.is_set():
                    process.kill()
                    raise RuntimeError("Đã dừng synth realtime")
                with session.lock:
                    if session.pending_index is not None:
                        process.kill()
                        raise RuntimeError("Đã chuyển chapter khi đang synth")
                time.sleep(0.05)

            stdout, stderr = process.communicate()
            session.current_stream = None

            if process.returncode == 0 and os.path.exists(audio_path):
                break

            last_error = (stderr or stdout or "edge-tts lỗi").strip()
            if os.path.exists(audio_path):
                os.remove(audio_path)
        else:
            raise RuntimeError(last_error)

        if not os.path.exists(audio_path):
            raise RuntimeError("edge-tts không tạo file audio")

        with open(audio_path, "rb") as handle:
            return handle.read()

def clamp_controls(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def format_rate(value: int) -> str:
    value = clamp_controls(value, -100, 100)
    return f"{value:+d}%"


def format_pitch(value: int) -> str:
    value = clamp_controls(value, -100, 100)
    return f"{value:+d}Hz"


@dataclass
class RuntimeSession:
    id: str
    story_id: int
    chapters: list[ChapterPayload]
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
    loop: asyncio.AbstractEventLoop | None = None
    outbox: asyncio.Queue[dict[str, Any]] | None = None
    worker: threading.Thread | None = None
    current_stream: Any | None = None
    stop_requested: threading.Event = field(default_factory=threading.Event)
    closed: threading.Event = field(default_factory=threading.Event)
    lock: threading.RLock = field(default_factory=threading.RLock)

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

    def attach(self, loop: asyncio.AbstractEventLoop, outbox: asyncio.Queue[dict[str, Any]]) -> None:
        with self.lock:
            self.loop = loop
            self.outbox = outbox

    def start(self) -> None:
        with self.lock:
            if self.worker and self.worker.is_alive():
                return
            self.worker = threading.Thread(target=self._run, daemon=True, name=f"tts-session-{self.id}")
            self.worker.start()

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
                self.speed = clamp_controls(controls.speed, -100, 100)
            if controls.pitch is not None:
                self.pitch = clamp_controls(controls.pitch, -120, 120)
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
            return
        asyncio.run_coroutine_threadsafe(self.outbox.put({"kind": "event", "payload": payload}), self.loop)

    def emit_audio(self, payload: bytes) -> None:
        if not payload or not self.loop or not self.outbox:
            return
        asyncio.run_coroutine_threadsafe(self.outbox.put({"kind": "audio", "payload": payload}), self.loop)

    def _run(self) -> None:
        try:
            self.status = "streaming"
            self.emit_event(
                {
                    "type": "session_started",
                    "sessionId": self.id,
                    "storyId": self.story_id,
                    "chapterId": self.chapters[self.current_index].chapterId,
                    "chapterIndex": self.chapters[self.current_index].chapterIndex,
                    "voice": self.voice,
                    "speed": self.speed,
                    "pitch": self.pitch,
                    "autoNext": self.auto_next,
                }
            )
            self.emit_event({"type": "audio_format", "mime": "audio/mpeg"})

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
                self.emit_event(
                    {
                        "type": "chapter_started",
                        "sessionId": self.id,
                        "storyId": self.story_id,
                        "chapterId": chapter.chapterId,
                        "chapterIndex": chapter.chapterIndex,
                        "chapterTitle": chapter.title,
                    }
                )

                interrupted = self._stream_chapter(chapter)
                if self.stop_requested.is_set():
                    self.status = "stopped"
                    self.emit_event({"type": "stopped", "sessionId": self.id})
                    break

                with self.lock:
                    if self.pending_index is not None:
                        self.emit_event(
                            {
                                "type": "chapter_transition",
                                "sessionId": self.id,
                                "fromChapterId": chapter.chapterId,
                                "toChapterId": self.chapters[self.pending_index].chapterId,
                                "reason": "skip",
                            }
                        )
                        chapter_index = self.pending_index
                        self.pending_index = None
                        continue

                if interrupted:
                    continue

                self.emit_event(
                    {
                        "type": "chapter_finished",
                        "sessionId": self.id,
                        "chapterId": chapter.chapterId,
                        "chapterIndex": chapter.chapterIndex,
                    }
                )
                if not self.auto_next:
                    self.status = "stopped"
                    self.emit_event({"type": "stopped", "sessionId": self.id})
                    break

                if chapter_index >= len(self.chapters) - 1:
                    self.status = "completed"
                    self.emit_event({"type": "story_finished", "sessionId": self.id, "storyId": self.story_id})
                    break

                next_chapter = self.chapters[chapter_index + 1]
                self.emit_event(
                    {
                        "type": "chapter_transition",
                        "sessionId": self.id,
                        "fromChapterId": chapter.chapterId,
                        "toChapterId": next_chapter.chapterId,
                        "reason": "auto_next",
                    }
                )
                chapter_index += 1
        except Exception as exc:
            logger.exception("RealtimeTTS session lỗi")
            self.status = "failed"
            self.last_error = str(exc)
            self.emit_event({"type": "error", "sessionId": self.id, "message": str(exc)})
        finally:
            self.closed.set()
            self.emit_event({"type": "stream_closed", "sessionId": self.id, "status": self.status})

    def _stream_chapter(self, chapter: ChapterPayload) -> bool:
        segments = split_stream_segments(chapter.text)
        if not segments:
            return False

        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                interrupted = False
                for segment in segments:
                    prepared_segment = prepare_tts_segment(segment)
                    if not prepared_segment:
                        continue

                    with self.lock:
                        current_voice = self.voice
                        current_speed = self.speed
                        current_pitch = self.pitch
                        pending_index = self.pending_index

                    if self.stop_requested.is_set() or pending_index is not None:
                        interrupted = True
                        break

                    audio_bytes = synthesize_segment_with_edge_cli(
                        prepared_segment,
                        current_voice,
                        current_speed,
                        current_pitch,
                        self,
                    )
                    if not audio_bytes:
                        continue

                    for offset in range(0, len(audio_bytes), 32 * 1024):
                        if self.stop_requested.is_set():
                            interrupted = True
                            break
                        with self.lock:
                            if self.pending_index is not None:
                                interrupted = True
                                break
                        self.emit_audio(audio_bytes[offset : offset + 32 * 1024])

                    if interrupted:
                        break

                    with self.lock:
                        self.current_stream = None

                return interrupted
            except Exception as exc:
                last_error = exc
                logger.warning("Retry realtime chapter %s lần %s do lỗi: %s", chapter.chapterId, attempt, exc)
                if self.stop_requested.is_set():
                    return True
                with self.lock:
                    if self.pending_index is not None:
                        return True
                if attempt < 3:
                    time.sleep(1.2 * attempt)
                    continue
            finally:
                self.current_stream = None

        raise RuntimeError(str(last_error) if last_error else f"RealtimeTTS không tạo được audio cho chương {chapter.chapterIndex}")


class SessionRegistry:
    def __init__(self) -> None:
        self._items: dict[str, RuntimeSession] = {}
        self._lock = threading.RLock()

    def create(self, request: CreateSessionRequest) -> RuntimeSession:
        if not request.chapters:
            raise HTTPException(status_code=400, detail="Danh sách chương trống")

        try:
            current_index = next(index for index, item in enumerate(request.chapters) if item.chapterId == request.chapterId)
        except StopIteration as exc:
            raise HTTPException(status_code=400, detail="Không tìm thấy chapterId trong danh sách chương") from exc

        session = RuntimeSession(
            id=uuid.uuid4().hex,
            story_id=request.storyId,
            chapters=request.chapters,
            current_index=current_index,
            voice=request.voice or DEFAULT_VOICE,
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
        return {"totalSessions": total, "activeSessions": active}


app = FastAPI(title="story-tts-realtime")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

registry = SessionRegistry()


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "story-tts-realtime", "host": DEFAULT_HOST, "port": DEFAULT_PORT, **registry.snapshot()}


@app.get("/voices")
async def voices() -> dict[str, Any]:
    items = []
    for voice in await edge_tts.list_voices():
        items.append(
            {
                "id": voice["ShortName"],
                "name": voice["ShortName"],
                "locale": voice["Locale"],
                "gender": voice.get("Gender", ""),
                "friendlyName": voice.get("FriendlyName") or voice["ShortName"],
            }
        )
    items.sort(key=lambda item: (item["locale"], item["friendlyName"]))
    return {"items": items, "defaultVoice": DEFAULT_VOICE}


@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest) -> SessionResponse:
    session = registry.create(request)
    return session.to_response()


@app.post("/sessions/{session_id}/stop")
async def stop_session(session_id: str) -> dict[str, str]:
    session = registry.get(session_id)
    session.stop()
    return {"status": "stopping", "id": session_id}


@app.post("/sessions/{session_id}/skip-next")
async def skip_next(session_id: str) -> dict[str, str]:
    session = registry.get(session_id)
    session.skip(1)
    return {"status": "skipping", "direction": "next", "id": session_id}


@app.post("/sessions/{session_id}/skip-prev")
async def skip_prev(session_id: str) -> dict[str, str]:
    session = registry.get(session_id)
    session.skip(-1)
    return {"status": "skipping", "direction": "prev", "id": session_id}


@app.post("/sessions/{session_id}/controls", response_model=SessionResponse)
async def update_controls(session_id: str, request: UpdateSessionControlsRequest) -> SessionResponse:
    session = registry.get(session_id)
    return session.update_controls(request)


@app.websocket("/sessions/{session_id}/stream")
async def stream_session(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    session = registry.get(session_id)
    outbox: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    session.attach(asyncio.get_running_loop(), outbox)
    session.start()

    try:
        while True:
            item = await outbox.get()
            if item["kind"] == "event":
                await websocket.send_json(item["payload"])
                if item["payload"].get("type") == "stream_closed":
                    break
            else:
                await websocket.send_bytes(item["payload"])
    except WebSocketDisconnect:
        logger.info("WebSocket session %s đã ngắt kết nối", session_id)
        session.stop()
    finally:
        with contextlib.suppress(Exception):
            await websocket.close()
