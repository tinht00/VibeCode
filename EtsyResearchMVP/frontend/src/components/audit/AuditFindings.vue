<template>
  <div class="surface">
    <h3 class="section-title">Findings</h3>
    <div v-if="!findings?.length" class="empty-state">
      Chưa có findings. Hãy chạy audit để xem các cảnh báo cần xử lý.
    </div>
    <div v-else class="page-grid">
      <article v-for="item in findings" :key="item.code" class="surface">
        <div class="toolbar">
          <span class="pill warn">{{ item.severity }}</span>
          <strong>{{ item.code }}</strong>
        </div>
        <p>{{ item.message_vi }}</p>
        <p class="muted">{{ item.action_vi }}</p>
      </article>
    </div>
  </div>
</template>

<script setup>
/**
 * Hiển thị findings sau khi audit listing.
 */
defineProps({
  findings: {
    type: Array,
    default: () => [],
  },
})
</script>
