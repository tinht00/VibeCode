/**
 * Pinia Store - Quản lý trạng thái toàn cục cho ứng dụng Background Remover.
 *
 * Quản lý:
 * - Ảnh gốc và ảnh kết quả (dạng base64)
 * - Trạng thái xử lý (loading, error)
 * - Cài đặt phương pháp xóa nền và tham số
 * - Giao tiếp với Backend API
 */
import { defineStore } from 'pinia'
import axios from 'axios'

/** URL cơ sở cho API backend */
const API_BASE = '/api'

export const useImageStore = defineStore('image', {
    state: () => ({
        // === Thông tin ảnh ===
        /** ID ảnh trên server, dùng để tham chiếu trong các request */
        fileId: null,
        /** Tên file gốc */
        fileName: '',
        /** Kích thước ảnh gốc */
        imageWidth: 0,
        imageHeight: 0,

        // === Unified Processing State ===
        isBatchMode: true, // Luôn bật chế độ danh sách (Unified Mode)
        batchFiles: [], // Danh sách File objects upload lên
        batchResults: [], // Danh sách kết quả trả về từ server {id, filename, status, preview...}
        isPickingColor: false,

        // === Ảnh dạng base64 ===
        /** Ảnh gốc preview */
        originalPreview: null,
        /** Ảnh kết quả sau xử lý */
        resultPreview: null,

        // === Trạng thái ===
        /** Đang upload ảnh */
        isUploading: false,
        /** Đang xử lý (xóa nền, thay nền, tinh chỉnh) */
        isProcessing: false,
        /** Thông báo lỗi */
        errorMessage: '',
        /** Thông báo thành công */
        successMessage: '',

        // === Cài đặt phương pháp ===
        /** Phương pháp xóa nền: auto | ai | color | edge | grabcut */
        method: 'auto',
        /** Màu cần xóa cho method "color" (R,G,B) */
        removeColor: '255,255,255',
        /** Ngưỡng tolerance cho method "color" */
        tolerance: 30,
        /** Ngưỡng threshold cho method "edge" */
        threshold: 50,
        /** Số lần lặp cho method "grabcut" */
        iterations: 5,

        // === Cài đặt AI Model ===
        /** Model AI: u2net | u2netp | u2net_human_seg | isnet-general-use | isnet-anime | silueta */
        aiModel: 'isnet-anime',
        /** Ngưỡng alpha để loại bỏ bóng mờ (0=tắt, 30-100 cho bóng nhẹ, 128+ cho bóng đậm) */
        alphaThreshold: 130,
        /** Bật alpha matting cho viền mượt hơn (tóc, lông) */
        alphaMatting: false,

        // === Cài đặt thay nền ===
        /** Màu nền thay thế (R,G,B) hoặc null nếu không thay */
        replaceColor: '',

        // === Cài đặt tinh chỉnh ===
        /** Bán kính feather */
        feather: 0,
        /** Số pixel mở rộng mask */
        expand: 0,
        /** Số pixel thu hẹp mask */
        contract: 0,

        // === Brush Tool State ===
        isBrushActive: false,
        brushSize: 20,
        brushType: 'erase', // 'erase' | 'restore'
    }),

    getters: {
        /** Đã upload ảnh chưa */
        hasImage: (state) => state.fileId !== null,
        /** Đã có kết quả chưa */
        hasResult: (state) => state.resultPreview !== null,
        /** Đang bận (upload hoặc xử lý) */
        isBusy: (state) => state.isUploading || state.isProcessing,
        /** Có kết quả batch để hiển thị không */
        hasBatchResults: (state) => state.batchResults.length > 0,
    },

    actions: {
        // ... (giữ nguyên uploadImage, removeBackground, replaceBackgroundColor, refineMask, downloadResult)

        /**
         * Upload ảnh lên server.
         *
         * Args:
         *   file: File object từ input hoặc drag-drop
         */
        async uploadImage(file) {
            // Unified: Upload chỉ thêm vào danh sách, không gửi request ngay (trừ khi cần preview thumbnail từ server, nhưng ở đây ta dùng FileReader preview client-side hoặc đợi batch logic)
            // Tuy nhiên, logic cũ là upload ngay để lấy file_id. 
            // Để gộp batch/single: Ta sẽ xử lý như Batch: thêm vào list batchFiles để chờ xử lý.
            // Nếu người dùng muốn "upload ngay" kiểu cũ, ta vẫn có thể giữ logic cũ nhưng ẩn đi.
            // Tạm thời: Logic uploadImage sẽ đổi thành "Add to Batch List" và validation.

            // Client-side validation
            const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']
            if (!validTypes.includes(file.type)) {
                this.errorMessage = 'Định dạng không hỗ trợ'
                return
            }
            if (file.size > 20 * 1024 * 1024) {
                this.errorMessage = 'File quá lớn (>20MB)'
                return
            }

            // Thêm vào danh sách chờ xử lý (chưa có ID từ server)
            this.batchFiles.push(file)
            this.successMessage = `Đã thêm ${file.name}`
        },

        async removeBackground() {
            if (!this.fileId) return

            this.isProcessing = true
            this.errorMessage = ''

            try {
                const formData = new FormData()
                formData.append('file_id', this.fileId)
                formData.append('method', this.method)
                formData.append('tolerance', this.tolerance)
                formData.append('threshold', this.threshold)
                formData.append('iterations', this.iterations)

                // Thêm tham số AI model nếu method là 'ai'
                if (this.method === 'ai') {
                    formData.append('ai_model', this.aiModel)
                    formData.append('alpha_threshold', this.alphaThreshold)
                    formData.append('alpha_matting', this.alphaMatting)
                }

                if (this.method === 'color' && this.removeColor) {
                    formData.append('color', this.removeColor)
                }

                const response = await axios.post(`${API_BASE}/remove-background`, formData)
                const resData = response.data.data || response.data
                this.resultPreview = `data:image/png;base64,${resData.result}`
                this.successMessage = `Xóa nền thành công (${resData.method_used})`

                // Nếu đang edit item trong batch, update lại preview trong list
                if (this.isBatchMode) {
                    const index = this.batchResults.findIndex(item => item.id === this.fileId)
                    if (index !== -1) {
                        this.batchResults[index].preview = resData.result
                    }
                }

            } catch (error) {
                this.errorMessage = error.response?.data?.error?.message || error.response?.data?.detail || 'Lỗi xóa nền'
            } finally {
                this.isProcessing = false
            }
        },

        async replaceBackgroundColor(colorStr) {
            if (!this.fileId) return
            this.isProcessing = true
            this.errorMessage = ''
            try {
                const formData = new FormData()
                formData.append('file_id', this.fileId)
                formData.append('color', colorStr)
                const response = await axios.post(`${API_BASE}/replace-background`, formData)
                const resData = response.data.data || response.data
                this.resultPreview = `data:image/png;base64,${resData.result}`
                this.successMessage = 'Thay nền thành công!'

                if (this.isBatchMode) {
                    const index = this.batchResults.findIndex(item => item.id === this.fileId)
                    if (index !== -1) {
                        this.batchResults[index].preview = resData.result
                    }
                }
            } catch (error) {
                this.errorMessage = error.response?.data?.error?.message || error.response?.data?.detail || 'Lỗi thay nền'
            } finally {
                this.isProcessing = false
            }
        },

        async refineMask() {
            if (!this.fileId) return
            this.isProcessing = true
            this.errorMessage = ''
            try {
                const formData = new FormData()
                formData.append('file_id', this.fileId)
                formData.append('feather', this.feather)
                formData.append('expand', this.expand)
                formData.append('contract', this.contract)

                if (this.isBrushActive) {
                    // Nếu đang active brush, refresh mask từ server để đồng bộ
                    // (Thực tế brush làm thay đổi mask trên server rồi, nên refine sẽ lấy mask mới nhất)
                }
                const response = await axios.post(`${API_BASE}/refine`, formData)
                const resData = response.data.data || response.data
                this.resultPreview = `data:image/png;base64,${resData.result}`
                this.successMessage = 'Tinh chỉnh thành công!'

                if (this.isBatchMode) {
                    const index = this.batchResults.findIndex(item => item.id === this.fileId)
                    if (index !== -1) {
                        this.batchResults[index].preview = resData.result
                    }
                }
            } catch (error) {
                this.errorMessage = error.response?.data?.error?.message || error.response?.data?.detail || 'Lỗi tinh chỉnh'
            } finally {
                this.isProcessing = false
            }
        },

        async upscaleImage() {
            if (!this.fileId) return
            this.isProcessing = true
            this.errorMessage = ''
            try {
                const formData = new FormData()
                formData.append('file_id', this.fileId)

                // Mặc định scale 4x (backend config)

                const response = await axios.post(`${API_BASE}/upscale`, formData)
                const resData = response.data.data

                this.resultPreview = `data:image/png;base64,${resData.image}`
                this.successMessage = `Đã nâng cấp ảnh lên 4x (${resData.width}x${resData.height})! 🚀`

                if (this.isBatchMode) {
                    const index = this.batchResults.findIndex(item => item.id === this.fileId)
                    if (index !== -1) {
                        this.batchResults[index].preview = resData.image
                    }
                }
            } catch (error) {
                this.errorMessage = error.response?.data?.message || 'Lỗi khi nâng cấp ảnh'
                console.error('Upscale error:', error)
            } finally {
                this.isProcessing = false
            }
        },

        async downloadResult(format = 'png') {
            if (!this.fileId) return
            try {
                const response = await axios.get(
                    `${API_BASE}/download/${this.fileId}?format=${format}`,
                    { responseType: 'blob' }
                )
                const url = window.URL.createObjectURL(response.data)
                const link = document.createElement('a')
                link.href = url
                link.download = `${this.fileName.split('.')[0] || 'result'}_nobg.${format}`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                window.URL.revokeObjectURL(url)
            } catch (error) {
                this.errorMessage = 'Lỗi tải file'
            }
        },

        /**
         * Xử lý hàng loạt (Batch Processing).
         */
        async processBatch() {
            if (this.batchFiles.length === 0) return

            this.isProcessing = true
            this.errorMessage = ''
            this.batchResults = [] // Reset results

            const CHUNK_SIZE = 5
            const totalFiles = this.batchFiles.length
            const totalChunks = Math.ceil(totalFiles / CHUNK_SIZE)

            try {
                for (let i = 0; i < totalChunks; i++) {
                    const start = i * CHUNK_SIZE
                    const end = Math.min(start + CHUNK_SIZE, totalFiles)
                    const chunk = this.batchFiles.slice(start, end)

                    // Update progress message
                    this.successMessage = `Đang xử lý gói ${i + 1}/${totalChunks} (${chunk.length} ảnh)...`

                    const formData = new FormData()
                    chunk.forEach(file => {
                        formData.append('files', file)
                    })

                    formData.append('method', this.method)
                    formData.append('tolerance', this.tolerance)
                    formData.append('threshold', this.threshold)
                    formData.append('iterations', this.iterations)
                    formData.append('feather', this.feather)

                    // Unified: Luôn gửi tham số AI
                    formData.append('ai_model', this.aiModel)
                    formData.append('alpha_threshold', this.alphaThreshold)
                    formData.append('alpha_matting', this.alphaMatting)

                    if (this.method === 'color' && this.removeColor) {
                        formData.append('color', this.removeColor)
                    }

                    // Gọi API mới: /api/batch/process
                    const response = await axios.post(`${API_BASE}/batch/process`, formData)
                    const data = response.data.data || response.data

                    // Thêm kết quả của chunk này vào danh sách chung
                    this.batchResults = [...this.batchResults, ...data]
                }

                this.successMessage = `Đã xử lý xong ${this.batchResults.length} ảnh. Hãy kiểm tra kết quả!`
                this.batchFiles = []

            } catch (error) {
                this.errorMessage = 'Lỗi xử lý hàng loạt: ' + (error.response?.data?.detail || error.message)
                console.error(error)
            } finally {
                this.isProcessing = false
            }
        },

        /**
         * Tải xuống toàn bộ (ZIP).
         */
        async downloadBatchResults() {
            if (this.batchResults.length === 0) return

            this.isProcessing = true
            try {
                const formData = new FormData()
                this.batchResults.forEach(item => {
                    if (item.id && item.status === 'success') {
                        formData.append('file_ids', item.id)
                    }
                })

                const response = await axios.post(`${API_BASE}/batch/download`, formData, {
                    responseType: 'blob',
                    timeout: 600000
                })

                const url = window.URL.createObjectURL(new Blob([response.data]))
                const link = document.createElement('a')
                link.href = url
                link.setAttribute('download', `batch_result_${Date.now()}.zip`)
                document.body.appendChild(link)
                link.click()
                link.remove()
                window.URL.revokeObjectURL(url)

            } catch (error) {
                this.errorMessage = 'Lỗi tải file ZIP.'
                console.error(error)
            } finally {
                this.isProcessing = false
            }
        },

        /**
         * Chọn 1 ảnh từ batch để chỉnh sửa (chuyển vào main view).
         */
        selectBatchItem(item) {
            if (!item || !item.id) return

            this.fileId = item.id
            this.fileName = item.filename
            this.imageWidth = item.width
            this.imageHeight = item.height

            // Set previews
            this.resultPreview = `data:image/png;base64,${item.preview}`
            if (item.original_preview) {
                this.originalPreview = `data:image/png;base64,${item.original_preview}`
            }

            // Reset các tham số edit tạm thời để không ảnh hưởng global settings
            // hoặc giữ nguyên tùy logic. Ở đây giữ nguyên.
        },

        async getMask() {
            if (!this.fileId) return null
            try {
                const response = await axios.get(`${API_BASE}/mask/${this.fileId}`, {
                    responseType: 'blob'
                })
                return response.data
            } catch (error) {
                console.error("Error fetching mask:", error)
                return null
            }
        },

        /**
         * Cập nhật mask từ canvas (Brush tool).
         */
        async updateMask(blob) {
            if (!this.fileId) return

            this.isProcessing = true
            try {
                const formData = new FormData()
                formData.append('file_id', this.fileId)
                formData.append('mask_file', blob, 'mask.png')

                const response = await axios.post(`${API_BASE}/mask/update`, formData)
                const resData = response.data.data || response.data

                this.resultPreview = `data:image/png;base64,${resData.result}`
                this.successMessage = 'Update Mask thành công!'

                // Update batch result list if in batch mode
                if (this.isBatchMode) {
                    const index = this.batchResults.findIndex(item => item.id === this.fileId)
                    if (index !== -1) {
                        this.batchResults[index].preview = resData.result
                    }
                }

            } catch (error) {
                this.errorMessage = 'Lỗi cập nhật mask.'
                console.error(error)
            } finally {
                this.isProcessing = false
            }
        },


        resetBatch() {
            this.batchFiles = []
            this.batchResults = []
            // this.errorMessage = ''
        },

        resetBatchItemSelection() {
            this.fileId = null
            this.fileName = ''
            this.imageWidth = 0
            this.imageHeight = 0
            this.originalPreview = null
            this.resultPreview = null
            this.errorMessage = ''
            this.successMessage = ''
            // Reset brush state
            this.isBrushActive = false
        },

        resetAll() {
            if (this.fileId) {
                // Xóa session trên server
                try {
                    axios.delete(`${API_BASE}/session/${this.fileId}`).catch(() => { })
                } catch { }
            }

            this.fileId = null
            this.fileName = ''
            this.imageWidth = 0
            this.imageHeight = 0
            this.originalPreview = null
            this.resultPreview = null
            this.errorMessage = ''
            this.successMessage = ''
            this.method = 'auto'
            this.removeColor = '255,255,255'
            this.feather = 0
            this.expand = 0
            this.contract = 0

            this.isBrushActive = false
            this.brushSize = 20
            this.brushType = 'erase'

            this.batchFiles = []
            this.isBatchMode = false // Exit batch mode
            this.batchResults = []
            this.isPickingColor = false
        }
    }
})
