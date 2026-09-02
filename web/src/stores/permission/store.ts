import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Permission, PermissionCreate } from '../../models/permission/model'
import { permissionService } from '../../services/permission/service'

export const usePermissionStore = defineStore('permission', () => {
  const permissions = ref<Permission[]>([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchPermissions(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await permissionService.listPermissions(params)
      permissions.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function createPermission(data: PermissionCreate) {
    const newPerm = await permissionService.createPermission(data)
    permissions.value.unshift(newPerm)
    return newPerm
  }

  async function updatePermission(id: number, data: Partial<PermissionCreate>) {
    const updated = await permissionService.updatePermission(id, data)
    const idx = permissions.value.findIndex((p) => p.id === id)
    if (idx !== -1) permissions.value[idx] = updated
    return updated
  }

  async function deletePermission(id: number) {
    await permissionService.deletePermission(id)
    permissions.value = permissions.value.filter((p) => p.id !== id)
  }

  return { permissions, total, loading, fetchPermissions, createPermission, updatePermission, deletePermission }
})
