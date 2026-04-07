<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Nội bộ</p>
        <h1>Etsy Research MVP</h1>
        <p class="muted">
          Dashboard tối ưu listing Etsy theo hướng audit, benchmark và gợi ý hành động.
        </p>
      </div>

      <nav class="nav-links">
        <RouterLink to="/connect">Kết nối shop</RouterLink>
        <RouterLink to="/listings">Danh sách listing</RouterLink>
      </nav>
    </aside>

    <main class="page-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
/**
 * Layout gốc của ứng dụng.
 */
</script>
