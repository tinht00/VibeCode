import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchListings } from '../services/api'

export const useListingStore = defineStore('listingStore', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref('')
  const filters = ref({
    state: '',
    score_lt: '',
    needs_attention: false,
  })

  const stats = computed(() => {
    const total = items.value.length
    const lowScore = items.value.filter((item) => (item.overall_score ?? 0) < 70).length
    const withoutBenchmark = items.value.filter((item) => !item.has_benchmark).length
    const missingData = items.value.filter(
      (item) => item.image_count < 5 || item.attribute_count < 2 || item.tag_count < 8,
    ).length
    return {
      total,
      lowScore,
      withoutBenchmark,
      missingData,
    }
  })

  async function loadListings(extraParams = {}) {
    loading.value = true
    error.value = ''
    try {
      const params = {
        ...filters.value,
        ...extraParams,
      }
      if (params.score_lt === '') {
        delete params.score_lt
      }
      if (!params.state) {
        delete params.state
      }
      if (!params.needs_attention) {
        delete params.needs_attention
      }
      items.value = await fetchListings(params)
    } catch (err) {
      error.value = err?.response?.data?.detail || 'Không thể tải danh sách listing.'
    } finally {
      loading.value = false
    }
  }

  return {
    items,
    loading,
    error,
    filters,
    stats,
    loadListings,
  }
})
