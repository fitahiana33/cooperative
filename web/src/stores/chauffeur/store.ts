import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Chauffeur, ChauffeurCreate } from '../../models/chauffeur/model'
import { chauffeurService } from '../../services/chauffeur/service'

export const useChauffeurStore = defineStore('chauffeur', () => {
  const chauffeurs = ref<Chauffeur[]>([])
  const currentChauffeur = ref<Chauffeur | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchChauffeurs(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await chauffeurService.listChauffeurs(params)
      chauffeurs.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchChauffeur(id: number) {
    loading.value = true
    try {
      currentChauffeur.value = await chauffeurService.getChauffeur(id)
    } finally {
      loading.value = false
    }
  }

  async function createChauffeur(data: ChauffeurCreate) {
    const item = await chauffeurService.createChauffeur(data)
    chauffeurs.value.unshift(item)
    return item
  }

  async function updateChauffeur(id: number, data: Partial<ChauffeurCreate>) {
    const updated = await chauffeurService.updateChauffeur(id, data)
    const idx = chauffeurs.value.findIndex((c) => c.id === id)
    if (idx !== -1) chauffeurs.value[idx] = updated
    if (currentChauffeur.value?.id === id) currentChauffeur.value = updated
    return updated
  }

  async function toggleChauffeur(id: number) {
    const updated = await chauffeurService.toggleChauffeur(id)
    const idx = chauffeurs.value.findIndex((c) => c.id === id)
    if (idx !== -1) chauffeurs.value[idx] = updated
    return updated
  }

  async function deleteChauffeur(id: number) {
    await chauffeurService.deleteChauffeur(id)
    chauffeurs.value = chauffeurs.value.filter((c) => c.id !== id)
  }

  return { chauffeurs, currentChauffeur, total, loading, fetchChauffeurs, fetchChauffeur, createChauffeur, updateChauffeur, toggleChauffeur, deleteChauffeur }
})
