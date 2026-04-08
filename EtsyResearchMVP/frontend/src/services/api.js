import axios from 'axios'

const api = axios.create({
  baseURL: '/',
  timeout: 30000,
})

export async function fetchHealth() {
  const { data } = await api.get('/health')
  return data
}

export async function fetchShops() {
  const { data } = await api.get('/api/shops')
  return data
}

export async function fetchListings(params = {}) {
  const { data } = await api.get('/api/listings', { params })
  return data
}

export async function fetchListingDetail(id) {
  const { data } = await api.get(`/api/listings/${id}`)
  return data
}

export async function runAudit(id) {
  const { data } = await api.post(`/api/listings/${id}/audit`)
  return data
}

export async function runBenchmark(id, seedKeyword) {
  const { data } = await api.post(`/api/listings/${id}/benchmark`, {
    seed_keyword: seedKeyword,
  })
  return data
}

export async function fetchRecommendations(id) {
  const { data } = await api.get(`/api/listings/${id}/recommendations`)
  return data
}

export async function syncShop(id) {
  const { data } = await api.post(`/api/shops/${id}/sync`)
  return data
}

export async function startEtsyOauth() {
  const { data } = await api.get('/api/auth/etsy/start')
  return data
}
