import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Gare, GareCreate } from '../../models/gare/model'
import { gareService } from '../../services/gare/service'

export const useGareStore = defineStore('gare', () => {
  const gares = ref<Gare[]>([])
  const currentGare = ref<Gare | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchGares(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await gareService.listGares(params)
      gares.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchGare(id: number) {
    loading.value = true
    try {
      currentGare.value = await gareService.getGare(id)
    } finally {
      loading.value = false
    }
  }

  async function createGare(data: GareCreate) {
    const newGare = await gareService.createGare(data)
    gares.value.unshift(newGare)
    return newGare
  }

  async function updateGare(id: number, data: Partial<GareCreate>) {
    const updated = await gareService.updateGare(id, data)
    const idx = gares.value.findIndex((g) => g.id === id)
    if (idx !== -1) gares.value[idx] = updated
    if (currentGare.value?.id === id) currentGare.value = updated
    return updated
  }

  async function toggleGare(id: number) {
    const updated = await gareService.toggleGare(id)
    const idx = gares.value.findIndex((g) => g.id === id)
    if (idx !== -1) gares.value[idx] = updated
    return updated
  }

  async function deleteGare(id: number) {
    await gareService.deleteGare(id)
    gares.value = gares.value.filter((g) => g.id !== id)
  }

  return { gares, currentGare, total, loading, fetchGares, fetchGare, createGare, updateGare, toggleGare, deleteGare }
})
