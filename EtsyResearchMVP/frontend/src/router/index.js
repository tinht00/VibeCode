import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/connect',
  },
  {
    path: '/connect',
    component: () => import('../pages/ConnectShopPage.vue'),
  },
  {
    path: '/listings',
    component: () => import('../pages/ListingsPage.vue'),
  },
  {
    path: '/listings/:id',
    component: () => import('../pages/ListingDetailPage.vue'),
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
