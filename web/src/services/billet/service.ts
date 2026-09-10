import { api } from '../api'
import type { Billet } from '../../models/billet/model'

export const billetService = {
  async list(params?: Record<string, unknown>) { return (await api.get('/billets', { params })).data },
  async get(id: number): Promise<Billet> { return (await api.get(`/billets/${id}`)).data },
  async find(code: string): Promise<Billet> { return (await api.get(`/billets/code/${encodeURIComponent(code)}`)).data },
}
