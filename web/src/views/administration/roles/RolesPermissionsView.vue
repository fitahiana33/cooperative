<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppLayout from '../../../components/layout/AppLayout.vue'
import BaseCard from '../../../components/ui/BaseCard.vue'
import ListToolbar from '../../../components/ui/ListToolbar.vue'
import { roleService } from '../../../services/role/service'
import { permissionService } from '../../../services/permission/service'
import { userService } from '../../../services/user/service'
import type { Role } from '../../../models/role/model'
import type { Permission } from '../../../models/permission/model'
import type { User } from '../../../models/user/model'
import { userError } from '../../../utils/errors'

type Tab = 'roles' | 'permissions'
const activeTab = ref<Tab>('roles')
const roles = ref<Role[]>([])
const permissions = ref<Permission[]>([])
const users = ref<User[]>([])
const selectedRoleId = ref(0)
const selectedUserId = ref(0)
const assignedPermissionIds = ref<number[]>([])
const loading = ref(true)
const saving = ref(false)
const busyAction = ref<string | null>(null)
const error = ref('')
const success = ref('')
const search = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const listPage = ref(1)
const pageSize = 20
const editingRole = ref<Role | null>(null)
const editingPermission = ref<Permission | null>(null)
const roleForm = ref({ libelle: '', description: '' })
const permissionForm = ref({ code: '', libelle: '', module: '', description: '' })

const selectedRole = computed(() => roles.value.find(item => item.id === selectedRoleId.value))
const selectedUser = computed(() => users.value.find(item => item.id === selectedUserId.value))
const filteredRoles = computed(() => roles.value.filter(item => `${item.libelle} ${item.description || ''}`.toLowerCase().includes(search.value.toLowerCase())).sort((a, b) => sortOrder.value === 'asc' ? a.libelle.localeCompare(b.libelle) : b.libelle.localeCompare(a.libelle)))
const filteredPermissions = computed(() => permissions.value.filter(item => `${item.code} ${item.libelle} ${item.module}`.toLowerCase().includes(search.value.toLowerCase())).sort((a, b) => sortOrder.value === 'asc' ? a.code.localeCompare(b.code) : b.code.localeCompare(a.code)))
const visibleRoles = computed(() => filteredRoles.value.slice((listPage.value - 1) * pageSize, listPage.value * pageSize))
const visiblePermissions = computed(() => filteredPermissions.value.slice((listPage.value - 1) * pageSize, listPage.value * pageSize))
const listPages = computed(() => Math.max(1, Math.ceil((activeTab.value === 'roles' ? filteredRoles.value.length : filteredPermissions.value.length) / pageSize)))

function showError(errorValue: unknown, fallback: string) { error.value = userError(errorValue, fallback, 'ROLES_PERMISSIONS_ERROR'); success.value = '' }
function changeListPage(next: number) { if (next >= 1 && next <= listPages.value) listPage.value = next }
function changeTab(tab: Tab) { activeTab.value = tab; search.value = ''; listPage.value = 1 }
function toggleSort() { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'; listPage.value = 1 }
function selectRole(id: number) { selectedRoleId.value = id; void loadRolePermissions() }
function hasPermission(id: number) { return assignedPermissionIds.value.includes(id) }
function userHasRole(roleId: number) { return selectedUser.value?.roles?.some(role => role.id === roleId) || false }

async function loadRolePermissions() {
  if (!selectedRoleId.value) { assignedPermissionIds.value = []; return }
  try {
    const items = await roleService.listRolePermissions(selectedRoleId.value)
    assignedPermissionIds.value = items.map(item => item.id)
  } catch (errorValue: unknown) { showError(errorValue, 'Impossible de charger les permissions du rôle.') }
}
async function load() {
  loading.value = true; error.value = ''; success.value = ''
  try {
    const [rolePage, permissionPage, userPage] = await Promise.all([
      roleService.listRoles({ page: 1, page_size: 100, sort_by: 'libelle', sort_order: 'asc' }),
      permissionService.listPermissions({ page: 1, page_size: 100, sort_by: 'code', sort_order: 'asc' }),
      userService.list({ page: 1, page_size: 100, sort_by: 'name', sort_order: 'asc' }),
    ])
    roles.value = rolePage.items; permissions.value = permissionPage.items; users.value = userPage.items
    if (!selectedRoleId.value && roles.value.length) selectedRoleId.value = roles.value[0].id
    if (!selectedUserId.value && users.value.length) selectedUserId.value = users.value[0].id
    await loadRolePermissions()
  } catch (errorValue: unknown) { showError(errorValue, 'Impossible de charger les rôles, permissions et utilisateurs.') }
  finally { loading.value = false }
}

async function saveRole() {
  if (saving.value || !roleForm.value.libelle.trim()) return
  saving.value = true; error.value = ''
  try {
    if (editingRole.value) Object.assign(editingRole.value, await roleService.updateRole(editingRole.value.id, roleForm.value))
    else { const created = await roleService.createRole(roleForm.value); roles.value.push(created); selectedRoleId.value = created.id }
    editingRole.value = null; roleForm.value = { libelle: '', description: '' }; success.value = 'Rôle enregistré avec succès.'
  } catch (errorValue: unknown) { showError(errorValue, 'Enregistrement du rôle impossible.') }
  finally { saving.value = false }
}
function startRoleEdit(role: Role) { editingRole.value = role; roleForm.value = { libelle: role.libelle, description: role.description || '' } }
function cancelRoleEdit() { editingRole.value = null; roleForm.value = { libelle: '', description: '' } }
async function removeRole(role: Role) {
  if (!window.confirm(`Supprimer le rôle « ${role.libelle} » ?`) || busyAction.value) return
  busyAction.value = `role-delete-${role.id}`; error.value = ''
  try { await roleService.deleteRole(role.id); roles.value = roles.value.filter(item => item.id !== role.id); if (selectedRoleId.value === role.id) selectedRoleId.value = roles.value[0]?.id || 0; await loadRolePermissions(); success.value = 'Rôle supprimé.' }
  catch (errorValue: unknown) { showError(errorValue, 'Suppression du rôle impossible.') }
  finally { busyAction.value = null }
}
async function toggleRole(role: Role) {
  if (busyAction.value) return
  busyAction.value = `role-toggle-${role.id}`
  try { Object.assign(role, await roleService.toggleRole(role.id)); success.value = 'Statut du rôle mis à jour.' }
  catch (errorValue: unknown) { showError(errorValue, 'Modification du rôle impossible.') }
  finally { busyAction.value = null }
}
async function togglePermissionForRole(permission: Permission) {
  if (!selectedRoleId.value || busyAction.value) return
  busyAction.value = `permission-role-${permission.id}`
  try {
    if (hasPermission(permission.id)) { await roleService.revokePermission(selectedRoleId.value, permission.id); assignedPermissionIds.value = assignedPermissionIds.value.filter(id => id !== permission.id) }
    else { await roleService.assignPermission(selectedRoleId.value, permission.id); assignedPermissionIds.value.push(permission.id) }
    success.value = 'Attribution des permissions mise à jour.'; error.value = ''
  } catch (errorValue: unknown) { showError(errorValue, 'Attribution de la permission impossible.') }
  finally { busyAction.value = null }
}

async function savePermission() {
  if (saving.value || !permissionForm.value.code.trim() || !permissionForm.value.libelle.trim() || !permissionForm.value.module.trim()) return
  saving.value = true; error.value = ''
  try {
    if (editingPermission.value) Object.assign(editingPermission.value, await permissionService.updatePermission(editingPermission.value.id, permissionForm.value))
    else permissions.value.push(await permissionService.createPermission(permissionForm.value))
    editingPermission.value = null; permissionForm.value = { code: '', libelle: '', module: '', description: '' }; success.value = 'Permission enregistrée avec succès.'
  } catch (errorValue: unknown) { showError(errorValue, 'Enregistrement de la permission impossible.') }
  finally { saving.value = false }
}
function startPermissionEdit(permission: Permission) { editingPermission.value = permission; permissionForm.value = { code: permission.code, libelle: permission.libelle, module: permission.module, description: permission.description || '' } }
function cancelPermissionEdit() { editingPermission.value = null; permissionForm.value = { code: '', libelle: '', module: '', description: '' } }
async function togglePermission(permission: Permission) {
  if (busyAction.value) return
  busyAction.value = `permission-toggle-${permission.id}`
  try { Object.assign(permission, await permissionService.togglePermission(permission.id)); success.value = 'Statut de la permission mis à jour.' }
  catch (errorValue: unknown) { showError(errorValue, 'Modification de la permission impossible.') }
  finally { busyAction.value = null }
}
async function removePermission(permission: Permission) {
  if (!window.confirm(`Supprimer la permission « ${permission.code} » ?`) || busyAction.value) return
  busyAction.value = `permission-delete-${permission.id}`
  try { await permissionService.deletePermission(permission.id); permissions.value = permissions.value.filter(item => item.id !== permission.id); assignedPermissionIds.value = assignedPermissionIds.value.filter(id => id !== permission.id); success.value = 'Permission supprimée.' }
  catch (errorValue: unknown) { showError(errorValue, 'Suppression de la permission impossible.') }
  finally { busyAction.value = null }
}
async function assignRoleToUser(roleId: number) {
  if (!selectedUserId.value || busyAction.value) return
  busyAction.value = `user-role-${roleId}`
  try { const updated = await userService.assignRole(selectedUserId.value, roleId); const index = users.value.findIndex(item => item.id === updated.id); if (index >= 0) users.value[index] = updated; success.value = 'Rôle attribué à l’utilisateur.' }
  catch (errorValue: unknown) { showError(errorValue, 'Attribution du rôle impossible.') }
  finally { busyAction.value = null }
}
async function revokeRoleFromUser(roleId: number) {
  if (!selectedUserId.value || busyAction.value) return
  busyAction.value = `user-role-${roleId}`
  try { const updated = await userService.revokeRole(selectedUserId.value, roleId); const index = users.value.findIndex(item => item.id === updated.id); if (index >= 0) users.value[index] = updated; success.value = 'Rôle retiré de l’utilisateur.' }
  catch (errorValue: unknown) { showError(errorValue, 'Retrait du rôle impossible.') }
  finally { busyAction.value = null }
}
onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>Rôles & permissions</template>
    <div class="page-intro"><div><p class="eyebrow">ADMINISTRATION</p><h2>Rôles & permissions</h2><p>Gérez les droits et les attributions sans quitter cette page.</p></div></div>
    <div class="section-links admin-tabs"><button type="button" :class="{ active: activeTab === 'roles' }" @click="changeTab('roles')">Rôles</button><button type="button" :class="{ active: activeTab === 'permissions' }" @click="changeTab('permissions')">Permissions</button></div>
    <p v-if="loading" class="status-msg" role="status">Chargement des données…</p><p v-else-if="error" class="error-banner" role="alert">{{ error }}</p><p v-if="success" class="success-banner" role="status">{{ success }}</p>
    <template v-if="!loading">
      <ListToolbar v-model="search" :loading="busyAction !== null" :placeholder="activeTab === 'roles' ? 'Rechercher un rôle' : 'Rechercher une permission'" :sort-label="sortOrder === 'asc' ? 'Tri croissant ↑' : 'Tri décroissant ↓'" @search="listPage = 1" @sort="toggleSort" />
      <template v-if="activeTab === 'roles'">
        <BaseCard><div class="card-heading"><div><h2>{{ editingRole ? 'Modifier le rôle' : 'Créer un rôle' }}</h2><p>Définissez un profil d’accès.</p></div></div><form class="management-form inline-form" @submit.prevent="saveRole"><input v-model="roleForm.libelle" required placeholder="Libellé du rôle" /><input v-model="roleForm.description" placeholder="Description" /><button class="primary-button compact-button" type="submit" :disabled="saving">{{ saving ? 'Enregistrement…' : (editingRole ? 'Modifier' : 'Créer') }}</button><button v-if="editingRole" class="secondary-button" type="button" :disabled="saving" @click="cancelRoleEdit">Annuler</button></form></BaseCard>
        <BaseCard><div class="card-heading"><div><h2>Rôles ({{ filteredRoles.length }})</h2><p>Activez, modifiez ou supprimez les rôles.</p></div></div><div class="table-scroll"><table class="data-table"><caption>Liste des rôles</caption><thead><tr><th>Libellé</th><th>Description</th><th>Statut</th><th>Actions</th></tr></thead><tbody><tr v-for="role in visibleRoles" :key="role.id"><td><strong>{{ role.libelle.toUpperCase() }}</strong></td><td>{{ role.description || '—' }}</td><td><span :class="['status-badge', role.is_active ? 'active' : 'inactive']">{{ role.is_active ? 'Actif' : 'Inactif' }}</span></td><td><button class="table-action" :disabled="busyAction !== null" @click="selectRole(role.id)">Permissions</button><button class="table-action" :disabled="busyAction !== null" @click="startRoleEdit(role)">Modifier</button><button class="table-action" :disabled="busyAction !== null" @click="toggleRole(role)">{{ busyAction === `role-toggle-${role.id}` ? 'Traitement…' : (role.is_active ? 'Désactiver' : 'Activer') }}</button><button class="table-action danger-action" :disabled="busyAction !== null" @click="removeRole(role)">{{ busyAction === `role-delete-${role.id}` ? 'Suppression…' : 'Supprimer' }}</button></td></tr><tr v-if="!visibleRoles.length"><td colspan="4"><div class="empty-state">Aucun rôle trouvé.</div></td></tr></tbody></table></div><div class="pagination"><button class="secondary-button" :disabled="listPage <= 1 || busyAction !== null" @click="changeListPage(listPage - 1)">Précédent</button><span>Page {{ listPage }} / {{ listPages }} · {{ filteredRoles.length }} rôle(s)</span><button class="secondary-button" :disabled="listPage >= listPages || busyAction !== null" @click="changeListPage(listPage + 1)">Suivant</button></div></BaseCard>
        <BaseCard><div class="card-heading"><div><h2>Permissions du rôle {{ selectedRole?.libelle || '—' }}</h2><p>Cochez les permissions à attribuer.</p></div><select class="assignment-select" v-model.number="selectedRoleId" @change="loadRolePermissions"><option :value="0">Choisir un rôle</option><option v-for="role in roles" :key="role.id" :value="role.id">{{ role.libelle }}</option></select></div><div class="permission-check-grid"><label v-for="permission in permissions" :key="permission.id" class="permission-check"><input type="checkbox" :disabled="busyAction !== null" :checked="hasPermission(permission.id)" @change="togglePermissionForRole(permission)" /><span><strong>{{ permission.code }}</strong><small>{{ permission.libelle }} · {{ permission.module }}</small></span></label></div><div v-if="!permissions.length" class="empty-state">Aucune permission disponible.</div></BaseCard>
        <BaseCard><div class="card-heading"><div><h2>Rôles des utilisateurs</h2><p>Attribuez ou retirez un rôle à un utilisateur.</p></div><select class="assignment-select" v-model.number="selectedUserId"><option :value="0">Choisir un utilisateur</option><option v-for="user in users" :key="user.id" :value="user.id">{{ user.first_name }} {{ user.name }} — {{ user.email }}</option></select></div><div v-if="selectedUser" class="role-assignment-grid"><div v-for="role in roles" :key="role.id" class="role-assignment"><span>{{ role.libelle }}</span><button class="table-action" type="button" :disabled="busyAction !== null" @click="userHasRole(role.id) ? revokeRoleFromUser(role.id) : assignRoleToUser(role.id)">{{ busyAction === `user-role-${role.id}` ? 'Traitement…' : (userHasRole(role.id) ? 'Retirer' : 'Attribuer') }}</button></div></div><div v-else class="empty-state">Sélectionnez un utilisateur.</div></BaseCard>
      </template>
      <template v-else>
        <BaseCard><div class="card-heading"><div><h2>{{ editingPermission ? 'Modifier la permission' : 'Créer une permission' }}</h2><p>Déclarez une permission exploitable dans les contrôles d’accès.</p></div></div><form class="management-form inline-form" @submit.prevent="savePermission"><input v-model="permissionForm.code" required placeholder="Code (ex. GARE_READ)" /><input v-model="permissionForm.libelle" required placeholder="Libellé" /><input v-model="permissionForm.module" required placeholder="Module" /><input v-model="permissionForm.description" placeholder="Description" /><button class="primary-button compact-button" type="submit" :disabled="saving">{{ saving ? 'Enregistrement…' : (editingPermission ? 'Modifier' : 'Créer') }}</button><button v-if="editingPermission" class="secondary-button" type="button" :disabled="saving" @click="cancelPermissionEdit">Annuler</button></form></BaseCard>
        <BaseCard><div class="card-heading"><div><h2>Permissions ({{ filteredPermissions.length }})</h2><p>Ces permissions peuvent ensuite être cochées dans l’onglet Rôles.</p></div></div><div class="table-scroll"><table class="data-table"><caption>Liste des permissions</caption><thead><tr><th>Code</th><th>Libellé</th><th>Module</th><th>Statut</th><th>Actions</th></tr></thead><tbody><tr v-for="permission in visiblePermissions" :key="permission.id"><td><strong>{{ permission.code }}</strong></td><td>{{ permission.libelle }}</td><td>{{ permission.module }}</td><td><span :class="['status-badge', permission.is_active ? 'active' : 'inactive']">{{ permission.is_active ? 'Active' : 'Inactive' }}</span></td><td><button class="table-action" :disabled="busyAction !== null" @click="startPermissionEdit(permission)">Modifier</button><button class="table-action" :disabled="busyAction !== null" @click="togglePermission(permission)">{{ busyAction === `permission-toggle-${permission.id}` ? 'Traitement…' : (permission.is_active ? 'Désactiver' : 'Activer') }}</button><button class="table-action danger-action" :disabled="busyAction !== null" @click="removePermission(permission)">{{ busyAction === `permission-delete-${permission.id}` ? 'Suppression…' : 'Supprimer' }}</button></td></tr><tr v-if="!visiblePermissions.length"><td colspan="5"><div class="empty-state">Aucune permission trouvée.</div></td></tr></tbody></table></div><div class="pagination"><button class="secondary-button" :disabled="listPage <= 1 || busyAction !== null" @click="changeListPage(listPage - 1)">Précédent</button><span>Page {{ listPage }} / {{ listPages }} · {{ filteredPermissions.length }} permission(s)</span><button class="secondary-button" :disabled="listPage >= listPages || busyAction !== null" @click="changeListPage(listPage + 1)">Suivant</button></div></BaseCard>
      </template>
    </template>
  </AppLayout>
</template>
