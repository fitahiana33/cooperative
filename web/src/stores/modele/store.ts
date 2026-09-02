import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Modele, ModeleCreate } from '../../models/modele/model'
import { modeleService } from '../../services/modele/service'

export const useModeleStore = defineStore('modele', () => {
  const modeles = ref<Modele[]>([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchModeles(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await modeleService.listModeles(params)
      modeles.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function createModele(data: ModeleCreate) {
    const item = await modeleService.createModele(data)
    modeles.value.unshift(item)
    return item
  }

  async function updateModele(id: number, data: Partial<ModeleCreate>) {
    const updated = await modeleService.updateModele(id, data)
    const idx = modeles.value.findIndex((m) => m.id === id)
    if (idx !== -1) modeles.value[idx] = updated
    return updated
  }

  async function toggleModele(id: number) {
    const updated = await modeleService.toggleModele(id)
    const idx = modeles.value.findIndex((m) => m.id === id)
    if (idx !== -1) modeles.value[idx] = updated
    return updated
  }

  async function deleteModele(id: number) {
    await modeleService.deleteModele(id)
    modeles.value = modeles.value.filter((m) => m.id !== id)
  }

  return { modeles, total, loading, fetchModeles, createModele, updateModele, toggleModele, deleteModele }
})
