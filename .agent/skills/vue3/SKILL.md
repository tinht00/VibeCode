---
name: vue3
description: Best practices and rules for Vue 3 development. Sử dụng khi cần viết, review, hoặc tối ưu Vue 3 code. Bao gồm Composition API, Pinia state management, advanced reactivity, routing guards, API handling, testing (Vitest), và anti-patterns.
---

# Vue 3 Skill

## 1. Architecture
*   **Composition API**: Bắt buộc sử dụng `<script setup>`.
*   **Directory Structure**:
    *   `src/components`: Reusable components (buttons, inputs).
    *   `src/views` hoặc `src/pages`: Page-level components.
    *   `src/stores`: Pinia stores.
    *   `src/composables`: Logic tái sử dụng (composable functions).
    *   `src/services`: API calls (Axios instances).

## 2. State Management (Pinia)
*   Định nghĩa Store theo dạng `defineStore` với Setup Store (function syntax) để đồng bộ với Composition API.
*   Tránh thay đổi state trực tiếp từ component; hãy dùng actions.
*   **Persist**: Sử dụng plugin `pinia-plugin-persistedstate` nếu cần lưu state trọn đời phiên.

## 3. Advanced Reactivity
*   **watch vs watchEffect**:
    *   `watch`: Dùng khi cần theo dõi lazy source cụ thể hoặc cần access giá trị cũ/mới (`oldValue`, `newValue`).
    *   `watchEffect`: Dùng khi muốn chạy ngay lập tức và tự động track dependency bên trong.
*   **shallowRef**: Sử dụng cho data structure lớn không cần deep reactivity (VD: chart data, large list) để tối ưu performance.

## 4. Routing & Guards
*   **Route Meta**: Dùng meta field để định nghĩa quyền truy cập (vd: `requiresAuth`).
*   **Navigation Guards**:
    ```javascript
    router.beforeEach((to, from, next) => {
      if (to.meta.requiresAuth && !isAuthenticated) next('/login')
      else next()
    })
    ```

## 5. API Handling
*   **Axios Interceptors**: Xử lý global error (401, 500) hoặc inject token tại `src/services/api.js`.
*   **Composite Service**: Pattern `useFetch` hoặc `useQuery` (TanStack Query) để quản lý loading/error state tự động.

## 6. Testing
*   **Unit Test**: Sử dụng **Vitest**.
*   **Component Test**: Sử dụng **Vue Test Utils**.
    ```javascript
    import { mount } from '@vue/test-utils'
    test('displays message', () => {
      const wrapper = mount(MessageComponent, { props: { msg: 'Hello' } })
      expect(wrapper.text()).toContain('Hello')
    })
    ```

## 7. Performance & Optimization
*   **Lazy Loading**:
    ```javascript
    const UserDetails = () => import('./views/UserDetails.vue')
    ```
*   **KeepAlive**: Cache component instance.
*   **Computed**: Luôn ưu tiên computed thay vì function call trong template.
*   **v-once/v-memo**: Dùng cho static content lớn.

## 8. Anti-Patterns (Cần tránh)
*   ❌ Dùng Options API (`data`, `methods`).
*   ❌ Mutate props trực tiếp.
*   ❌ Logic phức tạp trong Template.
