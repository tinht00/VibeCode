import { ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchListingDetail, fetchRecommendations, runAudit, runBenchmark } from '../services/api'

export const useAuditStore = defineStore('auditStore', () => {
  const listing = ref(null)
  const audit = ref(null)
  const benchmark = ref(null)
  const recommendations = ref(null)
  const loading = ref(false)
  const error = ref('')

  async function loadListing(id) {
    loading.value = true
    error.value = ''
    try {
      const [listingPayload, recommendationPayload] = await Promise.all([
        fetchListingDetail(id),
        fetchRecommendations(id),
      ])
      listing.value = listingPayload
      recommendations.value = recommendationPayload
    } catch (err) {
      error.value = err?.response?.data?.detail || 'Không thể tải chi tiết listing.'
    } finally {
      loading.value = false
    }
  }

  async function executeAudit(id) {
    loading.value = true
    error.value = ''
    try {
      audit.value = await runAudit(id)
      recommendations.value = await fetchRecommendations(id)
    } catch (err) {
      error.value = err?.response?.data?.detail || 'Chạy audit thất bại.'
    } finally {
      loading.value = false
    }
  }

  async function executeBenchmark(id, seedKeyword) {
    loading.value = true
    error.value = ''
    try {
      benchmark.value = await runBenchmark(id, seedKeyword)
    } catch (err) {
      error.value = err?.response?.data?.detail || 'Chạy benchmark thất bại.'
    } finally {
      loading.value = false
    }
  }

  return {
    listing,
    audit,
    benchmark,
    recommendations,
    loading,
    error,
    loadListing,
    executeAudit,
    executeBenchmark,
  }
})
