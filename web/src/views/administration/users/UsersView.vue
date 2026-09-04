<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../../../components/layout/AppLayout.vue'
import BaseCard from '../../../components/ui/BaseCard.vue'
import ListToolbar from '../../../components/ui/ListToolbar.vue'
import { userService } from '../../../services/user/service'
import { userError } from '../../../utils/errors'
import type { User } from '../../../models/user/model'

const users = ref<User[]>([])
const route = useRoute()
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const search = ref('')
const sortBy = ref('created_at')
const sortOrder = ref<'asc' | 'desc'>('desc')
const loading = ref(true)
const error = ref('')
const success = ref('')
const busyAction = ref<string | null>(null)

function roleLabel(user: User) {
  return user.roles?.length ? user.roles.map(role => role.libelle.toUpperCase()).join(', ') : user.role.toUpperCase()
}

function showError(errorValue: unknown, fallback: string) {
  error.value = userError(errorValue, fallback, 'USERS_ERROR')
  success.value = ''
}

async function load() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const result = await userService.list({
      page: page.value,
      page_size: 20,
      search: search.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    })
    users.value = result.items
    total.value = result.total
    pages.value = result.pages || 1
  } catch (errorValue: unknown) {
    showError(errorValue, 'Impossible de charger les utilisateurs.')
  } finally {
    loading.value = false
  }
}

async function toggle(user: User) {
  const key = `toggle-${user.id}`
  if (busyAction.value) return
  busyAction.value = key
  error.value = ''
  try {
    Object.assign(user, await userService.toggle(user.id))
    success.value = 'Statut utilisateur mis à jour.'
  } catch (errorValue: unknown) {
    showError(errorValue, 'Modification du statut impossible.')
  } finally {
    busyAction.value = null
  }
}

async function remove(user: User) {
  if (!window.confirm(`Supprimer l’utilisateur « ${user.first_name || ''} ${user.name} » ?`)) return
  const key = `delete-${user.id}`
  if (busyAction.value) return
  busyAction.value = key
  error.value = ''
  try {
    await userService.delete(user.id)
    users.value = users.value.filter(item => item.id !== user.id)
    total.value = Math.max(0, total.value - 1)
    success.value = 'Utilisateur supprimé.'
  } catch (errorValue: unknown) {
    showError(errorValue, 'Suppression de l’utilisateur impossible.')
  } finally {
    busyAction.value = null
  }
}

function changeSort(column: string) {
  sortOrder.value = sortBy.value === column && sortOrder.value === 'asc' ? 'desc' : 'asc'
  sortBy.value = column
  void load()
}

function changePage(next: number) {
  if (next >= 1 && next <= pages.value) {
    page.value = next
    void load()
  }
}

onMounted(async () => {
  await load()
  if (typeof route.query.success === 'string') success.value = route.query.success
})
</script>

<template>
  <AppLayout>
    <template #title>Utilisateurs</template>

    <div class="page-intro">
      <div>
        <p class="eyebrow">ADMINISTRATION</p>
        <h2>Utilisateurs</h2>
        <p>Consultez et gérez les comptes utilisateurs.</p>
      </div>
      <RouterLink class="primary-button compact-button" to="/users/new">+ Ajouter</RouterLink>
    </div>

    <BaseCard>
      <div class="card-heading"><div><h2>Utilisateurs enregistrés ({{ total }})</h2><p>Consultez les informations détaillées et gérez les comptes.</p></div></div>
      <ListToolbar v-model="search" :loading="loading" placeholder="Rechercher par nom ou email" sort-label="Trier" @search="page = 1; load()" @sort="changeSort('name')" />
      <p v-if="loading" class="status-msg" role="status">Chargement des utilisateurs…</p>
      <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
      <p v-if="success" class="success-banner" role="status">{{ success }}</p>

      <div v-if="!loading && !error" class="table-scroll">
        <table class="data-table">
          <caption>Liste des utilisateurs enregistrés</caption>
          <thead><tr><th><button class="sort-button" type="button" @click="changeSort('name')">Utilisateur ↕</button></th><th>Email</th><th>Rôles</th><th><button class="sort-button" type="button" @click="changeSort('is_active')">Statut ↕</button></th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td><strong>{{ user.first_name }} {{ user.name }}</strong></td>
              <td>{{ user.email }}</td>
              <td><span class="module-badge">{{ roleLabel(user) }}</span></td>
              <td><span :class="['status-badge', user.is_active ? 'active' : 'inactive']">{{ user.is_active ? 'Actif' : 'Inactif' }}</span></td>
              <td>
                <RouterLink class="table-action table-link" :to="`/users/${user.id}`">Détails</RouterLink>
                <RouterLink class="table-action table-link" :to="`/users/${user.id}/edit`">Modifier</RouterLink>
                <button class="table-action" :disabled="busyAction !== null" @click="toggle(user)">{{ busyAction === `toggle-${user.id}` ? 'Traitement…' : (user.is_active ? 'Désactiver' : 'Activer') }}</button>
                <button class="table-action danger-action" :disabled="busyAction !== null" @click="remove(user)">{{ busyAction === `delete-${user.id}` ? 'Suppression…' : 'Supprimer' }}</button>
              </td>
            </tr>
            <tr v-if="!users.length"><td colspan="5"><div class="empty-state">Aucun utilisateur trouvé.</div></td></tr>
          </tbody>
        </table>
      </div>

      <div v-if="!loading && !error" class="pagination">
        <button class="secondary-button" :disabled="page <= 1 || busyAction !== null" @click="changePage(page - 1)">Précédent</button>
        <span>Page {{ page }} / {{ pages || 1 }} · {{ total }} utilisateur(s)</span>
        <button class="secondary-button" :disabled="page >= pages || busyAction !== null" @click="changePage(page + 1)">Suivant</button>
      </div>
    </BaseCard>
  </AppLayout>
</template>
