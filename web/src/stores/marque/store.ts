import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Marque, MarqueCreate } from '../../models/marque/model'
import { marqueService } from '../../services/marque/service'

export const useMarqueStore = defineStore('marque', () => {
  const marques = ref<Marque[]>([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchMarques(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await marqueService.listMarques(params)
      marques.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function createMarque(data: MarqueCreate) {
    const item = await marqueService.createMarque(data)
    marques.value.unshift(item)
    return item
  }

  async function updateMarque(id: number, data: Partial<MarqueCreate>) {
    const updated = await marqueService.updateMarque(id, data)
    const idx = marques.value.findIndex((m) => m.id === id)
    if (idx !== -1) marques.value[idx] = updated
    return updated
  }

  async function toggleMarque(id: number) {
    const updated = await marqueService.toggleMarque(id)
    const idx = marques.value.findIndex((m) => m.id === id)
    if (idx !== -1) marques.value[idx] = updated
    return updated
  }

  async function deleteMarque(id: number) {
    await marqueService.deleteMarque(id)
    marques.value = marques.value.filter((m) => m.id !== id)
  }

  return { marques, total, loading, fetchMarques, createMarque, updateMarque, toggleMarque, deleteMarque }
})
