import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Vehicule, VehiculeCreate } from '../../models/vehicule/model'
import { vehiculeService } from '../../services/vehicule/service'

export const useVehiculeStore = defineStore('vehicule', () => {
  const vehicules = ref<Vehicule[]>([])
  const currentVehicule = ref<Vehicule | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchVehicules(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await vehiculeService.listVehicules(params)
      vehicules.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchVehicule(id: number) {
    loading.value = true
    try {
      currentVehicule.value = await vehiculeService.getVehicule(id)
    } finally {
      loading.value = false
    }
  }

  async function createVehicule(data: VehiculeCreate) {
    const item = await vehiculeService.createVehicule(data)
    vehicules.value.unshift(item)
    return item
  }

  async function updateVehicule(id: number, data: Partial<VehiculeCreate>) {
    const updated = await vehiculeService.updateVehicule(id, data)
    const idx = vehicules.value.findIndex((v) => v.id === id)
    if (idx !== -1) vehicules.value[idx] = updated
    if (currentVehicule.value?.id === id) currentVehicule.value = updated
    return updated
  }

  async function toggleVehicule(id: number) {
    const updated = await vehiculeService.toggleVehicule(id)
    const idx = vehicules.value.findIndex((v) => v.id === id)
    if (idx !== -1) vehicules.value[idx] = updated
    return updated
  }

  async function deleteVehicule(id: number) {
    await vehiculeService.deleteVehicule(id)
    vehicules.value = vehicules.value.filter((v) => v.id !== id)
  }

  return { vehicules, currentVehicule, total, loading, fetchVehicules, fetchVehicule, createVehicule, updateVehicule, toggleVehicule, deleteVehicule }
})
