---
name: reactjs
description: Best practices for ReactJS web development. Sử dụng khi cần viết, review, hoặc tối ưu React code. Bao gồm Advanced Hooks, performance optimization, TanStack Query, TypeScript integration, và architecture patterns.
---

# ReactJS Skill

## 1. Advanced Hooks Pattern
*   **Custom Hooks**: Tách logic phức tạp vào custom hooks (vd: `useAuth`, `useWindowScroll`).
    *   Quy tắc: Bắt đầu bằng `use...`, có thể gọi các hooks khác bên trong.
*   **useReducer**: Thay thế `useState` khi state logic phức tạp (nhiều sub-values) hoặc phụ thuộc state trước đó.

## 2. Performance Optimization
*   **Code Splitting**: Sử dụng `React.lazy` và `Suspense` cho các route hoặc modal nặng.
*   **Virtualization**: Dùng `react-window` hoặc `react-virtualized` cho các list dài (ngàn rows).
*   **Re-render prevention**:
    *   `React.memo`: Cho component.
    *   `useMemo`: Cho biến tính toán nặng.
    *   `useCallback`: Cho function truyền xuống child component.

## 3. Data Fetching
*   **TanStack Query (React Query)**: **BẮT BUỘC** (hoặc SWR) thay vì `useEffect` fetch tay.
    *   Lợi ích: Caching, Auto refetch, Deduping requests, Loading/Error states chuẩn.

## 4. TypeScript Integration
*   **Props Interface**: Định nghĩa rõ ràng.
    ```typescript
    interface ButtonProps {
        label: string;
        onClick: (id: number) => void;
        variant?: 'primary' | 'secondary';
    }
    ```
*   **Generics**: Sử dụng cho reusable components (Table, List).

## 5. Architecture & Patterns
*   **Container/Presentational**: Tách component logic (data fetching) khỏi component hiển thị (rendering).
*   **Error Boundaries**: Bọc app hoặc các feature lớn trong ErrorBoundary để crash không làm trắng trang.
*   **HOC (Higher Order Components)**: Hạn chế dùng, ưu tiên Hooks.

## 6. Styling approach
*   **TailwindCSS**: Utility-first (Recommended).
*   **CSS-in-JS**: Styled-components / Emotion (nếu project yêu cầu dynamic theming mạnh).
*   **CSS Modules**: Giải pháp tốt cho scoped CSS truyền thống.
