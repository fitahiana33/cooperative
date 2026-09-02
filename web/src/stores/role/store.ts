import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Role, RoleCreate } from '../../models/role/model'
import { roleService } from '../../services/role/service'

export const useRoleStore = defineStore('role', () => {
  const roles = ref<Role[]>([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchRoles(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await roleService.listRoles(params)
      roles.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function createRole(data: RoleCreate) {
    const newRole = await roleService.createRole(data)
    roles.value.unshift(newRole)
    return newRole
  }

  async function updateRole(id: number, data: Partial<RoleCreate>) {
    const updated = await roleService.updateRole(id, data)
    const idx = roles.value.findIndex((r) => r.id === id)
    if (idx !== -1) roles.value[idx] = updated
    return updated
  }

  async function toggleRole(id: number) {
    const updated = await roleService.toggleRole(id)
    const idx = roles.value.findIndex((r) => r.id === id)
    if (idx !== -1) roles.value[idx] = updated
    return updated
  }

  async function deleteRole(id: number) {
    await roleService.deleteRole(id)
    roles.value = roles.value.filter((r) => r.id !== id)
  }

  return { roles, total, loading, fetchRoles, createRole, updateRole, toggleRole, deleteRole }
})
