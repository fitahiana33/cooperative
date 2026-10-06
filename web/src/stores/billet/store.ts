import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Billet } from '../../models/billet/model'
import { billetService } from '../../services/billet/service'

export const useBilletStore = defineStore('billet', () => {
  const billets = ref<Billet[]>([])
  const currentBillet = ref<Billet | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function listBillets(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await billetService.list(params)
      billets.value = res.items || res
      total.value = res.total || billets.value.length
    } finally {
      loading.value = false
    }
  }

  async function getBillet(id: number) {
    loading.value = true
    try {
      currentBillet.value = await billetService.get(id)
    } finally {
      loading.value = false
    }
  }

  async function findBillet(code: string) {
    loading.value = true
    try {
      const found = await billetService.find(code)
      currentBillet.value = found
      return found
    } finally {
      loading.value = false
    }
  }

  return { billets, currentBillet, total, loading, listBillets, getBillet, findBillet }
})
