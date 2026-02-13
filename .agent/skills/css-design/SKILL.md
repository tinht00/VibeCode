---
name: css-design
description: Best practices for CSS, SCSS, Responsive Design, and UI Patterns. Sử dụng khi cần viết CSS/SCSS, thiết kế responsive layout, tối ưu animation, hoặc giải quyết vấn đề accessibility.
---

# CSS & UI Design Skill

## 1. Architecture & Methodology
*   **BEM (Block Element Modifier)**: Tiêu chuẩn đặt tên class cho CSS thuần/SCSS.
    *   `.card` (Block) -> `.card__image` (Element) -> `.card--featured` (Modifier).
*   **Mobile-First**: Define style mặc định cho mobile trước. Dùng `@media (min-width: ...)` để override cho màn hình lớn hơn.
*   **Utility-First (Tailwind)**: Ưu tiên dùng utility classes thay vì viết CSS custom. Giúp giảm bundle size và consistency UI.

## 2. Layout Patterns (Flex & Grid)
*   **Flexbox**: Căn chỉnh 1 chiều (hàng/cột).
    *   Center hoàn hảo: `display: flex; justify-content: center; align-items: center;`
*   **CSS Grid**: Layout 2 chiều phức tạp.
    *   Responsive Grid không cần media query: `grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));`

## 3. Modern CSS Features
*   **Variables (Custom Properties)**: `--primary-color: #ff5722;`. Dễ dàng implement Dark Mode bằng cách override biến ở `:root` hoặc `[data-theme='dark']`.
*   **Clamp()**: Responsive typography mượt mà. `font-size: clamp(1rem, 2.5vw, 2rem);`
*   **Aspect Ratio**: `aspect-ratio: 16 / 9;` thay cho hack padding-top ngày xưa.

## 4. UI/UX Principles (Deep Dive)
*   **Accessibility (A11y)**:
    *   Độ tương phản (Contrast Ratio) >= 4.5:1.
    *   Focus state: Không bao giờ `outline: none` mà không thay thế bằng style khác rõ ràng.
    *   Semantic Tags: Dùng `<button>`, `<a>`, `<nav>`, `<main>` đúng ngữ nghĩa.
*   **Motion**:
    *   Thời gian transition: 200ms - 300ms là tự nhiên nhất.
    *   Easing: Dùng `ease-out` cho hiện ra, `ease-in` cho biến mất.
    *   Performance: Chỉ animate `transform` và `opacity`. Hạn chế animate `width`, `height`, `top`, `left` (gây layout thrashing).

## 5. SCSS/SASS Advanced
*   **Functions & Mixins**: Dùng để gen các utility classes hoặc xử lý màu sắc (lighten, darken).
*   **Nesting Limit**: Tối đa 3 cấp.
    ```scss
    .nav {
        ul { ... } // OK
        li {
             a { ... } // Warning
             span { i { ... } } // DON'T
        }
    }
    ```
