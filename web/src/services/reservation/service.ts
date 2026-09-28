import { api } from '../api'
import type { DepartPlace, Reservation, ReservationPlaceInput } from '../../models/reservation/model'

export const reservationService = {
  async list(params?: Record<string, unknown>) { return (await api.get('/reservations', { params })).data },
  async exportCsv(params?: Record<string, unknown>): Promise<Blob> { return (await api.get('/reservations/export.csv', { params, responseType: 'blob' })).data },
  async exportManifest(departId: number): Promise<Blob> { return (await api.get(`/departs/${departId}/manifest.csv`, { responseType: 'blob' })).data },
  async get(id: number): Promise<Reservation> { return (await api.get(`/reservations/${id}`)).data },
  async places(departId: number, availableOnly = false): Promise<DepartPlace[]> { return (await api.get(`/departs/${departId}/places`, { params: { available_only: availableOnly } })).data },
  async create(data: { id_depart: number; places: ReservationPlaceInput[] }): Promise<Reservation> { return (await api.post('/reservations', data)).data },
  async confirm(id: number): Promise<Reservation> { return (await api.post(`/reservations/${id}/confirm`)).data },
  async cancel(id: number, idCaisse?: number): Promise<Reservation> {
    return (await api.post(`/reservations/${id}/cancel`, null, { params: idCaisse ? { id_caisse: idCaisse } : undefined })).data
  },
  async updatePlace(id: number, statut: string): Promise<DepartPlace> { return (await api.patch(`/depart-places/${id}`, { statut })).data },
}
