import { api } from './api'
import type { User, UserCreate } from '../models/user'

export const userService = {
  async list(): Promise<User[]> { return (await api.get<User[]>('/users')).data },
  async create(payload: UserCreate): Promise<User> { return (await api.post<User>('/users', payload)).data },
}

