import { api } from '../api'
import type { PasswordChange, ProfileUpdate, User, UserCreate, UserUpdate } from '../../models/user/model'

export const userService = {
  async me(): Promise<User> { return (await api.get<User>('/users/me')).data },
  async updateMe(payload: ProfileUpdate): Promise<User> { return (await api.put<User>('/users/me', payload)).data },
  async changePassword(payload: PasswordChange): Promise<void> { await api.post('/users/me/password', payload) },
  async list(params: { page?: number; page_size?: number; search?: string; sort_by?: string; sort_order?: string } = {}) { return (await api.get<{ items: User[]; total: number; page: number; page_size: number; pages: number }>('/users', { params })).data },
  async get(id: number): Promise<User> { return (await api.get<User>(`/users/${id}`)).data },
  async create(payload: UserCreate): Promise<User> { return (await api.post<User>('/users', payload)).data },
  async update(id: number, payload: UserUpdate): Promise<User> { return (await api.put<User>(`/users/${id}`, payload)).data },
  async toggle(id: number): Promise<User> { return (await api.patch<User>(`/users/${id}/toggle`)).data },
  async delete(id: number): Promise<void> { await api.delete(`/users/${id}`) },
  async assignRole(userId: number, roleId: number): Promise<User> { return (await api.post<User>(`/users/${userId}/roles/${roleId}`)).data },
  async revokeRole(userId: number, roleId: number): Promise<User> { return (await api.delete<User>(`/users/${userId}/roles/${roleId}`)).data },
}
