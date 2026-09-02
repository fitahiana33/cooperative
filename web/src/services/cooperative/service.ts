import { api } from '../api'
import type { Cooperative, CooperativeCreate } from '../../models/cooperative/model'

export const cooperativeService = {
  async listCooperatives(params?: Record<string, any>) {
    return (await api.get('/cooperatives', { params })).data
  },
  async getCooperative(id: number): Promise<Cooperative> {
    return (await api.get<Cooperative>(`/cooperatives/${id}`)).data
  },
  async createCooperative(data: CooperativeCreate): Promise<Cooperative> {
    return (await api.post<Cooperative>('/cooperatives', data)).data
  },
  async updateCooperative(id: number, data: Partial<CooperativeCreate>): Promise<Cooperative> {
    return (await api.put<Cooperative>(`/cooperatives/${id}`, data)).data
  },
  async toggleCooperative(id: number): Promise<Cooperative> {
    return (await api.patch<Cooperative>(`/cooperatives/${id}/toggle`)).data
  },
  async deleteCooperative(id: number): Promise<void> {
    await api.delete(`/cooperatives/${id}`)
  },
  async attachToGare(cooperativeId: number, gareId: number) {
    return (await api.post(`/cooperatives/${cooperativeId}/attach-gare/${gareId}`)).data
  },
  async addMember(cooperativeId: number, data: { id_user: number; fonction?: string }) {
    return (await api.post(`/cooperatives/${cooperativeId}/members`, data)).data
  },
}
