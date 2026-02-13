<script setup>
/**
 * ImagePreview - Component hiển thị so sánh Before/After ảnh.
 * Support Zoom & Pan.
 */
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useImageStore } from '../stores/imageStore'

const store = useImageStore()

// === Brush Tool Logic ===
const mainCanvas = ref(null)
const maskCanvas = document.createElement('canvas')
const maskCtx = maskCanvas.getContext('2d')
let ctx = null

const isDrawing = ref(false)
const originalImgObj = new Image()

// === Zoom & Pan State ===
const zoomLevel = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const startPanX = ref(0)
const startPanY = ref(0)

// Reset Zoom/Pan when image changes
watch(() => store.originalPreview, () => {
    zoomLevel.value = 1
    panX.value = 0
    panY.value = 0
})

// Watch brush activation
watch(() => store.isBrushActive, async (active) => {
    if (active) {
        await initBrushTool()
    }
})

// Cũng watch resultPreview để cập nhật nếu có thay đổi từ bên ngoài (reset, undo...)
watch(() => store.resultPreview, () => {
    if (store.isBrushActive) {
        initBrushTool()
    }
})

async function initBrushTool() {
    if (!store.originalPreview || !store.fileId) return

    // Load Original Image
    await  new Promise((resolve) => {
        originalImgObj.onload = resolve
        originalImgObj.src = store.originalPreview
    })

    // Load Mask Blob -> Image
    const maskBlob = await store.getMask()
    const maskImgObj = new Image()
    if (maskBlob) {
        await new Promise((resolve) => {
            maskImgObj.onload = resolve
            maskImgObj.src = URL.createObjectURL(maskBlob)
        })
    }

    // Setup Canvas Size (Use Natural Size)
    const w = originalImgObj.naturalWidth
    const h = originalImgObj.naturalHeight

    if (mainCanvas.value) {
        mainCanvas.value.width = w
        mainCanvas.value.height = h
        ctx = mainCanvas.value.getContext('2d')
    }

    maskCanvas.width = w
    maskCanvas.height = h

    // Draw initial mask
    if (maskBlob) {
        maskCtx.clearRect(0, 0, w, h)
        // Draw mask image. 
        maskCtx.drawImage(maskImgObj, 0, 0)
        // Convert Opaque Grayscale -> Alpha Channel
        convertMaskToAlpha()
    } else {
        // Fallback: Giả sử toàn bộ là foreground? Hay background?
        // Thường start là auto remove, nên có mask.
        maskCtx.fillStyle = 'white'
        maskCtx.fillRect(0, 0, w, h)
    }

    renderCanvas()
}

function renderCanvas() {
    if (!ctx || !mainCanvas.value) return
    const w = mainCanvas.value.width
    const h = mainCanvas.value.height

    ctx.clearRect(0, 0, w, h)
    
    // 1. Draw Original Image
    ctx.globalCompositeOperation = 'source-over'
    ctx.drawImage(originalImgObj, 0, 0)

    // 2. Apply Mask (Use destination-in to keep only masked parts)
    ctx.globalCompositeOperation = 'destination-in'
    ctx.drawImage(maskCanvas, 0, 0)
    
    // Reset composite
    ctx.globalCompositeOperation = 'source-over'
}

// Convert Opaque Map to Alpha Map
function convertMaskToAlpha() {
    const w = maskCanvas.width
    const h = maskCanvas.height
    const imgData = maskCtx.getImageData(0, 0, w, h)
    const data = imgData.data
    for (let i = 0; i < data.length; i += 4) {
        const gray = data[i]
        data[i+3] = gray // Alpha = Gray value
    }
    maskCtx.putImageData(imgData, 0, 0)
}

function startDrawing(e) {
    isDrawing.value = true
    draw(e)
}

function stopDrawing() {
    if (!isDrawing.value) return
    isDrawing.value = false
}

function draw(e) {
    if (!isDrawing.value || !mainCanvas.value) return
    
    // Get Coordinates relative to canvas (taking Zoom/Pan into account)
    const rect = mainCanvas.value.getBoundingClientRect()
    
    // Calculate scale factor relative to natural size
    const scaleX = mainCanvas.value.width / rect.width
    const scaleY = mainCanvas.value.height / rect.height
    
    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY
    
    const size = store.brushSize
    
    maskCtx.beginPath()
    maskCtx.arc(x, y, size / 2, 0, Math.PI * 2)
    
    if (store.brushType === 'erase') {
        // Xóa: Xóa Alpha (làm trong suốt)
        maskCtx.globalCompositeOperation = 'destination-out'
        maskCtx.fillStyle = 'rgba(0,0,0,1)'
        maskCtx.fill()
    } else {
        // Khôi phục: Tăng Alpha (làm hiện rõ)
        maskCtx.globalCompositeOperation = 'source-over'
        maskCtx.fillStyle = 'rgba(255,255,255,1)'
        maskCtx.fill()
    }
    
    renderCanvas()
}

async function saveMask() {
    maskCanvas.toBlob(blob => {
        store.updateMask(blob)
    }, 'image/png')
}

/**
 * Xử lý click chọn màu từ ảnh gốc.
 */
function pickColor(event) {
  if (!store.isPickingColor) return

  const img = event.target
  const canvas = document.createElement('canvas')
  canvas.width = img.naturalWidth
  canvas.height = img.naturalHeight
  
  const ctx = canvas.getContext('2d')
  ctx.drawImage(img, 0, 0)
  
  // Tính tọa độ trên ảnh gốc (cần chính xác sau khi zoom/pan?)
  // Click event trên img tag sẽ cho offset relative to img element.
  // Khi zoom/pan, img tag bị transform.
  // event.offsetX/Y có thể dùng được nếu nó relative to target element.
  
  // Tuy nhiên, logic cũ dùng getBoundingClientRect của img.
  const rect = img.getBoundingClientRect()
  const x = Math.floor((event.clientX - rect.left) * (img.naturalWidth / rect.width))
  const y = Math.floor((event.clientY - rect.top) * (img.naturalHeight / rect.height))
  
  // Lấy màu pixel
  const pixel = ctx.getImageData(x, y, 1, 1).data
  store.removeColor = `${pixel[0]},${pixel[1]},${pixel[2]}`
  
  // Tắt chế độ chọn và thông báo
  store.isPickingColor = false
  store.successMessage = `Đã chọn màu: ${store.removeColor}`
}

// === Zoom/Pan Handlers ===

function handleWheel(e) {
    if (e.ctrlKey || e.metaKey || true) { 
        e.preventDefault()
        const delta = e.deltaY > 0 ? -0.1 : 0.1
        const newZoom = Math.max(0.5, Math.min(zoomLevel.value + delta, 5))
        zoomLevel.value = parseFloat(newZoom.toFixed(2))
    }
}

function startPan(e) {
    if (store.isBrushActive) return 
    isPanning.value = true
    startPanX.value = e.clientX - panX.value
    startPanY.value = e.clientY - panY.value
}

function doPan(e) {
    if (!isPanning.value) return
    e.preventDefault()
    // Disable transition during dragging for immediate response
    const container = document.querySelectorAll('.transform-container')
    container.forEach(el => el.style.transition = 'none')
    
    panX.value = e.clientX - startPanX.value
    panY.value = e.clientY - startPanY.value
}

function stopPan() {
    isPanning.value = false
    // Re-enable transition after dragging
    const container = document.querySelectorAll('.transform-container')
    container.forEach(el => el.style.transition = '')
}

function resetView() {
    zoomLevel.value = 1
    panX.value = 0
    panY.value = 0
}

</script>

<template>
  <div class="preview-container">
    <!-- Trạng thái rỗng -->
    <div v-if="!store.hasImage && store.batchFiles.length === 0" class="preview-empty">
      <div class="preview-empty__icon">
        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="0.8" opacity="0.2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
      </div>
      <p class="preview-empty__text">Upload ảnh để bắt đầu xử lý</p>
    </div>

    <!-- Batch Mode Placeholder -->
    <div v-else-if="store.isBatchMode && !store.fileId" class="preview-empty batch-placeholder">
        <div class="batch-icon">🔥</div>
        <p class="preview-empty__text">Chế độ Batch đang kích hoạt</p>
        <p class="preview-empty__subtext">Xem danh sách file và xử lý ở cột bên trái</p>
    </div>

    <!-- Có ảnh -->
    <div v-else class="preview-content">
      <!-- Thông báo -->
      <Transition name="slide-down">
        <div v-if="store.errorMessage" class="alert alert--error">
          <span>❌</span> {{ store.errorMessage }}
          <button class="alert__close" @click="store.errorMessage = ''">×</button>
        </div>
      </Transition>

      <Transition name="slide-down">
        <div v-if="store.successMessage" class="alert alert--success">
          <span>✅</span> {{ store.successMessage }}
          <button class="alert__close" @click="store.successMessage = ''">×</button>
        </div>
      </Transition>

      <!-- Grid Before / After -->
      <div class="preview-grid" :class="{ 'preview-grid--single': !store.hasResult }">
        <!-- Before -->
        <div class="preview-card">
          <div class="preview-card__header">
            <span class="preview-card__badge preview-card__badge--before">TRƯỚC</span>
            <div class="view-controls">
                <button @click="zoomLevel = Math.max(0.5, zoomLevel - 0.5)" class="btn-control">-</button>
                <span class="zoom-text">{{ Math.round(zoomLevel * 100) }}%</span>
                <button @click="zoomLevel = Math.min(5, zoomLevel + 0.5)" class="btn-control">+</button>
                <button @click="resetView" class="btn-control ml-2">Reset</button>
            </div>
          </div>
          <div 
            class="preview-card__body checkerboard overflow-hidden cursor-grab" 
            :class="{ 'cursor-grabbing': isPanning }"
            @wheel.prevent="handleWheel"
            @mousedown="startPan"
            @mousemove="doPan"
            @mouseup="stopPan"
            @mouseleave="stopPan"
            @dblclick="resetView"
          >
            <div class="transform-container" :style="{ transform: `translate(${panX}px, ${panY}px) scale(${zoomLevel})` }">
                <img
                :src="store.originalPreview"
                alt="Ảnh gốc"
                class="preview-card__img"
                draggable="false"
                :class="{ 'cursor-crosshair': store.isPickingColor }"
                @click="pickColor"
                />
            </div>
          </div>
        </div>

        <!-- After -->
        <div v-if="store.hasResult" class="preview-card stagger-enter" style="animation-delay: 0.15s">
          <div class="preview-card__header">
            <span class="preview-card__badge preview-card__badge--after">SAU</span>
          </div>
          <div 
             class="preview-card__body checkerboard overflow-hidden" 
             style="position: relative;"
             @wheel.prevent="handleWheel"
             @mousedown="!store.isBrushActive ? startPan($event) : null"
             @mousemove="!store.isBrushActive ? doPan($event) : null"
             @mouseup="!store.isBrushActive ? stopPan() : null"
             @mouseleave="!store.isBrushActive ? stopPan() : null"
             @dblclick="resetView"
          >
             <div class="transform-container" :style="{ transform: `translate(${panX}px, ${panY}px) scale(${zoomLevel})` }">
                <!-- Result Image (Hidden when brushing) -->
                <img
                v-show="!store.isBrushActive"
                :src="store.resultPreview"
                draggable="false"
                alt="Kết quả"
                class="preview-card__img"
                />

                <!-- Brush Canvas -->
                <canvas 
                    v-show="store.isBrushActive"
                    ref="mainCanvas"
                    class="brush-canvas"
                    @mousedown.stop="startDrawing"
                    @mousemove.stop="draw"
                    @mouseup.stop="stopDrawing"
                    @mouseleave.stop="stopDrawing"
                ></canvas>
            </div>

            <!-- Floating Actions -->
            <div v-if="store.isBrushActive" class="brush-actions">
                <button class="btn-xs btn-primary shadow-lg" @click="saveMask">💾 Lưu Mask</button>
            </div>

          </div>
        </div>
      </div>

      <!-- Loading Overlay -->
      <Transition name="fade">
        <div v-if="store.isProcessing" class="loading-overlay">
          <div class="loading-content">
            <div class="spinner"></div>
            <p class="loading-text">Đang xử lý ảnh...</p>
            <p class="loading-subtext">Vui lòng chờ trong giây lát</p>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
/* ... existing styles ... */
.preview-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  position: relative;
}

.brush-canvas {
    max-width: 100%;
    max-height: 500px;
    object-fit: contain;
    cursor: crosshair;
}

.brush-canvas {
    pointer-events: auto; 
}

.brush-actions {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 10px;
    z-index: 5;
}

.shadow-lg {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
}

.btn-xs {
    padding: 6px 12px;
    font-size: 0.75rem;
    border-radius: 6px;
    cursor: pointer;
    border: none;
    color: white;
}

.btn-primary {
    background: #22d3ee;
    color: #0f172a;
}
.preview-empty {
  height: 100%;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}
.preview-empty__text {
  font-size: 0.95rem;
  color: rgba(226, 232, 240, 0.3);
  font-family: 'Space Grotesk', sans-serif;
}
.preview-empty__subtext {
    font-size: 0.8rem;
    color: rgba(226, 232, 240, 0.2);
}
.batch-icon {
    font-size: 3rem;
    color: #a78bfa;
    margin-bottom: 10px;
    opacity: 0.5;
}
.cursor-crosshair {
    cursor: crosshair;
    outline: 2px solid #22d3ee;
}
.preview-content {
  position: relative;
}
.alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 0.85rem;
  margin-bottom: 16px;
}
.alert--error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}
.alert--success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
  color: #86efac;
}
.alert__close {
  margin-left: auto;
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  opacity: 0.5;
}
.alert__close:hover {
  opacity: 1;
}
.preview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.preview-grid--single {
  grid-template-columns: 1fr;
}
.preview-card {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}
.preview-card__header {
  padding: 10px 14px;
  display: flex;
  align-items: center;
}
.preview-card__badge {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 4px 10px;
  border-radius: 6px;
  text-transform: uppercase;
}
.preview-card__badge--before {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}
.preview-card__badge--after {
  background: rgba(34, 211, 238, 0.15);
  color: #22d3ee;
}
.preview-card__body {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 12px;
}
.preview-card__img {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
  border-radius: 8px;
  margin: 0;
  pointer-events: none; /* Let pan events pass through to container */
}
.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(8, 5, 32, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  z-index: 10;
}
.loading-content {
  text-align: center;
}
.loading-text {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 600;
  color: #e2e8f0;
  margin-top: 16px;
}
.loading-subtext {
  font-size: 0.8rem;
  color: rgba(226, 232, 240, 0.4);
  margin-top: 4px;
}
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}
.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* === Zoom/Pan Styles === */
.overflow-hidden {
    overflow: hidden;
}
.cursor-grab {
    cursor: grab;
}
.cursor-grabbing {
    cursor: grabbing;
}
.transform-container {
    transition: transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94); /* Smooth transition with ease-out */
    transform-origin: center center;
    display: flex;
    align-items: center;
    justify-content: center;
    will-change: transform; /* Optimize performance */
}
.view-controls {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(0,0,0,0.3);
    padding: 2px 8px;
    border-radius: 20px;
}
.btn-control {
    background: rgba(255,255,255,0.1);
    color: white;
    border: none;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    cursor: pointer;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
}
.btn-control:hover {
    background: rgba(255,255,255,0.2);
}
.zoom-text {
    font-size: 0.7rem;
    color: #e2e8f0;
    min-width: 40px;
    text-align: center;
}
.ml-2 {
    margin-left: 8px;
}
</style>
