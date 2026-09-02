import { api } from '../api'
import type { Marque, MarqueCreate } from '../../models/marque/model'

export const marqueService = {
  async listMarques(params?: Record<string, any>) {
    return (await api.get('/marques', { params })).data
  },
  async getMarque(id: number): Promise<Marque> {
    return (await api.get<Marque>(`/marques/${id}`)).data
  },
  async createMarque(data: MarqueCreate): Promise<Marque> {
    return (await api.post<Marque>('/marques', data)).data
  },
  async updateMarque(id: number, data: Partial<Marque>): Promise<Marque> {
    return (await api.put<Marque>(`/marques/${id}`, data)).data
  },
  async toggleMarque(id: number): Promise<Marque> {
    return (await api.patch<Marque>(`/marques/${id}/toggle`)).data
  },
  async deleteMarque(id: number): Promise<void> {
    await api.delete(`/marques/${id}`)
  },
}
