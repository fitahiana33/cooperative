import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Cooperative, CooperativeCreate } from '../../models/cooperative/model'
import { cooperativeService } from '../../services/cooperative/service'

export const useCooperativeStore = defineStore('cooperative', () => {
  const cooperatives = ref<Cooperative[]>([])
  const currentCooperative = ref<Cooperative | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchCooperatives(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await cooperativeService.listCooperatives(params)
      cooperatives.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchCooperative(id: number) {
    loading.value = true
    try {
      currentCooperative.value = await cooperativeService.getCooperative(id)
    } finally {
      loading.value = false
    }
  }

  async function createCooperative(data: CooperativeCreate) {
    const newCoop = await cooperativeService.createCooperative(data)
    cooperatives.value.unshift(newCoop)
    return newCoop
  }

  async function updateCooperative(id: number, data: Partial<CooperativeCreate>) {
    const updated = await cooperativeService.updateCooperative(id, data)
    const idx = cooperatives.value.findIndex((c) => c.id === id)
    if (idx !== -1) cooperatives.value[idx] = updated
    if (currentCooperative.value?.id === id) currentCooperative.value = updated
    return updated
  }

  async function toggleCooperative(id: number) {
    const updated = await cooperativeService.toggleCooperative(id)
    const idx = cooperatives.value.findIndex((c) => c.id === id)
    if (idx !== -1) cooperatives.value[idx] = updated
    return updated
  }

  async function deleteCooperative(id: number) {
    await cooperativeService.deleteCooperative(id)
    cooperatives.value = cooperatives.value.filter((c) => c.id !== id)
  }

  return { cooperatives, currentCooperative, total, loading, fetchCooperatives, fetchCooperative, createCooperative, updateCooperative, toggleCooperative, deleteCooperative }
})
