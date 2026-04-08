<template>
  <section class="page-grid">
    <div class="page-card">
      <div class="toolbar">
        <div>
          <p class="eyebrow">OAuth Etsy</p>
          <h2>Kết nối shop</h2>
          <p class="muted">
            Bản MVP chỉ đọc dữ liệu để audit listing và benchmark từ khóa, không ghi ngược lên Etsy.
          </p>
        </div>
        <button class="btn" @click="store.connectEtsy">Kết nối Etsy</button>
      </div>
    </div>

    <div v-if="store.error" class="error-state">{{ store.error }}</div>

    <div class="page-card">
      <div class="toolbar">
        <h2>Trạng thái hệ thống</h2>
        <button class="btn-secondary" @click="store.loadDashboard">Tải lại</button>
      </div>
      <div class="section-row">
        <div class="stat-card">
          <span class="muted">API</span>
          <strong>{{ store.health?.status ?? '...' }}</strong>
        </div>
        <div class="stat-card">
          <span class="muted">Shop đã kết nối</span>
          <strong>{{ store.shops.length }}</strong>
        </div>
      </div>
    </div>

    <div class="page-card">
      <h2>Danh sách shop</h2>
      <div v-if="store.loading" class="empty-state">Đang tải dữ liệu kết nối...</div>
      <div v-else-if="!store.shops.length" class="empty-state">
        Chưa có shop nào được kết nối. Hãy bắt đầu bằng OAuth Etsy.
      </div>
      <div v-else class="page-grid">
        <article v-for="shop in store.shops" :key="shop.id" class="surface">
          <div class="toolbar">
            <div>
              <strong>{{ shop.name }}</strong>
              <div class="muted">Shop ID Etsy: {{ shop.etsy_shop_id }}</div>
            </div>
            <button
              class="btn-secondary"
              :disabled="store.syncingShopId === shop.id"
              @click="store.runSync(shop.id)"
            >
              {{ store.syncingShopId === shop.id ? 'Đang sync...' : 'Đồng bộ shop' }}
            </button>
          </div>
          <div class="chips">
            <span class="chip">Tiền tệ: {{ shop.currency_code ?? 'Chưa có' }}</span>
            <span class="chip">Listing active: {{ shop.listing_active_count }}</span>
            <span class="chip">Sync gần nhất: {{ shop.last_sync_at ?? 'Chưa có' }}</span>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
/**
 * Trang kết nối Etsy và theo dõi các shop nội bộ đã cấp quyền.
 */
import { onMounted } from 'vue'

import { useEtsyConnectionStore } from '../stores/etsyConnectionStore'

const store = useEtsyConnectionStore()

onMounted(() => {
  store.loadDashboard()
})
</script>
