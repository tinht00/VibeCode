<template>
  <section class="page-grid">
    <div v-if="store.error" class="error-state">{{ store.error }}</div>

    <div class="page-card split-layout">
      <div class="surface">
        <p class="eyebrow">Listing</p>
        <h2>{{ store.listing?.title ?? 'Đang tải...' }}</h2>
        <p class="muted">{{ store.listing?.description || 'Chưa có mô tả.' }}</p>

        <div class="chips" v-if="store.listing">
          <span class="chip">Giá: {{ formatPrice(store.listing) }}</span>
          <span class="chip">Taxonomy: {{ store.listing.taxonomy_id ?? 'Chưa có' }}</span>
          <span class="chip">
            Cá nhân hóa: {{ store.listing.is_personalizable ? 'Có' : 'Không' }}
          </span>
        </div>

        <div class="page-grid">
          <div class="surface">
            <strong>Tags hiện tại</strong>
            <div class="chips">
              <span v-for="tag in store.listing?.tags ?? []" :key="tag" class="chip">{{ tag }}</span>
            </div>
          </div>

          <div class="surface">
            <strong>Attributes</strong>
            <div v-if="store.listing?.attributes?.length" class="page-grid">
              <div v-for="attribute in store.listing.attributes" :key="attribute.id">
                <strong>{{ attribute.property_name || 'Thuộc tính' }}</strong>
                <div class="muted">{{ attribute.values_json.join(', ') || 'Chưa có giá trị' }}</div>
              </div>
            </div>
            <div v-else class="empty-state">Listing chưa có attribute nào.</div>
          </div>
        </div>
      </div>

      <div class="surface">
        <p class="eyebrow">Hành động</p>
        <h2>Audit và benchmark</h2>
        <div class="toolbar">
          <button class="btn" :disabled="store.loading" @click="store.executeAudit(listingId)">
            {{ store.loading ? 'Đang xử lý...' : 'Chạy audit' }}
          </button>
        </div>

        <label class="field">
          <span>Seed keyword benchmark</span>
          <input v-model="seedKeyword" placeholder="Ví dụ: teacher mug" />
        </label>
        <button class="btn-secondary" :disabled="store.loading || !seedKeyword" @click="store.executeBenchmark(listingId, seedKeyword)">
          Chạy benchmark
        </button>

        <div class="surface" v-if="store.audit">
          <strong>Điểm tổng</strong>
          <div class="stat-card">
            <strong>{{ store.audit.overall_score }}</strong>
          </div>
        </div>

        <div class="surface" v-if="store.benchmark">
          <strong>Benchmark gần nhất</strong>
          <p class="muted">
            {{ store.benchmark.snapshot_count }} listings, median price:
            {{ store.benchmark.median_price ?? 'Chưa có' }}
          </p>
          <div class="chips">
            <span v-for="term in store.benchmark.common_terms" :key="term" class="chip">{{ term }}</span>
          </div>
        </div>
      </div>
    </div>

    <AuditFindings :findings="store.audit?.findings ?? []" />
    <RecommendationCards :items="store.recommendations?.recommendations ?? []" />
  </section>
</template>

<script setup>
/**
 * Trang chi tiết listing, tập trung vào audit findings và benchmark keyword.
 */
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import AuditFindings from '../components/audit/AuditFindings.vue'
import RecommendationCards from '../components/audit/RecommendationCards.vue'
import { useAuditStore } from '../stores/auditStore'

const route = useRoute()
const store = useAuditStore()
const listingId = Number(route.params.id)
const seedKeyword = ref('')

onMounted(() => {
  store.loadListing(listingId)
})

function formatPrice(listing) {
  if (!listing || listing.price_amount == null) {
    return 'Chưa có'
  }
  return `${listing.price_amount} ${listing.currency_code ?? ''}`.trim()
}
</script>
