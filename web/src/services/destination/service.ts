import { api } from '../api'
import type { Destination, DestinationCreate } from '../../models/destination/model'

export const destinationService = {
  async list(params?: Record<string, any>) { return (await api.get('/destinations', { params })).data },
  async get(id: number): Promise<Destination> { return (await api.get(`/destinations/${id}`)).data },
  async create(data: DestinationCreate): Promise<Destination> { return (await api.post('/destinations', data)).data },
  async update(id: number, data: Partial<Destination>): Promise<Destination> { return (await api.put(`/destinations/${id}`, data)).data },
  async toggle(id: number): Promise<Destination> { return (await api.patch(`/destinations/${id}/toggle`)).data },
  async remove(id: number) { await api.delete(`/destinations/${id}`) },
}
