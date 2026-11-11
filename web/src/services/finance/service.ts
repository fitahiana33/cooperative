import type { Page } from "../pagination";
import { api } from '../api'
import type { Caisse, Paiement } from '../../models/finance/model'

export interface OperationCaisse {
  id: number
  id_caisse: number
  type_operation: string
  montant: number
  id_paiement?: number | null
  id_cooperative?: number | null
  description?: string | null
  date_operation: string
}

export const financeService = {
  async pendingOnline(id: number): Promise<import("../../models/finance/model").OnlinePayment | null> { return (await api.get(`/paiements/en-cours/${id}`)).data },
  async verifyFailure(id: number, reference: string): Promise<Paiement> { return (await api.post(`/paiements/${id}/verification-echec`, { reference_verification: reference })).data },
  async online(data: { id_reservation: number; montant: number; fournisseur: string; cle_idempotence: string; telephone_paiement: string }): Promise<import('../../models/finance/model').OnlinePayment> {
    return (await api.post('/paiements/en-ligne', data, { timeout: 30000 })).data
  },
  async caisses(params?: Record<string, unknown>): Promise<Page<Caisse>> { return (await api.get('/caisses', { params })).data },
  async getCaisse(id: number): Promise<Caisse> { return (await api.get(`/caisses/${id}`)).data },
  async open(data: { id_gare: number; montant_ouverture: number }): Promise<Caisse> { return (await api.post('/caisses', data)).data },
  async close(id: number, montant_cloture?: number): Promise<Caisse> { return (await api.post(`/caisses/${id}/cloturer`, { montant_cloture })).data },
  async listOperations(id: number, params?: Record<string, unknown>) { return (await api.get(`/caisses/${id}/operations`, { params })).data },
  async addOperation(id: number, data: Record<string, unknown>) { return (await api.post(`/caisses/${id}/operations`, data)).data },
  async payments(params?: Record<string, unknown>) { return (await api.get('/paiements', { params })).data },
  async pay(data: { id_reservation: number; id_caisse: number; montant: number; reference_paiement?: string }): Promise<Paiement> { return (await api.post('/paiements', data)).data },
  async refund(id: number, idCaisse?: number, data?: { methode: string; reference?: string }): Promise<Paiement> { return (await api.post(`/paiements/${id}/rembourser`, data || null, { params: { id_caisse: idCaisse } })).data },
}
