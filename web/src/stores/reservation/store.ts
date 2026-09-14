import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Reservation } from '../../models/reservation/model'
import { reservationService } from '../../services/reservation/service'

export const useReservationStore = defineStore('reservation', () => {
  const items = ref<Reservation[]>([])
  const current = ref<Reservation | null>(null)
  const loading = ref(false)
  const error = ref<any>(null)

  async function listReservations(params?: Record<string, any>) {
    loading.value = true
    error.value = null
    try {
      const res = await reservationService.list(params)
      items.value = res.items
      return res
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getReservation(id: number) {
    loading.value = true
    error.value = null
    try {
      current.value = await reservationService.get(id)
      return current.value
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createReservation(data: { id_depart: number; places: Array<{ id_depart_place: number; nom_passager: string; telephone_passager?: string }> }) {
    error.value = null
    try {
      const item = await reservationService.create(data)
      items.value.unshift(item)
      return item
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function confirmReservation(id: number) {
    error.value = null
    try {
      const updated = await reservationService.confirm(id)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      if (current.value?.id === id) current.value = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  async function cancelReservation(id: number) {
    error.value = null
    try {
      const updated = await reservationService.cancel(id)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = updated
      if (current.value?.id === id) current.value = updated
      return updated
    } catch (err) {
      error.value = err
      throw err
    }
  }

  return { items, current, loading, error, listReservations, getReservation, createReservation, confirmReservation, cancelReservation }
})
