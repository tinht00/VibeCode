<script setup>
/**
 * ImageUploader - Component upload ảnh bằng Drag & Drop hoặc click chọn file.
 *
 * Tính năng:
 * - Drag & Drop zone với visual feedback
 * - Click để mở file dialog
 * - Hiển thị thumbnail preview sau upload
 * - Loading state khi đang upload
 *
 * Emits:
 *   uploaded: Khi upload thành công
 */
import { ref } from 'vue'
import { useImageStore } from '../stores/imageStore'

const store = useImageStore()

/** Trạng thái đang kéo file qua drop zone */
const isDragging = ref(false)
/** Ref tới input file ẩn */
const fileInput = ref(null)

/**
 * Xử lý khi kéo file vào vùng drop.
 * Ngăn hành vi mặc định và hiển thị visual feedback.
 */
function onDragOver(event) {
  event.preventDefault()
  isDragging.value = true
}

/**
 * Xử lý khi kéo file ra khỏi vùng drop.
 */
function onDragLeave() {
  isDragging.value = false
}

/**
 * Xử lý khi thả file vào vùng drop.
 * Lấy file đầu tiên và gọi handleFile().
 */
function onDrop(event) {
  event.preventDefault()
  isDragging.value = false

  const files = event.dataTransfer.files
  if (files.length > 0) {
    if (store.isBatchMode) {
      handleFiles(Array.from(files))
    } else {
      handleFile(files[0])
    }
  }
}

/**
 * Mở file dialog khi click vào drop zone.
 */
function openFileDialog() {
  fileInput.value?.click()
}

/**
 * Xử lý khi chọn file từ dialog.
 */
function onFileSelected(event) {
  const files = event.target.files
  if (files.length > 0) {
    if (store.isBatchMode) {
        handleFiles(Array.from(files))
    } else {
        handleFile(files[0])
    }
  }
}

/**
 * Upload file lên server qua store.
 *
 * Args:
 *   file: File object cần upload
 */
async function handleFile(file) {
  if (!validateFile(file)) return
  await store.uploadImage(file)
}

/**
 * Xử lý danh sách file (Batch).
 */
function handleFiles(files) {
    const validFiles = files.filter(validateFile)
    if (validFiles.length > 0) {
        store.batchFiles = [...store.batchFiles, ...validFiles].slice(0, 50) // Limit 50
        if (validFiles.length < files.length) {
            store.errorMessage = "Một số file không hợp lệ đã bị bỏ qua."
        }
    }
}

function validateFile(file) {
  const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']
  if (!validTypes.includes(file.type)) {
    store.errorMessage = 'Chỉ hỗ trợ định dạng: JPG, PNG, WEBP, BMP'
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    store.errorMessage = 'File quá lớn! Tối đa 20MB'
    return false
  }
  return true
}
</script>

<template>
  <div class="uploader-container">
    <!-- Drop Zone -->
    <div
      v-if="!store.hasImage && store.batchFiles.length === 0"
      class="drop-zone"
      :class="{ 'drop-zone--active': isDragging, 'drop-zone--loading': store.isUploading }"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
      @click="openFileDialog"
    >
      <!-- Icon Upload -->
      <div class="drop-zone__icon" :class="{ 'animate-float': !store.isUploading }">
        <svg v-if="!store.isUploading" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <div v-else class="spinner"></div>
      </div>

      <!-- Text -->
      <h3 class="drop-zone__title">
        {{ store.isUploading ? 'Đang tải lên...' : 'Kéo thả ảnh vào đây' }}
      </h3>
      <p class="drop-zone__subtitle">
        {{ store.isUploading ? 'Vui lòng chờ' : 'hoặc click để chọn nhiều file' }}
      </p>

      <!-- Supported Formats -->
      <div v-if="!store.isUploading" class="drop-zone__formats">
        <span v-for="fmt in ['JPG', 'PNG', 'WEBP', 'BMP']" :key="fmt" class="format-badge">
          {{ fmt }}
        </span>
      </div>


    </div>



    <!-- Uploaded List (Unified Mode) -->
    <div v-else class="batch-list">
        <div v-for="(file, index) in store.batchFiles" :key="index" class="uploaded-preview__info mb-2">
             <div class="uploaded-preview__icon">📄</div>
             <div class="flex-1 overflow-hidden">
                <p class="uploaded-preview__name">{{ file.name }}</p>
                <p class="uploaded-preview__size">{{ (file.size / 1024).toFixed(1) }} KB</p>
             </div>
        </div>
        <button class="btn-add-more" @click="openFileDialog">
            + Thêm ảnh
        </button>
        <button class="btn-reset mt-2 w-full" @click="store.resetBatch()">
            Xóa tất cả
        </button>
    </div>

    <!-- Hidden Input (Always present) -->
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp,image/bmp"
      multiple
      style="display: none"
      @change="onFileSelected"
    />
  </div>
</template>

<style scoped>
.uploader-container {
  width: 100%;
}

/* === Drop Zone === */
.drop-zone {
  border: 2px dashed rgba(139, 92, 246, 0.3);
  border-radius: 20px;
  padding: 48px 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.4s ease;
  background: rgba(139, 92, 246, 0.03);
  position: relative;
  overflow: hidden;
}

.drop-zone::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, rgba(139, 92, 246, 0.08), transparent 70%);
  opacity: 0;
  transition: opacity 0.4s ease;
}

.drop-zone:hover,
.drop-zone--active {
  border-color: rgba(139, 92, 246, 0.6);
  background: rgba(139, 92, 246, 0.06);
}

.drop-zone:hover::before,
.drop-zone--active::before {
  opacity: 1;
}

.drop-zone--active {
  transform: scale(1.01);
}

.drop-zone__icon {
  color: #a78bfa;
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
}

.drop-zone__title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.2rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 6px;
}

.drop-zone__subtitle {
  font-size: 0.85rem;
  color: rgba(226, 232, 240, 0.5);
  margin-bottom: 20px;
}

.drop-zone__formats {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.format-badge {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* === Uploaded Preview === */
.uploaded-preview__info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(34, 211, 238, 0.06);
  border: 1px solid rgba(34, 211, 238, 0.15);
  border-radius: 14px;
}

.uploaded-preview__icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(34, 211, 238, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.uploaded-preview__name {
  font-weight: 600;
  font-size: 0.9rem;
  color: #e2e8f0;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uploaded-preview__size {
  font-size: 0.75rem;
  color: rgba(226, 232, 240, 0.5);
}

.btn-reset {
  margin-left: auto;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(226, 232, 240, 0.6);
  transition: all 0.3s ease;
}

.btn-reset:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.batch-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mb-2 { margin-bottom: 8px; }
.flex-1 { flex: 1; }
.overflow-hidden { overflow: hidden; }

.btn-add-more {
    width: 100%;
    padding: 8px;
    border: 1px dashed rgba(139, 92, 246, 0.4);
    border-radius: 12px;
    background: rgba(139, 92, 246, 0.05);
    color: #a78bfa;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
}
.btn-add-more:hover {
    background: rgba(139, 92, 246, 0.1);
}
.w-full { width: 100%; }
</style>
