<template>
  <div class="surface">
    <h3 class="section-title">Gợi ý hành động</h3>
    <div v-if="!items?.length" class="empty-state">
      Chưa có recommendation. Chạy audit để sinh gợi ý tối ưu.
    </div>
    <div v-else class="page-grid">
      <article v-for="item in items" :key="item.code" class="surface">
        <strong>{{ item.title }}</strong>
        <p class="muted">{{ item.content }}</p>
      </article>
    </div>
  </div>
</template>

<script setup>
/**
 * Card recommendation cho listing hiện tại.
 */
defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})
</script>
