import { api } from '../api'
import type { Gare, GareCreate } from '../../models/gare/model'

export const gareService = {
  async listGares(params?: Record<string, any>) {
    return (await api.get('/gares', { params })).data
  },
  async getGare(id: number): Promise<Gare> {
    return (await api.get<Gare>(`/gares/${id}`)).data
  },
  async createGare(data: GareCreate): Promise<Gare> {
    return (await api.post<Gare>('/gares', data)).data
  },
  async updateGare(id: number, data: Partial<GareCreate>): Promise<Gare> {
    return (await api.put<Gare>(`/gares/${id}`, data)).data
  },
  async toggleGare(id: number): Promise<Gare> {
    return (await api.patch<Gare>(`/gares/${id}/toggle`)).data
  },
  async deleteGare(id: number): Promise<void> {
    await api.delete(`/gares/${id}`)
  },
  async addQuai(gareId: number, data: { numero: string; nom?: string; description?: string }) {
    return (await api.post(`/gares/${gareId}/quais`, data)).data
  },
  async addZone(gareId: number, data: { nom: string; type_zone?: string; description?: string }) {
    return (await api.post(`/gares/${gareId}/zones`, data)).data
  },
  async addEmplacement(zoneId: number, data: { code: string; nom?: string; type_emplacement?: string; description?: string }) {
    return (await api.post(`/gares/zones/${zoneId}/emplacements`, data)).data
  },
  async toggleQuai(gareId: number, quaiId: number) {
    return (await api.patch(`/gares/${gareId}/quais/${quaiId}/toggle`)).data
  },
  async deleteQuai(gareId: number, quaiId: number): Promise<void> {
    await api.delete(`/gares/${gareId}/quais/${quaiId}`)
  },
  async toggleZone(gareId: number, zoneId: number) {
    return (await api.patch(`/gares/${gareId}/zones/${zoneId}/toggle`)).data
  },
  async deleteZone(gareId: number, zoneId: number): Promise<void> {
    await api.delete(`/gares/${gareId}/zones/${zoneId}`)
  },
  async toggleEmplacement(gareId: number, zoneId: number, emplacementId: number) {
    return (await api.patch(`/gares/${gareId}/zones/${zoneId}/emplacements/${emplacementId}/toggle`)).data
  },
  async deleteEmplacement(gareId: number, zoneId: number, emplacementId: number): Promise<void> {
    await api.delete(`/gares/${gareId}/zones/${zoneId}/emplacements/${emplacementId}`)
  },
}
