import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dashboardService } from '../../services/dashboard/service'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<any>(null)
  const departsStats = ref<any>(null)
  const financeStats = ref<any>(null)
  const loading = ref(false)

  async function loadStats() {
    loading.value = true
    try {
      stats.value = await dashboardService.summary()
      return stats.value
    } finally {
      loading.value = false
    }
  }

  async function loadDepartsStats(params?: Record<string, any>) {
    loading.value = true
    try {
      departsStats.value = await dashboardService.statistics({ ...params, type: 'departs' })
      return departsStats.value
    } finally {
      loading.value = false
    }
  }

  async function loadFinanceStats(params?: Record<string, any>) {
    loading.value = true
    try {
      financeStats.value = await dashboardService.statistics({ ...params, type: 'finance' })
      return financeStats.value
    } finally {
      loading.value = false
    }
  }

  return { stats, departsStats, financeStats, loading, loadStats, loadDepartsStats, loadFinanceStats }
})
