import { api } from '../api'
import type { Tarif, TarifCreate } from '../../models/tarif/model'

export const tarifService = {
  async list(params?: Record<string, any>) { return (await api.get('/tarifs', { params })).data },
  async get(id: number): Promise<Tarif> { return (await api.get(`/tarifs/${id}`)).data },
  async create(data: TarifCreate): Promise<Tarif> { return (await api.post('/tarifs', data)).data },
  async update(id: number, data: Partial<Tarif>): Promise<Tarif> { return (await api.put(`/tarifs/${id}`, data)).data },
  async toggle(id: number): Promise<Tarif> { return (await api.patch(`/tarifs/${id}/toggle`)).data },
  async remove(id: number) { await api.delete(`/tarifs/${id}`) },
  async history(itineraireId: number): Promise<Tarif[]> { return (await api.get(`/tarifs/history/${itineraireId}`)).data },
}
