import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Caisse, Paiement } from '../../models/finance/model'
import { financeService } from '../../services/finance/service'

export const useFinanceStore = defineStore('finance', () => {
  const caisses = ref<Caisse[]>([])
  const currentCaisse = ref<Caisse | null>(null)
  const operations = ref<any[]>([])
  const paiements = ref<Paiement[]>([])
  const total = ref(0)
  const totalPaiements = ref(0)
  const loading = ref(false)

  async function listCaisses(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await financeService.caisses(params)
      caisses.value = res.items || res
      total.value = res.total || caisses.value.length
    } finally {
      loading.value = false
    }
  }

  async function getCaisse(id: number) {
    loading.value = true
    try {
      if (caisses.value.length) {
        currentCaisse.value = caisses.value.find((c) => c.id === id) || null
      }
      if (!currentCaisse.value) {
        const res = await financeService.caisses()
        const items = res.items || res
        currentCaisse.value = items.find((c: Caisse) => c.id === id) || null
      }
    } finally {
      loading.value = false
    }
  }

  async function openCaisse(data: { id_gare: number; montant_ouverture: number }) {
    loading.value = true
    try {
      const newCaisse = await financeService.open(data)
      caisses.value.unshift(newCaisse)
      return newCaisse
    } finally {
      loading.value = false
    }
  }

  async function closeCaisse(id: number, montant_cloture?: number) {
    loading.value = true
    try {
      const updated = await financeService.close(id, montant_cloture)
      const idx = caisses.value.findIndex((c) => c.id === id)
      if (idx !== -1) caisses.value[idx] = updated
      if (currentCaisse.value?.id === id) currentCaisse.value = updated
      return updated
    } finally {
      loading.value = false
    }
  }

  async function listOperations(id: number, data: Record<string, any> = {}) {
    loading.value = true
    try {
      const res = await financeService.operations(id, data)
      operations.value = res.items || res
      return operations.value
    } finally {
      loading.value = false
    }
  }

  async function addDepense(idCaisse: number, data: Record<string, any>) {
    loading.value = true
    try {
      const res = await financeService.operations(idCaisse, { ...data, type: 'DEPENSE' })
      operations.value = res.items || res
      return res
    } finally {
      loading.value = false
    }
  }

  async function listPaiements(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await financeService.payments(params)
      paiements.value = res.items || res
      totalPaiements.value = res.total || paiements.value.length
    } finally {
      loading.value = false
    }
  }

  async function payReservation(data: { id_reservation: number; id_caisse: number; montant: number; reference_paiement?: string }) {
    loading.value = true
    try {
      const newPaiement = await financeService.pay(data)
      paiements.value.unshift(newPaiement)
      return newPaiement
    } finally {
      loading.value = false
    }
  }

  async function refundPaiement(id: number, idCaisse: number) {
    loading.value = true
    try {
      const updated = await financeService.refund(id, idCaisse)
      const idx = paiements.value.findIndex((p) => p.id === id)
      if (idx !== -1) paiements.value[idx] = updated
      return updated
    } finally {
      loading.value = false
    }
  }

  return { caisses, currentCaisse, operations, paiements, total, totalPaiements, loading, listCaisses, getCaisse, openCaisse, closeCaisse, listOperations, addDepense, listPaiements, payReservation, refundPaiement }
})
