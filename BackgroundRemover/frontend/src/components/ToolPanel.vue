<script setup>
/**
 * ToolPanel - Panel chọn phương pháp xóa nền và tùy chỉnh tham số.
 *
 * Tính năng:
 * - Chọn method: Auto, Color, Edge, GrabCut
 * - Sliders cho tolerance, threshold, iterations
 * - Color picker cho remove_color
 * - Section thay nền (replace background)
 * - Section tinh chỉnh (feather, expand, contract)
 * - Nút xử lý và download
 */
import { ref, computed } from 'vue'
import { useImageStore } from '../stores/imageStore'

const store = useImageStore()

/** Tab đang active: 'remove' | 'replace' | 'refine' */
const activeTab = ref('remove')

/** Danh sách phương pháp xóa nền */
const methods = [
  { id: 'auto', label: 'Tự động', icon: '✨', desc: 'AI chọn phương pháp tốt nhất' },
  { id: 'ai', label: 'AI (rembg)', icon: '🤖', desc: 'Chính xác nhất (Mới)' },
  { id: 'color', label: 'Theo màu', icon: '🎨', desc: 'Xóa nền đơn sắc' },
  { id: 'edge', label: 'Phát hiện cạnh', icon: '📐', desc: 'Dùng Edge Detection' },
  { id: 'grabcut', label: 'GrabCut', icon: '✂️', desc: 'Thuật toán OpenCV GrabCut' },
]

/** Màu nền preset cho replace */
const presetColors = [
  { label: 'Trắng', value: '255,255,255', hex: '#ffffff' },
  { label: 'Đen', value: '0,0,0', hex: '#000000' },
  { label: 'Xanh dương', value: '0,120,255', hex: '#0078ff' },
  { label: 'Xanh lá', value: '0,200,100', hex: '#00c864' },
  { label: 'Đỏ', value: '220,50,50', hex: '#dc3232' },
  { label: 'Tím', value: '139,92,246', hex: '#8b5cf6' },
]

/** Chuyển hex color thành RGB string */
function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `${r},${g},${b}`
}

/** Custom color picker value */
const customColor = ref('#ffffff')

/** Xử lý xóa nền */
async function handleRemove() {
  await store.removeBackground()
}

/** Xử lý thay nền */
async function handleReplace(colorStr) {
  await store.replaceBackgroundColor(colorStr)
}

/** Xử lý thay nền bằng custom color */
async function handleCustomReplace() {
  const rgb = hexToRgb(customColor.value)
  await store.replaceBackgroundColor(rgb)
}

async function handleRefine() {
  await store.refineMask()
}

async function handleUpscale() {
  if (store.isProcessing) return
  await store.upscaleImage()
}

/** Toggle Batch Mode */
function toggleBatchMode() {
  store.isBatchMode = !store.isBatchMode
  if (store.isBatchMode) {
     activeTab.value = 'remove'
     store.resetBatch()
  } else {
     store.resetAll()
  }
}

/** Toggle Color Picker */
function toggleColorPicker() {
  store.isPickingColor = !store.isPickingColor
}

/** Batch Edit Logic */
const isEditingBatchItem = ref(false)

function editBatchItem(item) {
    store.selectBatchItem(item)
    isEditingBatchItem.value = true
    activeTab.value = 'refine' // Mặc định vào tab refine để sửa
}

function exitBatchEdit() {
    isEditingBatchItem.value = false
    store.resetBatchItemSelection() // Cần thêm action này vào store để clear selection nếu muốn
}

</script>

<template>
  <div class="tool-panel glass-card">
    <!-- Panel Header -->
    <div class="panel-header">
      <h2 class="panel-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
        </svg>
        Công cụ
      </h2>
      
      <!-- Batch Toggle Removed (Unified Mode Always On) -->
    </div>

    <!-- Unified Status Panel -->
    <div v-if="true" class="batch-status-panel">
         <!-- <p class="batch-info">Chế độ danh sách</p> -->
         
         <div v-if="!store.hasBatchResults">
             <p class="batch-count">{{ store.batchFiles.length }} ảnh đã chọn</p>
             <div class="batch-actions mt-3">
                 <button 
                    class="btn-primary w-full" 
                    :disabled="store.batchFiles.length === 0 || store.isProcessing"
                    @click="store.processBatch()"
                 >
                    {{ store.isProcessing ? '⏳ Đang xử lý...' : '🚀 Xử lý tất cả' }}
                 </button>
             </div>
         </div>

         <!-- Batch Results List -->
         <div v-else class="batch-results">
             <div class="batch-list">
                 <div v-for="item in store.batchResults" :key="item.id" class="batch-item">
                     <img :src="`data:image/png;base64,${item.preview}`" class="batch-thumb" />
                     <div class="batch-details">
                         <span class="batch-name" :title="item.filename">{{ item.filename }}</span>
                         <button class="btn-xs" @click="editBatchItem(item)">✏️ Sửa</button>
                     </div>
                 </div>
             </div>
             
             <div class="batch-actions mt-3">
                 <button 
                    class="btn-primary w-full" 
                    @click="store.downloadBatchResults()"
                    :disabled="store.isProcessing"
                 >
                    📦 Tải tất cả (ZIP)
                 </button>
                 <button class="btn-text mt-2" @click="store.resetBatch">
                    🔄 Làm mới
                 </button>
             </div>
         </div>
    </div>

    <!-- Tabs (Settings/Refine) -->
    <div v-if="true" class="tabs">
      <div v-if="isEditingBatchItem" class="batch-edit-header">
          <button class="btn-back" @click="exitBatchEdit">⬅ Quay lại danh sách</button>
      </div>

      <button
        v-for="tab in [
          { id: 'remove', label: 'Xóa nền' },
          { id: 'replace', label: 'Thay nền' },
          { id: 'refine', label: 'Tinh chỉnh' },
          { id: 'upscale', label: 'Upscale AI (4x)' },
        ]"
        :key="tab.id"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Xóa nền (Settings) -->
    <div v-if="activeTab === 'remove'" class="tab-content">
      <!-- ... (giữ nguyên content tab remove) ... -->
      <!-- Chọn phương pháp -->
      <div class="section">
        <label class="section-label">Phương pháp</label>
        <div class="method-grid">
          <button
            v-for="m in methods"
            :key="m.id"
            class="method-card"
            :class="{ 'method-card--active': store.method === m.id }"
            @click="store.method = m.id"
          >
            <span class="method-card__icon">{{ m.icon }}</span>
            <span class="method-card__label">{{ m.label }}</span>
          </button>
        </div>
      </div>

      <!-- Tham số cho method AI -->
      <div v-if="store.method === 'ai'" class="section">
        <label class="section-label">🧠 Model AI</label>
        <select v-model="store.aiModel" class="input-select">
          <option value="u2net">U²-Net (Cân bằng)</option>
          <option value="isnet-general-use">ISNet General (Chính xác cao)</option>
          <option value="isnet-anime">ISNet Anime (Clipart/Cartoon) ⭐</option>
          <option value="birefnet-general">BiRefNet General (SOTA - Rất mạnh) 🌟</option>
          <option value="birefnet-general-lite">BiRefNet Lite (Nhanh & Tốt)</option>
          <option value="birefnet-portrait">BiRefNet Portrait (Chân dung)</option>
          <option value="bria-rmbg">BRIA RMBG 1.4 (Cần license) ⚠️</option>
          <option value="u2net_human_seg">U²-Net Human (Ảnh người)</option>
          <option value="u2netp">U²-Net Lite (Nhanh)</option>
          <option value="silueta">Silueta (Nhẹ nhất)</option>
        </select>

        <label class="section-label mt-3">🌫️ Loại bỏ bóng: {{ store.alphaThreshold }}</label>
        <p class="param-hint">0 = tắt, 30-100 = bóng nhẹ, 128+ = bóng đậm</p>
        <input
          v-model.number="store.alphaThreshold"
          type="range"
          min="0"
          max="200"
          step="5"
        />

        <label class="section-label mt-3 flex-row">
          <input type="checkbox" v-model="store.alphaMatting" class="checkbox" />
          ✨ Alpha Matting (viền mượt - tóc, lông)
        </label>
      </div>
      <div v-if="store.method === 'color'" class="section">
        <label class="section-label">Màu nền cần xóa (R,G,B)</label>
        <input 
          v-model="store.removeColor"
          type="text" 
          class="input-text"
          placeholder="255,255,255"
        />
        <button 
            class="btn-icon-text mt-2" 
            :class="{ 'btn-active': store.isPickingColor }"
            @click="toggleColorPicker"
        >
            🖌️ {{ store.isPickingColor ? 'Đang chọn...' : 'Hút màu từ ảnh' }}
        </button>

        <label class="section-label mt-3">Tolerance: {{ store.tolerance }}</label>
        <input
          v-model.number="store.tolerance"
          type="range"
          min="0"
          max="100"
          step="1"
        />
      </div>

      <!-- Tham số cho method Edge -->
      <div v-if="store.method === 'edge'" class="section">
        <label class="section-label">Threshold: {{ store.threshold }}</label>
        <input
          v-model.number="store.threshold"
          type="range"
          min="10"
          max="200"
          step="5"
        />
      </div>

      <!-- Tham số cho method GrabCut -->
      <div v-if="store.method === 'grabcut'" class="section">
        <label class="section-label">Iterations: {{ store.iterations }}</label>
        <input
          v-model.number="store.iterations"
          type="range"
          min="1"
          max="20"
          step="1"
        />
      </div>

      <!-- Nút xử lý lại (Re-process) - Chỉ hiện khi đang Edit Batch Item -->
      <button
        v-if="isEditingBatchItem"
        class="btn-primary w-full mt-4"
        :disabled="store.isProcessing"
        @click="handleRemove"
      >
        <span>{{ store.isProcessing ? '⏳ Đang xử lý...' : '♻️ Xóa nền lại với setting mới' }}</span>
      </button>
    </div>

    <!-- Tab: Thay nền -->
    <div v-if="activeTab === 'replace' && (!store.isBatchMode || isEditingBatchItem)" class="tab-content">
      <div class="section">
        <label class="section-label">Chọn màu nền mới</label>
        <div class="color-grid">
          <button
            v-for="c in presetColors"
            :key="c.value"
            class="color-swatch"
            :style="{ background: c.hex }"
            :title="c.label"
            @click="handleReplace(c.value)"
          />
        </div>
      </div>

      <div class="section">
        <label class="section-label">Hoặc chọn màu tùy chỉnh</label>
        <div class="custom-color-row">
          <input
            v-model="customColor"
            type="color"
            class="color-input"
          />
          <button
            class="btn-secondary flex-1"
            :disabled="!store.hasResult || store.isBusy"
            @click="handleCustomReplace"
          >
            Áp dụng
          </button>
        </div>
      </div>

      <p v-if="!store.hasResult" class="hint-text">
        ⚠️ Bạn cần xóa nền trước khi thay nền mới
      </p>
    </div>

    <!-- Tab: Tinh chỉnh -->
    <div v-if="activeTab === 'refine' && (!store.isBatchMode || isEditingBatchItem)" class="tab-content">
      
      <!-- Brush Tool Section -->
      <div class="section border-b pb-4 mb-4" v-if="store.hasResult">
          <label class="section-label">Thủ công (Brush)</label>
          <button 
            class="btn-icon-text" 
            :class="{ 'btn-active': store.isBrushActive }"
            @click="store.isBrushActive = !store.isBrushActive"
          >
            🖌️ {{ store.isBrushActive ? 'Đang bật Brush' : 'Bật công cụ vẽ' }}
          </button>
          
          <div v-if="store.isBrushActive" class="brush-controls mt-3">
              <div class="flex gap-2 mb-2">
                  <button 
                    class="btn-xs flex-1"
                    :class="{ 'btn-primary': store.brushType === 'erase', 'btn-secondary': store.brushType !== 'erase' }"
                    @click="store.brushType = 'erase'"
                  >🧽 Xóa</button>
                  <button 
                    class="btn-xs flex-1"
                    :class="{ 'btn-primary': store.brushType === 'restore', 'btn-secondary': store.brushType !== 'restore' }"
                    @click="store.brushType = 'restore'"
                  >🎨 Khôi phục</button>
              </div>
              
              <label class="text-xs text-gray-400">Kích thước: {{ store.brushSize }}px</label>
              <input 
                  v-model.number="store.brushSize"
                  type="range" min="1" max="100" class="w-full"
              />
              
              <p class="text-xs text-yellow-500 mt-2">
                  * Vẽ lên ảnh để sửa. Nhấn nút "Save" trên ảnh hoặc "Áp dụng" dưới đây để lưu.
              </p>
          </div>
      </div>

      <div class="section">
        <label class="section-label">Feather (Làm mượt viền): {{ store.feather }}</label>
        <input
          v-model.number="store.feather"
          type="range"
          min="0"
          max="10"
          step="1"
        />
      </div>

      <div class="section">
        <label class="section-label">Expand (Mở rộng mask): {{ store.expand }}</label>
        <input
          v-model.number="store.expand"
          type="range"
          min="0"
          max="10"
          step="1"
        />
      </div>

      <div class="section">
        <label class="section-label">Contract (Thu hẹp mask): {{ store.contract }}</label>
        <input
          v-model.number="store.contract"
          type="range"
          min="0"
          max="10"
          step="1"
        />
      </div>

      <button
        class="btn-primary w-full mt-4"
        :disabled="!store.hasResult || store.isBusy"
        @click="handleRefine"
      >
        <span>{{ store.isProcessing ? '⏳ Đang xử lý...' : '✨ Áp dụng tinh chỉnh' }}</span>
      </button>

      <p v-if="!store.hasResult" class="hint-text">
        ⚠️ Bạn cần xóa nền trước khi tinh chỉnh
      </p>
    </div>

    <!-- Tab: Upscale -->
    <div v-if="activeTab === 'upscale' && (!store.isBatchMode || isEditingBatchItem)" class="tab-content">
      <div class="section">
        <label class="section-label">🚀 AI Super Resolution</label>
        <div class="bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
          <p class="text-sm text-gray-300 mb-2">
             Tự động phóng to ảnh gấp <strong>4 lần (4x)</strong> bằng mô hình AI chuyên dụng.
          </p>
          <ul class="text-xs text-gray-400 space-y-1 list-disc pl-4">
             <li>Khôi phục chi tiết cho ảnh vỡ/mờ.</li>
             <li>Làm nét viền cho clipart & anime.</li>
             <li>⚠️ Tốn tài nguyên: 10-30s/ảnh.</li>
          </ul>
        </div>
      </div>

      <button
        class="btn-primary w-full mt-4 bg-gradient-to-r from-pink-500 to-violet-600 hover:from-pink-600 hover:to-violet-700 border-none shadow-lg shadow-purple-900/20"
        :disabled="!store.hasImage || store.isBusy"
        @click="handleUpscale"
      >
        <span>{{ store.isProcessing ? '⏳ Đang xử lý...' : '✨ Nâng cấp 4x ngay' }}</span>
      </button>
      
      <p v-if="!store.hasImage" class="hint-text">
        ⚠️ Bạn cần upload ảnh trước
      </p>
    </div>

    <!-- Download Section -->
    <div v-if="store.hasResult" class="download-section">
      <label class="section-label">Tải kết quả</label>
      <div class="download-btns">
        <button class="btn-secondary" @click="store.downloadResult('png')">
          📥 PNG
        </button>
        <button class="btn-secondary" @click="store.downloadResult('webp')">
          📥 WEBP
        </button>
        <button class="btn-secondary" @click="store.downloadResult('jpeg')">
          📥 JPEG
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tool-panel {
  padding: 20px;
  height: fit-content;
}

/* === Header === */
.panel-header {
  margin-bottom: 18px;
}

.panel-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e2e8f0;
}

/* === Tabs === */
.tabs {
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 20px;
}

.tab-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: rgba(226, 232, 240, 0.5);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn--active {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.tab-btn:hover:not(.tab-btn--active) {
  color: #e2e8f0;
}

/* === Tab Content === */
.tab-content {
  animation: stagger-in 0.3s ease-out;
}

/* === Sections === */
.section {
  margin-bottom: 16px;
}

.section-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 500;
  color: rgba(226, 232, 240, 0.6);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.mt-3 {
  margin-top: 12px;
}

/* === Method Grid === */
.method-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.method-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(226, 232, 240, 0.7);
}

.method-card:hover {
  border-color: rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.05);
}

.method-card--active {
  border-color: rgba(139, 92, 246, 0.5);
  background: rgba(139, 92, 246, 0.1);
  color: #e2e8f0;
  box-shadow: 0 0 15px rgba(139, 92, 246, 0.15);
}

.method-card__icon {
  font-size: 1.4rem;
}

.method-card__label {
  font-size: 0.75rem;
  font-weight: 500;
}

/* === Input === */
.input-text {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #e2e8f0;
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.3s ease;
}

.input-text:focus {
  border-color: rgba(139, 92, 246, 0.5);
}

.input-select {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #e2e8f0;
  font-size: 0.85rem;
  outline: none;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23e2e8f0' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  transition: border-color 0.3s ease;
}
.input-select:focus {
  border-color: rgba(139, 92, 246, 0.5);
}
.input-select option {
  background: #1e1b4b;
  color: #e2e8f0;
}

.param-hint {
  font-size: 0.7rem;
  color: rgba(226, 232, 240, 0.35);
  margin: 2px 0 6px;
}

.flex-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox {
  width: 16px;
  height: 16px;
  accent-color: #8b5cf6;
  cursor: pointer;
}

/* === Color Grid === */
.color-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-swatch {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.color-swatch:hover {
  transform: scale(1.15);
  border-color: rgba(255, 255, 255, 0.4);
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.15);
}

/* === Custom Color === */
.custom-color-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.color-input {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  background: none;
  padding: 0;
}

.color-input::-webkit-color-swatch-wrapper {
  padding: 2px;
}

.color-input::-webkit-color-swatch {
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

/* === Download Section === */
.download-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.download-btns {
  display: flex;
  gap: 8px;
}

.download-btns .btn-secondary {
  flex: 1;
  text-align: center;
  font-size: 0.8rem;
  padding: 10px 8px;
}

/* === Utils === */
.w-full {
  width: 100%;
}

.flex-1 {
  flex: 1;
}

.hint-text {
  font-size: 0.78rem;
  color: rgba(251, 191, 36, 0.7);
  text-align: center;
  margin-top: 12px;
}

@keyframes stagger-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* === Batch UI === */
.batch-toggle {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.3);
    color: #a78bfa;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    margin-left: auto;
    transition: all 0.3s ease;
}

.batch-toggle--active {
    background: #a78bfa;
    color: white;
    box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
}

.batch-status-panel {
    background: rgba(139, 92, 246, 0.05);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
    border: 1px dashed rgba(139, 92, 246, 0.3);
    text-align: center;
}

.batch-info {
    font-size: 0.85rem;
    color: #a78bfa;
    font-weight: 500;
}

.batch-count {
    font-size: 1.2rem;
    font-weight: bold;
    color: #e2e8f0;
    margin: 4px 0;
}

.btn-icon-text {
    width: 100%;
    padding: 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e2e8f0;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.2s;
}

.btn-icon-text:hover {
    background: rgba(255,255,255,0.1);
}

.btn-active {
    background: rgba(34, 213, 238, 0.2) !important;
    border-color: #22d3ee;
    color: #22d3ee;
}

/* === Interactive States === */
.btn-primary, .btn-secondary, .btn-icon-text, .method-card, .tab-btn {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-primary:active, 
.btn-secondary:active, 
.btn-icon-text:active, 
.method-card:active,
.tab-btn:active {
    transform: scale(0.96);
}

.btn-primary:hover {
    filter: brightness(1.1);
    box-shadow: 0 0 15px rgba(34, 211, 238, 0.4);
}

.method-card:hover {
    background: rgba(255, 255, 255, 0.08);
}

.method-card--active {
    background: rgba(34, 211, 238, 0.15);
    border-color: #22d3ee;
    color: #22d3ee;
    box-shadow: 0 0 15px rgba(34, 211, 238, 0.15);
}
</style>