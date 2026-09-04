import { api } from '../api'
import type { Vehicule, VehiculeCreate, VehiculeDocument } from '../../models/vehicule/model'

export const vehiculeService = {
  async listVehicules(params?: Record<string, any>) {
    return (await api.get('/vehicules', { params })).data
  },
  async getVehicule(id: number): Promise<Vehicule> {
    return (await api.get<Vehicule>(`/vehicules/${id}`)).data
  },
  async createVehicule(data: VehiculeCreate): Promise<Vehicule> {
    return (await api.post<Vehicule>('/vehicules', data)).data
  },
  async updateVehicule(id: number, data: Partial<Vehicule>): Promise<Vehicule> {
    return (await api.put<Vehicule>(`/vehicules/${id}`, data)).data
  },
  async toggleVehicule(id: number): Promise<Vehicule> {
    return (await api.patch<Vehicule>(`/vehicules/${id}/toggle`)).data
  },
  async deleteVehicule(id: number): Promise<void> {
    await api.delete(`/vehicules/${id}`)
  },
  async addDocument(vehiculeId: number, data: Partial<VehiculeDocument>): Promise<VehiculeDocument> {
    return (await api.post<VehiculeDocument>(`/vehicules/${vehiculeId}/documents`, data)).data
  },
  async uploadDocument(vehiculeId: number, data: FormData): Promise<VehiculeDocument> {
    return (await api.post<VehiculeDocument>(`/vehicules/${vehiculeId}/documents/upload`, data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })).data
  },
  async toggleDocument(documentId: number): Promise<VehiculeDocument> {
    return (await api.patch<VehiculeDocument>(`/vehicules/documents/${documentId}/toggle`)).data
  },
  async deleteDocument(documentId: number): Promise<void> {
    await api.delete(`/vehicules/documents/${documentId}`)
  },
  async downloadDocument(documentId: number): Promise<Blob> {
    return (await api.get<Blob>(`/vehicules/documents/${documentId}/download`, {
      responseType: 'blob',
    })).data
  },
}
