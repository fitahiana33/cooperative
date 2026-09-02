import { api } from '../api'
import type { Permission, PermissionCreate } from '../../models/permission/model'

export const permissionService = {
  async listPermissions(params?: Record<string, any>) {
    return (await api.get('/permissions', { params })).data
  },
  async createPermission(data: PermissionCreate): Promise<Permission> {
    return (await api.post<Permission>('/permissions', data)).data
  },
  async updatePermission(id: number, data: Partial<PermissionCreate>): Promise<Permission> {
    return (await api.put<Permission>(`/permissions/${id}`, data)).data
  },
  async deletePermission(id: number): Promise<void> {
    await api.delete(`/permissions/${id}`)
  },
  async togglePermission(id: number): Promise<Permission> {
    return (await api.patch<Permission>(`/permissions/${id}/toggle`)).data
  },
}
