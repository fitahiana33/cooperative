import { api } from '../api'
import type { Role, RoleCreate } from '../../models/role/model'

export const roleService = {
  async listRoles(params?: Record<string, any>) {
    return (await api.get('/roles', { params })).data
  },
  async createRole(data: RoleCreate): Promise<Role> {
    return (await api.post<Role>('/roles', data)).data
  },
  async updateRole(id: number, data: Partial<RoleCreate>): Promise<Role> {
    return (await api.put<Role>(`/roles/${id}`, data)).data
  },
  async toggleRole(id: number): Promise<Role> {
    return (await api.patch<Role>(`/roles/${id}/toggle`)).data
  },
  async deleteRole(id: number): Promise<void> {
    await api.delete(`/roles/${id}`)
  },
  async assignPermission(roleId: number, permissionId: number): Promise<void> {
    await api.post(`/roles/${roleId}/permissions/${permissionId}`)
  },
  async revokePermission(roleId: number, permissionId: number): Promise<void> {
    await api.delete(`/roles/${roleId}/permissions/${permissionId}`)
  },
  async listRolePermissions(roleId: number) {
    return (await api.get(`/roles/${roleId}/permissions`)).data
  },
}
