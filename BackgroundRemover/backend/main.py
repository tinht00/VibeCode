#!/usr/bin/env python3
"""
Background Remover API - FastAPI server cung cấp REST API cho xử lý ảnh.

Server endpoints:
- POST /api/upload: Upload ảnh
- POST /api/remove-background: Xóa nền
- POST /api/replace-background: Thay nền
- POST /api/refine: Tinh chỉnh mask
- GET /api/download/{file_id}: Tải kết quả
- GET /api/preview/{file_id}: Xem preview
- DELETE /api/session/{file_id}: Xóa session
"""

import io
import uuid
import base64
from pathlib import Path
from typing import Optional, Tuple, List
from contextlib import asynccontextmanager
import io
import zipfile

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from PIL import Image

from background_remover import BackgroundRemover
from config import settings
from errors import (
    AppError,
    SessionNotFoundError,
    ImageProcessingError,
    ValidationError,
    NoResultError,
    register_exception_handlers,
    success_response,
)
from logger import setup_logging, get_logger, RequestLoggingMiddleware
from session_manager import SessionManager
from upscaler import Upscaler

# Init Upscaler (Global to load model once)
# Model sẽ được load trong lifespan để tránh block startup
upscaler = None

# === Thiết lập Logging ===
setup_logging(
    level=settings.LOG_LEVEL,
    json_format=settings.is_production,
)
logger = get_logger(__name__)

# === Cấu hình thư mục ===
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# === Lifespan Manager ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng (startup/shutdown)."""
    # Startup: Log thông tin
    logger.info(
        f"🚀 Background Remover API v1.1.0 khởi động",
        extra={
            "environment": settings.ENVIRONMENT,
            "cors_origins": settings.CORS_ORIGINS,
            "session_ttl": settings.SESSION_TTL_SECONDS,
            "max_sessions": settings.MAX_SESSIONS,
        },
    )

    # Init Upscaler
    global upscaler
    try:
        logger.info("⚡ Đang khởi tạo AI Upscaler (có thể mất vài giây để tải model)...")
        upscaler = Upscaler(model_name="EDSR_x4", scale=4)
        logger.info("✅ AI Upscaler sẵn sàng")
    except Exception as e:
        logger.error(f"❌ Lỗi khởi tạo Upscaler: {e}")
        upscaler = None

    yield
    # Shutdown: Clean up resources nếu cần
    logger.info("🛑 Background Remover API đang dừng...")


# === Khởi tạo FastAPI ===
app = FastAPI(
    title="Background Remover API",
    description="API xóa nền ảnh sử dụng OpenCV và Pillow",
    version="1.1.0",
    lifespan=lifespan,
)

# === Đăng ký Middleware ===
# Request logging (phải đăng ký TRƯỚC CORS)
app.add_middleware(RequestLoggingMiddleware)

# CORS - Origins từ config thay vì cho phép tất cả
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Đăng ký Exception Handlers ===
register_exception_handlers(app)

# === Session Manager ===
sessions = SessionManager()

# === Các hằng số ===
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}


# ============================================================
# Hàm tiện ích nội bộ
# ============================================================


def _parse_color(color_str: Optional[str]) -> Optional[Tuple[int, int, int]]:
    """
    Parse chuỗi màu "R,G,B" thành tuple (R, G, B).

    Args:
        color_str: Chuỗi dạng "255,255,255" hoặc None

    Returns:
        Tuple (R, G, B) hoặc None nếu đầu vào rỗng
    """
    if not color_str:
        return None
    parts = color_str.split(',')
    return tuple(int(p.strip()) for p in parts)


def _image_to_base64(img: Image.Image) -> str:
    """
    Chuyển PIL Image thành chuỗi base64 PNG.

    Args:
        img: PIL Image object

    Returns:
        Chuỗi base64 của ảnh PNG
    """
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def _get_session(file_id: str) -> BackgroundRemover:
    """
    Lấy session hoặc raise SessionNotFoundError.

    Args:
        file_id: ID phiên cần lấy

    Returns:
        BackgroundRemover instance

    Raises:
        SessionNotFoundError: Nếu session không tồn tại hoặc hết hạn
    """
    remover = sessions.get(file_id)
    if remover:
        return remover

    # Thử phục hồi từ file upload (nếu server restart)
    try:
        # Tìm file bắt đầu bằng file_id. (lưu ý dấu chấm)
        for file_path in UPLOAD_DIR.glob(f"{file_id}.*"):
            if file_path.is_file():
                logger.info(f"♻️ Đang phục hồi session {file_id} từ {file_path.name}")
                remover = BackgroundRemover()
                remover.load(str(file_path))
                sessions[file_id] = remover
                return remover
    except Exception as e:
        logger.error(f"❌ Lỗi phục hồi session {file_id}: {e}")

    raise SessionNotFoundError(file_id)


# ============================================================
# API Endpoints
# ============================================================


@app.get("/")
async def root():
    """Endpoint kiểm tra server hoạt động."""
    return success_response(
        data={"version": "1.1.0"},
        message="Background Remover API đang hoạt động",
    )


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload ảnh lên server.

    Args:
        file: File ảnh (jpg, png, webp, bmp)

    Returns:
        file_id, preview, width, height, filename
    """
    # Kiểm tra định dạng file
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            message=f"Định dạng không hỗ trợ: {file.content_type}. "
                    f"Chấp nhận: {', '.join(ALLOWED_IMAGE_TYPES)}",
            details={"content_type": file.content_type},
        )

    # Tạo ID và lưu file
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix.lower() or ".png"
    filepath = UPLOAD_DIR / f"{file_id}{file_ext}"

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Tạo session xử lý ảnh
    remover = BackgroundRemover()
    remover.load(str(filepath))
    sessions.set(file_id, remover)

    # Tạo preview base64
    preview = _image_to_base64(remover.get_image())
    w, h = remover.get_image().size

    logger.info(
        f"Upload thành công: {file.filename} ({w}x{h})",
        extra={"file_id": file_id, "width": w, "height": h},
    )

    return success_response(
        data={
            "file_id": file_id,
            "filename": file.filename,
            "width": w,
            "height": h,
            "preview": preview,
        },
        message="Upload thành công",
    )


@app.post("/api/remove-background")
async def remove_background(
    file_id: str = Form(...),
    method: str = Form("auto"),
    color: Optional[str] = Form(None),
    tolerance: int = Form(30),
    threshold: int = Form(50),
    iterations: int = Form(5),
    ai_model: str = Form("isnet-general-use"),
    alpha_threshold: int = Form(50),
    alpha_matting: bool = Form(False),
):
    """
    Xóa nền ảnh đã upload.

    Args:
        file_id: ID ảnh từ bước upload
        method: Phương pháp - "auto" | "ai" | "color" | "edge" | "grabcut"
        color: Màu nền cần xóa (R,G,B) - chỉ dùng cho method "color"
        tolerance: Ngưỡng tolerance cho method "color" (0-255)
        threshold: Ngưỡng edge detection cho method "edge" (0-255)
        iterations: Số lần lặp cho method "grabcut" (1-20)
        ai_model: Model AI cho method "ai" (u2net, isnet-anime, isnet-general-use...)
        alpha_threshold: Ngưỡng alpha để loại bỏ bóng mờ (0-255, 0=tắt)
        alpha_matting: Bật alpha matting cho viền mượt hơn (chậm hơn)

    Returns:
        result (base64), method_used
    """
    remover = _get_session(file_id)

    # Reset về ảnh gốc trước khi xử lý lại
    remover.image = remover.original.copy()
    remover.mask = None

    try:
        if method in ("ai", "auto"):
             # Cả 'ai' và 'auto' đều dùng AI (nếu có rembg)
             remover.remove_ai(
                 model_name=ai_model,
                 alpha_threshold=alpha_threshold,
                 use_alpha_matting=alpha_matting,
             )
        elif method == "color" and color:
            parsed_color = _parse_color(color)
            remover.remove_color(parsed_color, tolerance=tolerance)
        elif method == "edge":
            remover.remove_edges(threshold=threshold)
        elif method == "grabcut":
            remover.grabcut(iterations=iterations)
        else:
            remover.remove_background(method=method)

        result = _image_to_base64(remover.get_image())

        logger.info(
            f"Xóa nền thành công (method={method})",
            extra={"file_id": file_id, "method": method},
        )

        return success_response(
            data={
                "file_id": file_id,
                "result": result,
                "method_used": method,
                "preview": _image_to_base64(remover.get_image()),
                "download_url": f"/api/download/{file_id}"
            },
            message="Xóa nền thành công",
        )

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"Lỗi xử lý ảnh: {e}", extra={"file_id": file_id})
        raise ImageProcessingError(str(e))


@app.post("/api/batch/process")
async def batch_process_images(
    files: List[UploadFile] = File(...),
    method: str = Form("auto"),
    color: Optional[str] = Form(None),
    tolerance: int = Form(30),
    threshold: int = Form(50),
    iterations: int = Form(5),
    feather: int = Form(2),
    ai_model: str = Form("isnet-anime"),
    alpha_threshold: int = Form(50),
    alpha_matting: bool = Form(False),
):
    """
    API xử lý hàng loạt (Batch Processing) - Trả về danh sách kết quả để review.
    """
    if len(files) > 50:
         raise ValidationError("Chỉ hỗ trợ tối đa 50 ảnh cùng lúc để đảm bảo hiệu năng.")

    results = []

    for file in files:
        try:
            # 1. Đọc và lưu file gốc
            content = await file.read()
            file_id = str(uuid.uuid4())
            file_ext = Path(file.filename).suffix.lower() or ".png"
            filepath = UPLOAD_DIR / f"{file_id}{file_ext}"
            
            with open(filepath, "wb") as f:
                f.write(content)

            # 2. Xử lý xóa nền
            remover = BackgroundRemover()
            remover.load(str(filepath)) # Load từ file để giữ path
            
            # Áp dụng method
            if method in ("ai", "auto"):
                remover.remove_ai(
                    model_name=ai_model,
                    alpha_threshold=alpha_threshold,
                    use_alpha_matting=alpha_matting
                )
            elif method == "color" and color:
                r, g, b = map(int, color.split(","))
                remover.remove_color((r, g, b), tolerance=tolerance)
            elif method == "edge":
                remover.remove_edges(threshold=threshold)
            elif method == "grabcut":
                remover.grabcut(iterations=iterations)
            else:
                # Fallback
                remover.remove_ai(model_name=ai_model)
                
            if feather > 0:
                remover.refine_edges(feather=feather)
            
            # 3. Lưu session
            sessions.set(file_id, remover)

            # 4. Tạo preview result
            result_preview = _image_to_base64(remover.get_image())
            w, h = remover.get_image().size
            
            results.append({
                "id": file_id,
                "filename": file.filename,
                "status": "success",
                "width": w,
                "height": h,
                "preview": result_preview, # Base64 của ảnh kết quả
                "original_preview": _image_to_base64(remover.original) # Để hiện so sánh nếu cần
            })
            
            logger.info(f"Batch processed: {file.filename} ({file_id})")

        except Exception as e:
            logger.error(f"Lỗi xử lý batch file {file.filename}: {e}")
            results.append({
                "id": None,
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })

    return success_response(
        data=results,
        message=f"Đã xử lý {len(results)} ảnh"
    )


@app.post("/api/batch/download")
async def download_batch_result(
    file_ids: List[str] = Form(...), # Nhận list ID từ form data (client gửi dạng 'file_ids': 'id1', 'file_ids': 'id2'...)
):
    """
    Tải file ZIP chứa kết quả của các session ID được gửi lên.
    """
    if not file_ids:
        raise ValidationError("Danh sách file ID không được để trống")
        
    zip_buffer = io.BytesIO()
    
    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_id in file_ids:
                try:
                    remover = sessions.get(file_id)
                    if not remover or not remover.get_image():
                        zip_file.writestr(f"MISSING_{file_id}.txt", "Session expired or not found")
                        continue
                        
                    # Lưu ảnh vào zip
                    img_buffer = io.BytesIO()
                    remover.get_image().save(img_buffer, format="PNG")
                    
                    # Lấy tên file gốc từ filepath nếu có, hoặc dùng ID
                    original_name = Path(remover.filepath).stem if remover.filepath else file_id
                    filename = f"{original_name}_nobg.png"
                    
                    zip_file.writestr(filename, img_buffer.getvalue())
                    
                except Exception as e:
                    zip_file.writestr(f"ERROR_{file_id}.txt", str(e))
                    
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=batch_result_{uuid.uuid4().hex[:8]}.zip"}
        )

    except Exception as e:
         logger.exception(f"Lỗi Download Batch: {e}")
         raise ImageProcessingError(f"Lỗi tạo file ZIP: {e}")


@app.post("/api/mask/update")
async def update_mask(
    file_id: str = Form(...),
    mask_file: UploadFile = File(...)
):
    """
    Cập nhật mask cho session từ file mask upload lên (Brush tool).
    """
    remover = _get_session(file_id)
    
    try:
        content = await mask_file.read()
        mask_img = Image.open(io.BytesIO(content))
        
        # Áp dụng mask
        remover.apply_mask(mask_img)
        
        result = _image_to_base64(remover.get_image())
        
        return success_response(
            data={
                "file_id": file_id,
                "result": result,
            },
            message="Cập nhật mask thành công"
        )
        
    except Exception as e:
        logger.exception(f"Lỗi update mask: {e}", extra={"file_id": file_id})
        raise ImageProcessingError(str(e))


@app.post("/api/replace-background")
async def replace_background(
    file_id: str = Form(...),
    color: Optional[str] = Form(None),
    bg_file: Optional[UploadFile] = File(None)
):
    """
    Thay nền ảnh đã xử lý.

    Args:
        file_id: ID ảnh đã xóa nền
        color: Màu nền mới (R,G,B)
        bg_file: File ảnh nền thay thế

    Returns:
        result (base64)
    """
    remover = _get_session(file_id)

    try:
        if bg_file:
            # Lưu file nền tạm
            bg_path = UPLOAD_DIR / f"bg_{file_id}.png"
            bg_content = await bg_file.read()
            with open(bg_path, "wb") as f:
                f.write(bg_content)
            remover.replace_background(image=str(bg_path))
        elif color:
            parsed_color = _parse_color(color)
            remover.replace_background(color=parsed_color)
        else:
            remover.replace_background(color=(255, 255, 255))

        result = _image_to_base64(remover.get_image())

        logger.info("Thay nền thành công", extra={"file_id": file_id})

        return success_response(
            data={
                "file_id": file_id,
                "result": result,
            },
            message="Thay nền thành công",
        )

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"Lỗi thay nền: {e}", extra={"file_id": file_id})
        raise ImageProcessingError(str(e))


@app.post("/api/refine")
async def refine_edges(
    file_id: str = Form(...),
    feather: int = Form(0),
    expand: int = Form(0),
    contract: int = Form(0)
):
    """
    Tinh chỉnh mask sau khi xóa nền.

    Args:
        file_id: ID ảnh đã xóa nền
        feather: Bán kính feather (0 = không áp dụng)
        expand: Số pixel mở rộng mask (0 = không áp dụng)
        contract: Số pixel thu hẹp mask (0 = không áp dụng)

    Returns:
        result (base64)
    """
    remover = _get_session(file_id)

    try:
        if feather > 0:
            remover.refine_edges(feather=feather)
        if expand > 0:
            remover.expand_mask(pixels=expand)
        if contract > 0:
            remover.contract_mask(pixels=contract)

        result = _image_to_base64(remover.get_image())

        logger.info(
            "Tinh chỉnh thành công",
            extra={
                "file_id": file_id,
                "feather": feather,
                "expand": expand,
                "contract": contract,
            },
        )

        return success_response(
            data={
                "file_id": file_id,
                "result": result,
            },
            message="Tinh chỉnh thành công",
        )

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"Lỗi tinh chỉnh: {e}", extra={"file_id": file_id})
        raise ImageProcessingError(str(e))


@app.get("/api/mask/{file_id}")
async def get_mask(file_id: str):
    """
    Lấy mask hiện tại của ảnh (để chỉnh sửa thủ công).
    """
    remover = _get_session(file_id)
    if not remover.mask:
        # Nếu chưa có mask (ví dụ ảnh gốc chưa xóa nền), tạo mask trắng (giữ nguyên ảnh)
        if remover.original:
             # Mask trắng = giữ nguyên ảnh (alpha=255)
             remover.mask = Image.new("L", remover.original.size, 255)
        else:
             raise ImageProcessingError("Chưa có dữ liệu ảnh/mask")
    
    mask_bytes = io.BytesIO()
    remover.mask.save(mask_bytes, format="PNG")
    mask_bytes.seek(0)
    return StreamingResponse(mask_bytes, media_type="image/png")


@app.post("/api/mask/update")
async def update_mask(
    file_id: str = Form(...),
    mask_file: UploadFile = File(...)
):
    """
    Cập nhật mask từ frontend (Brush tool).
    """
    remover = _get_session(file_id)
    try:
        content = await mask_file.read()
        mask_image = Image.open(io.BytesIO(content))
        remover.apply_mask(mask_image)
        result = _image_to_base64(remover.get_image())
        
        return success_response(
            data={"file_id": file_id, "result": result},
            message="Cập nhật mask thành công"
        )
    except Exception as e:
        raise ImageProcessingError(str(e))


@app.get("/api/download/{file_id}")
async def download_result(file_id: str, format: str = "png"):
    """
    Tải ảnh kết quả.

    Args:
        file_id: ID ảnh đã xử lý
        format: Định dạng xuất - "png" | "webp" | "jpeg"

    Returns:
        File ảnh kết quả
    """
    remover = _get_session(file_id)
    img = remover.get_image()

    if img is None:
        raise NoResultError(file_id)

    # Lưu ra file tạm và trả về
    output_path = OUTPUT_DIR / f"{file_id}_result.{format}"
    remover.save(str(output_path))

    media_types = {
        "png": "image/png",
        "webp": "image/webp",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
    }

    logger.info(
        f"Download kết quả (format={format})",
        extra={"file_id": file_id, "format": format},
    )

    return FileResponse(
        path=str(output_path),
        media_type=media_types.get(format, "image/png"),
        filename=f"background_removed.{format}",
    )


@app.get("/api/preview/{file_id}")
async def preview_image(file_id: str):
    """
    Xem preview ảnh gốc.

    Args:
        file_id: ID ảnh

    Returns:
        original (base64), current (base64), has_mask
    """
    remover = _get_session(file_id)

    original = _image_to_base64(remover.original)
    current = _image_to_base64(remover.get_image())

    return success_response(
        data={
            "file_id": file_id,
            "original": original,
            "current": current,
            "has_mask": remover.mask is not None,
        },
        message="Preview thành công",
    )


@app.delete("/api/session/{file_id}")
async def delete_session(file_id: str):
    """
    Xóa session và dọn dẹp file tạm.

    Args:
        file_id: ID ảnh cần xóa
    """
    sessions.delete(file_id)

    # Xóa file upload tạm
    for f in UPLOAD_DIR.glob(f"{file_id}*"):
        f.unlink(missing_ok=True)
    for f in OUTPUT_DIR.glob(f"{file_id}*"):
        f.unlink(missing_ok=True)

    logger.info("Xóa session thành công", extra={"file_id": file_id})

    return success_response(message="Đã xóa session")





@app.post("/api/upscale")
async def upscale_image(
    file_id: str = Form(...),
):
    """
    Nâng cấp độ phân giải ảnh (Upscale 4x) sử dụng AI model.
    """
    remover = _get_session(file_id)
    if not remover:
        raise SessionNotFoundError()

    logger.info(f"Yêu cầu Upscale ảnh {file_id}", extra={"file_id": file_id})

    try:
        # Lấy ảnh hiện tại (đã xóa nền hoặc chưa)
        current_image = remover.get_image()
        
        # Upscale
        # Lưu ý: upscale có thể lâu (10-20s trên CPU)
        upscaled_image = upscaler.process(current_image)
        
        # Cập nhật session
        # 1. Update image
        remover.image = upscaled_image
        
        # 2. Update mask nếu có (resize mask theo kích thước mới)
        if remover.mask:
            remover.mask = remover.mask.resize(upscaled_image.size, Image.Resampling.LANCZOS)
            
        return success_response(
            message="Upscale thành công",
            data={
                "image": _image_to_base64(upscaled_image),
                "width": upscaled_image.width,
                "height": upscaled_image.height
            }
        )
    except Exception as e:
        logger.error(f"Lỗi Upscale: {e}")
        # Không raise lỗi 500 để client có thể handle gracefully
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
    )
