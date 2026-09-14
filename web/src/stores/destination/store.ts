import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Destination, DestinationCreate } from '../../models/destination/model'
import { destinationService } from '../../services/destination/service'

export const useDestinationStore = defineStore('destination', () => {
  const items = ref<Destination[]>([])
  const current = ref<Destination | null>(null)
  const loading = ref(false)
  const error = ref<any>(null)

  async function listDestinations(params?: Record<string, any>) {
    loading.value = true
    error.value = null
    try {
      const res = await destinationService.list(params)
      items.value = res.items
      return res
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getDestination(id: number) {
    loading.value = true
    error.value = null
    try {
      current.value = await destinationService.get(id)
      return current.value
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createDestination(data: DestinationCreate) {
    error.value = null
    try {
      const item = await destinationService.create(data)
      items.value.unshift(item)
      return item
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function updateDestination(id: number, data: Partial<DestinationCreate>) {
    error.value = null
    try {
      const updated = await destinationService.update(id, data)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      if (current.value?.id === id) current.value = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function toggleDestination(id: number) {
    error.value = null
    try {
      const updated = await destinationService.toggle(id)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function deleteDestination(id: number) {
    error.value = null
    try {
      await destinationService.remove(id)
      items.value = items.value.filter((i) => i.id !== id)
      if (current.value?.id === id) current.value = null
    } catch (err) {
      error.value = err
      throw err
    }
  }

  return { items, current, loading, error, listDestinations, getDestination, createDestination, updateDestination, toggleDestination, deleteDestination }
})
