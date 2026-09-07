import { api } from '../api'
import type { Itineraire, ItineraireCreate, ItineraireCooperative } from '../../models/itineraire/model'

export const itineraireService = {
  async list(params?: Record<string, any>) { return (await api.get('/itineraires', { params })).data },
  async get(id: number): Promise<Itineraire> { return (await api.get(`/itineraires/${id}`)).data },
  async create(data: ItineraireCreate): Promise<Itineraire> { return (await api.post('/itineraires', data)).data },
  async update(id: number, data: Partial<Itineraire>): Promise<Itineraire> { return (await api.put(`/itineraires/${id}`, data)).data },
  async toggle(id: number): Promise<Itineraire> { return (await api.patch(`/itineraires/${id}/toggle`)).data },
  async remove(id: number) { await api.delete(`/itineraires/${id}`) },
  async listCooperatives(id: number): Promise<ItineraireCooperative[]> { return (await api.get(`/itineraires/${id}/cooperatives`)).data },
  async attach(id: number, cooperativeId: number, data?: Record<string, any>): Promise<ItineraireCooperative> { return (await api.post(`/itineraires/${id}/cooperatives/${cooperativeId}`, data || {})).data },
  async detach(id: number, cooperativeId: number) { await api.delete(`/itineraires/${id}/cooperatives/${cooperativeId}`) },
}
