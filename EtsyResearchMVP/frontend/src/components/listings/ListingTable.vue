<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Listing</th>
          <th>Điểm</th>
          <th>Trạng thái</th>
          <th>Giá</th>
          <th>Tags</th>
          <th>Ảnh</th>
          <th>Benchmark</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>
            <strong>{{ item.title }}</strong>
            <div class="muted">Taxonomy: {{ item.taxonomy_id ?? 'Chưa có' }}</div>
          </td>
          <td>{{ item.overall_score ?? 'Chưa audit' }}</td>
          <td>{{ item.state }}</td>
          <td>{{ formatPrice(item) }}</td>
          <td>{{ item.tag_count }}</td>
          <td>{{ item.image_count }}</td>
          <td>
            <span :class="['pill', item.has_benchmark ? 'success' : 'warn']">
              {{ item.has_benchmark ? 'Đã có' : 'Chưa có' }}
            </span>
          </td>
          <td>
            <RouterLink class="btn-secondary" :to="`/listings/${item.id}`">
              Xem audit
            </RouterLink>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
/**
 * Bảng danh sách listing trên dashboard.
 */
defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})

function formatPrice(item) {
  if (item.price_amount == null) {
    return 'Chưa có'
  }
  return `${item.price_amount} ${item.currency_code ?? ''}`.trim()
}
</script>
