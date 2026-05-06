import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/data-sources',
    name: 'DataSourceManager',
    component: () => import('@/views/DataSourceManager.vue'),
    meta: {
      title: '数据源管理',
      icon: 'DataSources',
      requiresAuth: true,
      permissions: ['admin', 'data_admin']
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router