import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Depart, DepartCreate, DepartStatus } from '../../models/depart/model'
import { departService } from '../../services/depart/service'

export const useDepartStore = defineStore('depart', () => {
  const items = ref<Depart[]>([])
  const current = ref<Depart | null>(null)
  const loading = ref(false)
  const error = ref<any>(null)

  async function listDeparts(params?: Record<string, any>) {
    loading.value = true
    error.value = null
    try {
      const res = await departService.list(params)
      items.value = res.items
      return res
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getDepart(id: number) {
    loading.value = true
    error.value = null
    try {
      current.value = await departService.get(id)
      return current.value
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createDepart(data: DepartCreate) {
    error.value = null
    try {
      const item = await departService.create(data)
      items.value.unshift(item)
      return item
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function updateDepart(id: number, data: Partial<DepartCreate>) {
    error.value = null
    try {
      const updated = await departService.update(id, data)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      if (current.value?.id === id) current.value = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function updateDepartStatus(id: number, statut: DepartStatus) {
    error.value = null
    try {
      const updated = await departService.updateStatus(id, statut)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      if (current.value?.id === id) current.value = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function cancelDepart(id: number, idCaisse?: number) {
    error.value = null
    try {
      const updated = await departService.cancel(id, idCaisse)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      if (current.value?.id === id) current.value = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function deleteDepart(id: number) {
    error.value = null
    try {
      const res = await (departService as any).remove?.(id)
      items.value = items.value.filter((i) => i.id !== id)
      if (current.value?.id === id) current.value = null
      return res
    } catch (err) {
      error.value = err
      throw err
    }
  }

  return { items, current, loading, error, listDeparts, getDepart, createDepart, updateDepart, updateDepartStatus, cancelDepart, deleteDepart }
})
