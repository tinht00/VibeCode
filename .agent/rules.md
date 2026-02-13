# ANTIGRAVITY PROJECT: PROTOCOL (QUY CHUẨN TOÀN CỤC)

Tài liệu này là sự kết hợp giữa các quy tắc kỹ thuật bắt buộc (Rules) và quy trình làm việc (Workflow) cho dự án Antigravity. Đây là kim chỉ nam duy nhất để đảm bảo tính đồng bộ và hiệu suất cao.

## PHẦN 1: GLOBAL RULES (QUY TẮC KỸ THUẬT)

* **Quan trọng**: Luôn trả lời tôi bằng tiếng Việt và khi sinh ra Plan thì cũng là tiếng Việt.

Các quy chuẩn kỹ thuật cứng (Hard Rules) mà mọi lập trình viên và AI phải tuân thủ.

### 1. Triết lý cốt lõi (Core Philosophy)

**"Strict & Explicit" (Chặt chẽ & Tường minh)**

*   Mọi dòng code phải rõ ràng về mục đích.
*   Ưu tiên code dễ đọc (Readability) hơn code ngắn gọn nhưng khó hiểu (Cleverness).
*   Không được giấu lỗi (Swallow errors); lỗi phải được xử lý hoặc báo cáo rõ ràng.

### 2. Quy tắc theo công nghệ (Tech Stack Rules)

#### 🟢 Vue 3 + Vite (Frontend Web)
*   **Architecture (Kiến trúc)**: Bắt buộc dùng Composition API với `<script setup>`. **CẤM** dùng Options API.
*   **State Management (Quản lý trạng thái)**: Bắt buộc dùng Pinia. **CẤM** dùng Vuex.
*   **Performance (Hiệu năng)**: Áp dụng Lazy Loading (Tải lười/Tải khi cần) cho toàn bộ Route (đường dẫn) và Component lớn.
*   **Styling**: Sử dụng TailwindCSS hoặc Scoped CSS. Tránh dùng Global CSS (CSS toàn cục) để ngăn chặn xung đột giao diện.

#### 🔵 Golang (Backend/Microservices)
*   **Error Handling (Xử lý lỗi)**: Phải kiểm tra lỗi ngay lập tức: `if err != nil`. Tuyệt đối không dùng `_` để bỏ qua lỗi quan trọng.
*   **Concurrency (Đồng thời)**: Sử dụng Goroutines và Channels. Bắt buộc kiểm tra Race Condition (Điều kiện tranh đua) bằng cờ `-race` khi test.
*   **Design Pattern (Mẫu thiết kế)**: Tuân thủ Clean Architecture (Handler -> Service -> Repository).

#### 🟡 Python (AI/Data Processing)
*   **Typing (Định kiểu)**: Bắt buộc sử dụng Type Hints (Gợi ý kiểu) cho mọi hàm.
    *   Ví dụ đúng: `def process(data: dict) -> list:`
*   **Environment (Môi trường)**: Code phải chạy trong Virtual Environment (Môi trường ảo - venv/conda).
*   **Documentation**: Docstring (Chuỗi tài liệu) phải theo chuẩn Google hoặc NumPy.

#### 🟠 Python FastAPI (Backend API)
*   **Pydantic Models**: Bắt buộc dùng `BaseModel` cho request/response schema. Không dùng raw dict.
*   **Dependency Injection**: Sử dụng `Depends()` cho database sessions, auth, và shared services.
*   **Router Organization**: Tách endpoints theo feature/domain vào các `APIRouter` riêng.
*   **Error Handling**: Dùng `HTTPException` với status code chính xác và `detail` rõ ràng (tiếng Việt).
*   **Async/Await**: Ưu tiên `async def` cho I/O-bound handlers. Dùng `def` cho CPU-bound.
*   **CORS**: Cấu hình CORS middleware với origins cụ thể trong production. Chỉ dùng `*` khi dev.

#### 🔴 C++ (Core Performance)
*   **Standard (Tiêu chuẩn)**: Sử dụng C++17 hoặc C++20.
*   **Memory Safety (An toàn bộ nhớ)**:
    *   **CẤM** dùng `new`/`delete` thủ công (Raw Pointers).
    *   **BẮT BUỘC** dùng Smart Pointers (`std::unique_ptr`, `std::shared_ptr`) để tự động quản lý bộ nhớ, tránh Memory Leak (Rò rỉ bộ nhớ).
*   **Resource Management**: Tuân thủ nguyên tắc RAII (Resource Acquisition Is Initialization).

#### 🟣 Flutter (Mobile App)
*   **Performance**: Ưu tiên dùng `const` constructor cho các Widget tĩnh để tối ưu việc vẽ lại (Re-build).
*   **State Management**: Tách biệt hoàn toàn UI (Giao diện) và Logic. Sử dụng BLoC hoặc Riverpod.
*   **Async Safety**: Xử lý các tác vụ bất đồng bộ (Async tasks) cẩn thận, không được chặn (block) luồng UI chính.

#### ⚛️ ReactJS (Frontend Web - Alternative)
*   **Architecture**: Bắt buộc dùng Functional Components và Hooks. **TRÁNH** Class Components.
*   **Performance**: Sử dụng `useMemo` và `useCallback` hợp lý để tránh re-render không cần thiết.
*   **State Management**: Sử dụng Context API hoặc Redux Toolkit (nếu cần thiết cho app lớn). Typings với TypeScript là bắt buộc.

### 3. Quy ước cấu trúc dự án (Project Structure Policy)

*   **Bắt buộc**: Mỗi dự án mới phải có thư mục `.agent/` với ít nhất:
    *   `rules.md` — Quy tắc riêng cho dự án (tech stack, cấu trúc, conventions)
    *   `workflows/dev.md` — Hướng dẫn chạy development
*   **Tùy chọn**: Thêm `workflows/deploy.md`, `skills/` nếu dự án cần.
*   **Template tối thiểu** cho `rules.md` dự án:
    1.  Tổng quan dự án (mô tả, tech stack)
    2.  Cấu trúc thư mục và vai trò từng file
    3.  Quy tắc coding cụ thể
    4.  Hướng dẫn dev (ports, commands)

### 4. Quy ước Skill Format (Skill Structure Policy)

*   **CẤM** tạo skill dưới dạng file `.md` đơn lẻ (vd: `skill_name.md`).
*   **BẮT BUỘC** tạo skill theo cấu trúc thư mục:
    ```
    skills/
    └── skill-name/
        ├── SKILL.md          # File chính (bắt buộc, YAML frontmatter)
        ├── scripts/          # Scripts hỗ trợ (tùy chọn)
        └── examples/         # Ví dụ tham khảo (tùy chọn)
    ```
*   **SKILL.md** phải có YAML frontmatter với `name` và `description`.
*   `description` phải mô tả rõ **khi nào** AI nên sử dụng skill này.

## PHẦN 2: WORKFLOW & AI PROTOCOL (QUY TRÌNH LÀM VIỆC)

Áp dụng tư duy "đo lường kỹ, làm một lần" (Zero-G) để giảm thiểu nợ kỹ thuật.

### 1. The "Zero-G" Workflow (Quy trình phát triển)

#### Giai đoạn 1: Phân tích & Mô phỏng (Analysis - 30% Thời gian)
Yêu cầu bắt buộc trước khi viết code:
*   **I/O Definition (Định nghĩa Đầu vào/Đầu ra)**: Input là gì? Output mong đợi là gì? (Cấu trúc JSON, Trạng thái UI...).
*   **Location Strategy (Chiến lược vị trí)**: Logic này thuộc về đâu? (Frontend hiển thị, Backend xử lý, hay AI phân tích?).
*   **Edge Cases (Trường hợp biên)**: Dự đoán các tình huống lỗi: Mất mạng, dữ liệu rỗng, tràn bộ nhớ.
*   **Dependencies (Sự phụ thuộc)**: Module này cần những gì để chạy?

#### Giai đoạn 2: Implementation (Triển khai - 40% Thời gian)
Nguyên tắc: Atomic Commits (Cam kết nhỏ).
*   **Interface First**: Viết Interface (Giao diện/Khuôn mẫu) trước khi viết chi tiết.
*   **Core Logic & Test**: Viết Unit Test cho logic cốt lõi.
*   **Coding**: Viết code thực thi.
*   **Instant Refactor**: Nếu hàm dài quá 50 dòng -> Tách hàm ngay lập tức.

#### Giai đoạn 3: Review & Optimize (Kiểm tra & Tối ưu - 30% Thời gian)
*   **Vue/Flutter/React**: Kiểm tra Re-render (Số lần vẽ lại không cần thiết).
*   **Go/C++**: Kiểm tra Memory Footprint (Dung lượng bộ nhớ chiếm dụng).
*   **Python**: Profile (Đo đạc) thời gian thực thi.

### 2. AI Collaboration Protocol (Giao thức hỗ trợ bởi AI)

Quy tắc giao tiếp để AI hiểu và hỗ trợ bạn chính xác nhất.

#### Rule 1: Context Setting (Thiết lập ngữ cảnh)
Luôn bắt đầu yêu cầu theo mẫu:
*   **Context**: [Ngôn ngữ/Công nghệ]
*   **Task**: [Nhiệm vụ cụ thể]
*   **Requirement**: [Yêu cầu đặc biệt về hiệu năng/bảo mật...]

*Ví dụ: "Context: Golang. Task: Viết middleware xác thực. Requirement: Dùng JWT và cache vào Redis."*

#### Rule 2: Structured Response (Phản hồi có cấu trúc)
AI cần trả lời theo cấu trúc 3 phần:
1.  **Phân tích (Analysis)**: Giải thích ngắn gọn giải pháp bằng tiếng Việt.
2.  **Code**: Code đầy đủ, có comment (chú thích) ở các đoạn phức tạp.
3.  **Lưu ý (Caveats)**: Cảnh báo lỗi tiềm ẩn, cách tối ưu.

#### Rule 3: Debugging Standard (Tiêu chuẩn gỡ lỗi)
Khi báo lỗi cho AI, hãy cung cấp đủ:
*   **Code**: Đoạn code đang lỗi.
*   **Log**: Thông báo lỗi chính xác.
*   **Expectation**: Hành vi bạn mong muốn.

#### Rule 4: Language (Ngôn ngữ)
*   Ưu tiên trả lời bằng **Tiếng Việt**.
*   Giữ nguyên thuật ngữ chuyên ngành Tiếng Anh nếu phổ biến, hoặc mở ngoặc giải thích tiếng Việt ngay sau đó.
    *   *Ví dụ: "Sử dụng Dependency Injection (Tiêm sự phụ thuộc)..."*

#### Rule 5: Documentation (Tài liệu) và comment (chú thích)
*   Viết tài liệu theo chuẩn Google hoặc NumPy.
    *   *Ví dụ: `def process(data: dict) -> list:`*
*   Viết bằng tiếng Việt tối ưu thân thiện dễ hiểu.
*   Luôn cập nhật docs và comment của tất cả chức năng bao gồm chức năng mới sau khi cập nhật code.
