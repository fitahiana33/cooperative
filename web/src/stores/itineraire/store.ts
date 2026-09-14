import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Itineraire, ItineraireCreate } from '../../models/itineraire/model'
import { itineraireService } from '../../services/itineraire/service'

export const useItineraireStore = defineStore('itineraire', () => {
  const items = ref<Itineraire[]>([])
  const current = ref<Itineraire | null>(null)
  const loading = ref(false)
  const error = ref<any>(null)

  async function listItineraires(params?: Record<string, any>) {
    loading.value = true
    error.value = null
    try {
      const res = await itineraireService.list(params)
      items.value = res.items
      return res
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getItineraire(id: number) {
    loading.value = true
    error.value = null
    try {
      current.value = await itineraireService.get(id)
      return current.value
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createItineraire(data: ItineraireCreate) {
    error.value = null
    try {
      const item = await itineraireService.create(data)
      items.value.unshift(item)
      return item
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function updateItineraire(id: number, data: Partial<ItineraireCreate>) {
    error.value = null
    try {
      const updated = await itineraireService.update(id, data)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      if (current.value?.id === id) current.value = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function toggleItineraire(id: number) {
    error.value = null
    try {
      const updated = await itineraireService.toggle(id)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function deleteItineraire(id: number) {
    error.value = null
    try {
      await itineraireService.remove(id)
      items.value = items.value.filter((i) => i.id !== id)
      if (current.value?.id === id) current.value = null
    } catch (err) {
      error.value = err
      throw err
    }
  }

  return { items, current, loading, error, listItineraires, getItineraire, createItineraire, updateItineraire, toggleItineraire, deleteItineraire }
})
