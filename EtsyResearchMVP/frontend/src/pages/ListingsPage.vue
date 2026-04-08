<template>
  <section class="page-grid">
    <div class="page-card">
      <div class="toolbar">
        <div>
          <p class="eyebrow">Dashboard</p>
          <h2>Danh sách listing</h2>
          <p class="muted">
            Ưu tiên xác định listing yếu, thiếu dữ liệu hoặc chưa benchmark để tối ưu nhanh.
          </p>
        </div>
        <button class="btn-secondary" @click="store.loadListings">Làm mới</button>
      </div>

      <div class="section-row">
        <div class="stat-card">
          <span class="muted">Tổng listing</span>
          <strong>{{ store.stats.total }}</strong>
        </div>
        <div class="stat-card">
          <span class="muted">Điểm thấp</span>
          <strong>{{ store.stats.lowScore }}</strong>
        </div>
        <div class="stat-card">
          <span class="muted">Chưa benchmark</span>
          <strong>{{ store.stats.withoutBenchmark }}</strong>
        </div>
        <div class="stat-card">
          <span class="muted">Thiếu dữ liệu</span>
          <strong>{{ store.stats.missingData }}</strong>
        </div>
      </div>
    </div>

    <div class="page-card">
      <div class="filters">
        <label class="field">
          <span>Trạng thái</span>
          <select v-model="store.filters.state">
            <option value="">Tất cả</option>
            <option value="active">active</option>
            <option value="draft">draft</option>
          </select>
        </label>

        <label class="field">
          <span>Điểm dưới</span>
          <select v-model="store.filters.score_lt">
            <option value="">Tất cả</option>
            <option value="80">80</option>
            <option value="70">70</option>
            <option value="60">60</option>
          </select>
        </label>

        <label class="field">
          <span>Cần chú ý</span>
          <select v-model="store.filters.needs_attention">
            <option :value="false">Tắt</option>
            <option :value="true">Bật</option>
          </select>
        </label>

        <button class="btn" @click="store.loadListings">Áp dụng bộ lọc</button>
      </div>
    </div>

    <div v-if="store.error" class="error-state">{{ store.error }}</div>

    <ListingTable v-if="store.items.length" :items="store.items" />
    <div v-else class="empty-state">
      Chưa có listing để hiển thị. Hãy kết nối shop và chạy đồng bộ trước.
    </div>
  </section>
</template>

<script setup>
/**
 * Trang dashboard listing với lọc nhanh theo điểm và độ đầy đủ dữ liệu.
 */
import { onMounted } from 'vue'

import ListingTable from '../components/listings/ListingTable.vue'
import { useListingStore } from '../stores/listingStore'

const store = useListingStore()

onMounted(() => {
  store.loadListings()
})
</script>
