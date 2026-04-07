import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchHealth, fetchShops, startEtsyOauth, syncShop } from '../services/api'

export const useEtsyConnectionStore = defineStore('etsyConnection', () => {
  const shops = ref([])
  const health = ref(null)
  const loading = ref(false)
  const syncingShopId = ref(null)
  const error = ref('')

  const isConnected = computed(() => shops.value.length > 0)

  async function loadDashboard() {
    loading.value = true
    error.value = ''
    try {
      const [healthResponse, shopsResponse] = await Promise.all([
        fetchHealth(),
        fetchShops(),
      ])
      health.value = healthResponse
      shops.value = shopsResponse
    } catch (err) {
      error.value = err?.response?.data?.detail || 'Không thể tải trạng thái kết nối.'
    } finally {
      loading.value = false
    }
  }

  async function connectEtsy() {
    const payload = await startEtsyOauth()
    window.location.href = payload.authorization_url
  }

  async function runSync(shopId) {
    syncingShopId.value = shopId
    error.value = ''
    try {
      await syncShop(shopId)
      await loadDashboard()
    } catch (err) {
      error.value = err?.response?.data?.detail || 'Đồng bộ shop thất bại.'
    } finally {
      syncingShopId.value = null
    }
  }

  return {
    shops,
    health,
    loading,
    syncingShopId,
    error,
    isConnected,
    loadDashboard,
    connectEtsy,
    runSync,
  }
})
