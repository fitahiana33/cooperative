import { api } from '../api'
import type { User, UserCreate } from '../../models/user/model'

export const userService = {
  async list(params: { page?: number; page_size?: number; search?: string; sort_by?: string; sort_order?: string } = {}) { return (await api.get<{ items: User[]; total: number; page: number; page_size: number; pages: number }>('/users', { params })).data },
  async create(payload: UserCreate): Promise<User> { return (await api.post<User>('/users', payload)).data },
}


