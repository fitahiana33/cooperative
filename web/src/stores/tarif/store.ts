import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Tarif, TarifCreate } from '../../models/tarif/model'
import { tarifService } from '../../services/tarif/service'

export const useTarifStore = defineStore('tarif', () => {
  const items = ref<Tarif[]>([])
  const current = ref<Tarif | null>(null)
  const loading = ref(false)
  const error = ref<any>(null)

  async function listTarifs(params?: Record<string, any>) {
    loading.value = true
    error.value = null
    try {
      const res = await tarifService.list(params)
      items.value = res.items
      return res
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getTarif(id: number) {
    loading.value = true
    error.value = null
    try {
      current.value = await tarifService.get(id)
      return current.value
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createTarif(data: TarifCreate) {
    error.value = null
    try {
      const item = await tarifService.create(data)
      items.value.unshift(item)
      return item
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function updateTarif(id: number, data: Partial<TarifCreate>) {
    error.value = null
    try {
      const updated = await tarifService.update(id, data)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      if (current.value?.id === id) current.value = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function toggleTarif(id: number) {
    error.value = null
    try {
      const updated = await tarifService.toggle(id)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function deleteTarif(id: number) {
    error.value = null
    try {
      await tarifService.remove(id)
      items.value = items.value.filter((i) => i.id !== id)
      if (current.value?.id === id) current.value = null
    } catch (err) {
      error.value = err
      throw err
    }
  }

  return { items, current, loading, error, listTarifs, getTarif, createTarif, updateTarif, toggleTarif, deleteTarif }
})
