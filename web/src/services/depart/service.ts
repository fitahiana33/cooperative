import { api } from '../api'
import type { Depart, DepartCreate, DepartStatus } from '../../models/depart/model'

export const departService = {
  async list(params?: Record<string, unknown>) {
    return (await api.get('/departs', { params })).data
  },
  async get(id: number): Promise<Depart> {
    return (await api.get<Depart>(`/departs/${id}`)).data
  },
  async create(data: DepartCreate): Promise<Depart> {
    return (await api.post<Depart>('/departs', data)).data
  },
  async update(id: number, data: Partial<DepartCreate>): Promise<Depart> {
    return (await api.put<Depart>(`/departs/${id}`, data)).data
  },
  async updateStatus(id: number, statut: DepartStatus): Promise<Depart> {
    return (await api.patch<Depart>(`/departs/${id}/status`, { statut })).data
  },
  async cancel(id: number): Promise<Depart> {
    return (await api.post<Depart>(`/departs/${id}/cancel`)).data
  },
}
