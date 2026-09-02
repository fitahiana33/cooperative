import { api } from '../api'
import type { Modele, ModeleCreate } from '../../models/modele/model'

export const modeleService = {
  async listModeles(params?: Record<string, any>) {
    return (await api.get('/modeles', { params })).data
  },
  async getModele(id: number): Promise<Modele> {
    return (await api.get<Modele>(`/modeles/${id}`)).data
  },
  async createModele(data: ModeleCreate): Promise<Modele> {
    return (await api.post<Modele>('/modeles', data)).data
  },
  async updateModele(id: number, data: Partial<Modele>): Promise<Modele> {
    return (await api.put<Modele>(`/modeles/${id}`, data)).data
  },
  async toggleModele(id: number): Promise<Modele> {
    return (await api.patch<Modele>(`/modeles/${id}/toggle`)).data
  },
  async deleteModele(id: number): Promise<void> {
    await api.delete(`/modeles/${id}`)
  },
}
