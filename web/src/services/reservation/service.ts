import type { Page } from "../pagination";
import { api } from '../api'
import type { DepartPlace, PublicReservationCreate, PublicReservationResult, Reservation, ReservationPlaceInput } from '../../models/reservation/model'

export interface BookingPolicy {
  max_seats: number; max_pending: number; hold_minutes: number; cancellation_deadline_minutes: number;
  booking_close_minutes: number;
  deposit_rate: number; minimum_deposit_amount: number; online_payment_enabled: boolean; boarding_requires_full_payment: boolean;
}
export const reservationService = {
  async publicPendingOnline(number: string, token: string): Promise<import("../../models/finance/model").OnlinePayment | null> { return (await api.get(`/reservations/public/${encodeURIComponent(number)}/paiement`, { headers: { "X-Reservation-Token": token } })).data },
  async policy(): Promise<BookingPolicy> { return (await api.get('/reservations/policy')).data },
  async publicPay(number: string, token: string, data: { montant: number; cle_idempotence: string; fournisseur: string; telephone_paiement: string }): Promise<import('../../models/finance/model').OnlinePayment> {
    return (await api.post(`/reservations/public/${encodeURIComponent(number)}/paiement`, data,
      { headers: { 'X-Reservation-Token': token }, timeout: 30000 })).data
  },
  async list(params?: Record<string, unknown>): Promise<Page<Reservation>> { return (await api.get('/reservations', { params })).data },
  async exportCsv(params?: Record<string, unknown>): Promise<Blob> { return (await api.get('/reservations/export.csv', { params, responseType: 'blob', timeout: 60000 })).data },
  async exportManifest(departId: number): Promise<Blob> { return (await api.get(`/departs/${departId}/manifest.csv`, { responseType: 'blob', timeout: 60000 })).data },
  async get(id: number): Promise<Reservation> { return (await api.get(`/reservations/${id}`)).data },
  async places(departId: number, availableOnly = false): Promise<DepartPlace[]> { return (await api.get(`/departs/${departId}/places`, { params: { available_only: availableOnly } })).data },
  async publicPlaces(departId: number): Promise<DepartPlace[]> { return (await api.get(`/reservations/public/departs/${departId}/places`)).data },
  async publicCreate(data: PublicReservationCreate): Promise<PublicReservationResult> { return (await api.post('/reservations/public', data)).data },
  async publicCancel(number: string, token: string): Promise<Reservation> {
    return (await api.post(`/reservations/public/${encodeURIComponent(number)}/cancel`, null, { headers: { 'X-Reservation-Token': token } })).data
  },
  async publicGet(number: string, token: string): Promise<Reservation> { return (await api.get(`/reservations/public/${encodeURIComponent(number)}`, { headers: { "X-Reservation-Token": token } })).data },
  async create(data: { id_depart: number; places: ReservationPlaceInput[] }): Promise<Reservation> { return (await api.post('/reservations', data)).data },
  async update(id: number, data: { id_depart: number; places: ReservationPlaceInput[] }): Promise<Reservation> { return (await api.patch(`/reservations/${id}`, data)).data },
  // Counter sale by staff: books, confirms and, when a cash desk is given, takes the cash payment.
  async counterSale(data: { id_depart: number; places: ReservationPlaceInput[]; id_caisse?: number | null }): Promise<Reservation> { return (await api.post('/reservations/guichet', data)).data },
  async confirm(id: number): Promise<Reservation> { return (await api.post(`/reservations/${id}/confirm`)).data },
  async cancel(id: number, idCaisse?: number): Promise<Reservation> {
    return (await api.post(`/reservations/${id}/cancel`, null, { params: idCaisse ? { id_caisse: idCaisse } : undefined })).data
  },
  async updatePlace(id: number, statut: string): Promise<DepartPlace> { return (await api.patch(`/depart-places/${id}`, { statut })).data },
}
