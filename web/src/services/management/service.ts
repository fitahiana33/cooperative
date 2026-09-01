import { api } from '../api'
import type { Cooperative, Gare, Permission, Role } from '../../models/management/model'
type Page<T> = { items: T[]; total: number; page: number; page_size: number; pages: number }
type ListParams = { page?: number; page_size?: number; search?: string; sort_by?: string; sort_order?: 'asc' | 'desc' }

export const managementService = {
  listGares: (params?: ListParams) => api.get<Page<Gare>>('/gares', { params }).then(r => r.data),
  createGare: (data: Omit<Gare, 'id'|'is_active'|'created_at'>) => api.post<Gare>('/gares', data).then(r => r.data),
  getGare: (id: number) => api.get<Gare>(`/gares/${id}`).then(r => r.data),
  toggleGare: (id: number) => api.patch<Gare>(`/gares/${id}/toggle`).then(r => r.data),
  updateGare: (id: number, data: Omit<Gare, 'id'|'is_active'|'created_at'>) => api.put<Gare>(`/gares/${id}`, data).then(r => r.data),
  deleteGare: (id: number) => api.delete(`/gares/${id}`).then(() => undefined),
  listCooperatives: (params?: ListParams) => api.get<Page<Cooperative>>('/cooperatives', { params }).then(r => r.data),
  createCooperative: (data: Omit<Cooperative, 'id'|'is_active'|'created_at'>) => api.post<Cooperative>('/cooperatives', data).then(r => r.data),
  getCooperative: (id: number) => api.get<Cooperative>(`/cooperatives/${id}`).then(r => r.data),
  toggleCooperative: (id: number) => api.patch<Cooperative>(`/cooperatives/${id}/toggle`).then(r => r.data),
  updateCooperative: (id: number, data: Omit<Cooperative, 'id'|'is_active'|'created_at'>) => api.put<Cooperative>(`/cooperatives/${id}`, data).then(r => r.data),
  deleteCooperative: (id: number) => api.delete(`/cooperatives/${id}`).then(() => undefined),
  listRoles: (params?: ListParams) => api.get<Page<Role>>('/roles', { params }).then(r => r.data),
  createRole: (data: Omit<Role, 'id'|'is_active'|'created_at'>) => api.post<Role>('/roles', data).then(r => r.data),
  updateRole: (id: number, data: Omit<Role, 'id'|'is_active'|'created_at'>) => api.put<Role>(`/roles/${id}`, data).then(r => r.data),
  toggleRole: (id: number) => api.patch<Role>(`/roles/${id}/toggle`).then(r => r.data),
  deleteRole: (id: number) => api.delete(`/roles/${id}`).then(() => undefined),
  listPermissions: (params?: ListParams) => api.get<Page<Permission>>('/permissions', { params }).then(r => r.data),
  createPermission: (data: Omit<Permission, 'id'|'is_active'|'created_at'>) => api.post<Permission>('/permissions', data).then(r => r.data),
  updatePermission: (id: number, data: Omit<Permission, 'id'|'is_active'|'created_at'>) => api.put<Permission>(`/permissions/${id}`, data).then(r => r.data),
  deletePermission: (id: number) => api.delete(`/permissions/${id}`).then(() => undefined),
}
