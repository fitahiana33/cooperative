import { api } from '../api'
import type { Caisse, Paiement } from '../../models/finance/model'

export const financeService = {
  async caisses(params?: Record<string, unknown>) { return (await api.get('/caisses', { params })).data },
  async open(data: { id_gare: number; montant_ouverture: number }): Promise<Caisse> { return (await api.post('/caisses', data)).data },
  async close(id: number, montant_cloture?: number): Promise<Caisse> { return (await api.post(`/caisses/${id}/cloturer`, { montant_cloture })).data },
  async operations(id: number, data: Record<string, unknown>) { return (await api.post(`/caisses/${id}/operations`, data)).data },
  async payments(params?: Record<string, unknown>) { return (await api.get('/paiements', { params })).data },
  async pay(data: { id_reservation: number; id_caisse: number; montant: number; reference_paiement?: string }): Promise<Paiement> { return (await api.post('/paiements', data)).data },
  async refund(id: number, idCaisse: number): Promise<Paiement> { return (await api.post(`/paiements/${id}/rembourser`, null, { params: { id_caisse: idCaisse } })).data },
}
