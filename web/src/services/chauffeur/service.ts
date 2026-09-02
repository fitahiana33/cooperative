import { api } from '../api'
import type { Chauffeur, ChauffeurCreate, VehiculeChauffeurAssign } from '../../models/chauffeur/model'

export const chauffeurService = {
  async listChauffeurs(params?: Record<string, any>) {
    return (await api.get('/chauffeurs', { params })).data
  },
  async getChauffeur(id: number): Promise<Chauffeur> {
    return (await api.get<Chauffeur>(`/chauffeurs/${id}`)).data
  },
  async createChauffeur(data: ChauffeurCreate): Promise<Chauffeur> {
    return (await api.post<Chauffeur>('/chauffeurs', data)).data
  },
  async updateChauffeur(id: number, data: Partial<Chauffeur>): Promise<Chauffeur> {
    return (await api.put<Chauffeur>(`/chauffeurs/${id}`, data)).data
  },
  async toggleChauffeur(id: number): Promise<Chauffeur> {
    return (await api.patch<Chauffeur>(`/chauffeurs/${id}/toggle`)).data
  },
  async deleteChauffeur(id: number): Promise<void> {
    await api.delete(`/chauffeurs/${id}`)
  },
  async assignVehicule(chauffeurId: number, data: VehiculeChauffeurAssign) {
    return (await api.post(`/chauffeurs/${chauffeurId}/assign-vehicule`, data)).data
  },
}
