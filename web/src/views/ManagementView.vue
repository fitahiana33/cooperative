<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '../components/layout/AppLayout.vue'
import BaseCard from '../components/ui/BaseCard.vue'
import ListToolbar from '../components/ui/ListToolbar.vue'
import { managementService } from '../services/management/service'
import type { Cooperative, Gare, Permission, Role } from '../models/management/model'

const route = useRoute()
const section = computed(() => String(route.name || 'gares'))
const isListPage = computed(() => ['gares', 'cooperatives', 'roles'].includes(section.value))

const gares = ref<Gare[]>([])
const cooperatives = ref<Cooperative[]>([])
const roles = ref<Role[]>([])
const permissions = ref<Permission[]>([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const search = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const loading = ref(true)
const error = ref('')
const success = ref('')
const gareSubmitting = ref(false)
const cooperativeSubmitting = ref(false)
const editingGare = ref<Gare | null>(null)
const editingCooperative = ref<Cooperative | null>(null)
const roleSubmitting = ref(false)
const permissionSubmitting = ref(false)
const roleForm = reactive({ libelle: '', description: '' })
const permissionForm = reactive({ code: '', libelle: '', module: '', description: '' })

const gare = reactive({
  nom: '',
  adresse: '',
  ville: '',
  region: '',
  telephone: '',
  email: '',
  description: '',
  latitude: null as number | null,
  longitude: null as number | null,
})

const cooperative = reactive({
  nom: '',
  sigle: '',
  numero_agrement: '',
  adresse: '',
  ville: '',
  telephone: '',
  email: '',
  logo_url: '',
  description: '',
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (section.value === 'gares') {
      const result = await managementService.listGares({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'nom', sort_order: sortOrder.value }); gares.value = result.items; total.value = result.total; pages.value = result.pages || 1
    } else if (section.value === 'cooperatives') {
      const result = await managementService.listCooperatives({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'nom', sort_order: sortOrder.value }); cooperatives.value = result.items; total.value = result.total; pages.value = result.pages || 1
    } else {
      const rolePage = await managementService.listRoles({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'libelle', sort_order: sortOrder.value }); const permissionPage = await managementService.listPermissions({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'code', sort_order: sortOrder.value }); roles.value = rolePage.items; permissions.value = permissionPage.items; total.value = rolePage.total; pages.value = rolePage.pages || 1
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Impossible de charger les données. Vérifiez votre rôle et votre connexion.'
  } finally {
    loading.value = false
  }
}

async function addGare() {
  if (gareSubmitting.value) return
  error.value = ''; success.value = ''; gareSubmitting.value = true
  try {
    const created = await managementService.createGare(gare)
    gares.value.push(created)
    Object.assign(gare, {
      nom: '',
      adresse: '',
      ville: '',
      region: '',
      telephone: '',
      email: '',
      description: '',
      latitude: null,
      longitude: null,
    })
    success.value = 'Gare enregistrée avec succès.'
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Création de la gare impossible.'
  } finally { gareSubmitting.value = false
  }
}

async function addCooperative() {
  if (cooperativeSubmitting.value) return
  error.value = ''; success.value = ''; cooperativeSubmitting.value = true
  try {
    const created = await managementService.createCooperative(cooperative)
    cooperatives.value.push(created)
    Object.assign(cooperative, {
      nom: '',
      sigle: '',
      numero_agrement: '',
      adresse: '',
      ville: '',
      telephone: '',
      email: '',
      logo_url: '',
      description: '',
    })
    success.value = 'Coopérative enregistrée avec succès.'
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Création de la coopérative impossible.'
  } finally { cooperativeSubmitting.value = false
  }
}

async function toggleGare(item: Gare) {
  try {
    error.value = ''
    item.is_active = (await managementService.toggleGare(item.id)).is_active
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Action impossible sur cette gare.'
  }
}

async function toggleCooperative(item: Cooperative) {
  try {
    error.value = ''
    item.is_active = (await managementService.toggleCooperative(item.id)).is_active
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Action impossible sur cette coopérative.'
  }
}

function editGare(item: Gare) { editingGare.value = { ...item } }
function editCooperative(item: Cooperative) { editingCooperative.value = { ...item } }
function cancelEdit() { editingGare.value = null; editingCooperative.value = null }

async function saveGare() {
  if (!editingGare.value) return
  try {
    const updated = await managementService.updateGare(editingGare.value.id, editingGare.value)
    const index = gares.value.findIndex(item => item.id === updated.id)
    if (index >= 0) gares.value[index] = updated
    editingGare.value = null; success.value = 'Gare modifiée avec succès.'; error.value = ''
  } catch (e: any) { error.value = e?.response?.data?.detail || 'Modification de la gare impossible.' }
}

async function removeGare(item: Gare) {
  if (!window.confirm(`Supprimer la gare « ${item.nom} » ?`)) return
  try { await managementService.deleteGare(item.id); await load(); success.value = 'Gare supprimée avec succès.'; error.value = '' }
  catch (e: any) { error.value = e?.response?.data?.detail || 'Suppression de la gare impossible.' }
}

async function saveCooperative() {
  if (!editingCooperative.value) return
  try {
    const updated = await managementService.updateCooperative(editingCooperative.value.id, editingCooperative.value)
    const index = cooperatives.value.findIndex(item => item.id === updated.id)
    if (index >= 0) cooperatives.value[index] = updated
    editingCooperative.value = null; success.value = 'Coopérative modifiée avec succès.'; error.value = ''
  } catch (e: any) { error.value = e?.response?.data?.detail || 'Modification de la coopérative impossible.' }
}

async function removeCooperative(item: Cooperative) {
  if (!window.confirm(`Supprimer la coopérative « ${item.nom} » ?`)) return
  try { await managementService.deleteCooperative(item.id); await load(); success.value = 'Coopérative supprimée avec succès.'; error.value = '' }
  catch (e: any) { error.value = e?.response?.data?.detail || 'Suppression de la coopérative impossible.' }
}

async function addRole() {
  if (roleSubmitting.value || !roleForm.libelle.trim()) return
  roleSubmitting.value = true
  try { await managementService.createRole(roleForm); Object.assign(roleForm, { libelle: '', description: '' }); await load(); success.value = 'Rôle créé avec succès.'; error.value = '' }
  catch (e: any) { error.value = e?.response?.data?.detail || 'Création du rôle impossible.' }
  finally { roleSubmitting.value = false }
}

async function addPermission() {
  if (permissionSubmitting.value || !permissionForm.code.trim() || !permissionForm.libelle.trim() || !permissionForm.module.trim()) return
  permissionSubmitting.value = true
  try { await managementService.createPermission(permissionForm); Object.assign(permissionForm, { code: '', libelle: '', module: '', description: '' }); await load(); success.value = 'Permission créée avec succès.'; error.value = '' }
  catch (e: any) { error.value = e?.response?.data?.detail || 'Création de la permission impossible.' }
  finally { permissionSubmitting.value = false }
}

async function toggleRole(item: Role) { try { Object.assign(item, await managementService.toggleRole(item.id)) } catch (e: any) { error.value = e?.response?.data?.detail || 'Action impossible sur ce rôle.' } }
async function removeRole(item: Role) { if (!window.confirm(`Supprimer le rôle « ${item.libelle} » ?`)) return; try { await managementService.deleteRole(item.id); await load(); success.value = 'Rôle supprimé avec succès.' } catch (e: any) { error.value = e?.response?.data?.detail || 'Suppression du rôle impossible.' } }
async function removePermission(item: Permission) { if (!window.confirm(`Supprimer la permission « ${item.code} » ?`)) return; try { await managementService.deletePermission(item.id); await load(); success.value = 'Permission supprimée avec succès.' } catch (e: any) { error.value = e?.response?.data?.detail || 'Suppression de la permission impossible.' } }

onMounted(load)
watch(section, () => {
  if (!isListPage.value) return
  page.value = 1
  search.value = ''
  load()
})
function changePage(next: number) { if (next >= 1 && next <= pages.value) { page.value = next; load() } }
function toggleSort() { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'; page.value = 1; load() }
</script>

<template>
  <AppLayout>
    <template #title>
      {{ section === 'cooperatives' ? 'Coopératives' : section === 'roles' ? 'Rôles & permissions' : 'Gares Routières' }}
    </template>

    <p v-if="loading" class="status-msg">Chargement des données en cours…</p>
    <p v-else-if="error" class="error-banner">{{ error }}</p>
    <p v-if="success" class="success-banner" role="status">{{ success }}</p>
    <ListToolbar v-if="isListPage && !loading && !error" v-model="search" placeholder="Rechercher dans cette liste" :sort-label="`Tri ${sortOrder === 'asc' ? 'croissant ↑' : 'décroissant ↓'}`" @search="page = 1; load()" @sort="toggleSort" />

    <!-- SECTION GARES -->
    <template v-if="section === 'gares'">
      <BaseCard v-if="!isListPage">
        <div class="card-heading">
          <div>
            <h2>Ajouter une gare routière</h2>
            <p>Enregistrez les coordonnées et la géolocalisation de la gare.</p>
          </div>
        </div>
        <form class="management-form" @submit.prevent="addGare">
          <div class="form-grid">
            <input v-model="gare.nom" placeholder="Nom de la gare (ex: Gare Routière Anosibe)" required />
            <input v-model="gare.ville" placeholder="Ville (ex: Antananarivo)" required />
            <input v-model="gare.adresse" placeholder="Adresse complète" required />
            <input v-model="gare.telephone" placeholder="Téléphone de contact" />
            <input v-model="gare.email" type="email" placeholder="Adresse Email" />
            <input v-model.number="gare.latitude" type="number" step="any" placeholder="Latitude (ex: -18.8792)" />
            <input v-model.number="gare.longitude" type="number" step="any" placeholder="Longitude (ex: 47.5079)" />
          </div>
          <button class="primary-button" type="submit" :disabled="gareSubmitting">{{ gareSubmitting ? 'Enregistrement…' : 'Enregistrer la gare' }}</button>
        </form>
      </BaseCard>

      <BaseCard>
        <div v-if="false" class="edit-panel">
          <h2>Modifier la gare</h2>
          <form class="management-form" @submit.prevent="saveGare">
            <div class="form-grid"><input v-model="editingGare.nom" required placeholder="Nom" /><input v-model="editingGare.ville" required placeholder="Ville" /><input v-model="editingGare.adresse" required placeholder="Adresse" /><input v-model="editingGare.telephone" placeholder="Téléphone" /><input v-model="editingGare.email" type="email" placeholder="Email" /></div>
            <button class="primary-button" type="submit">Enregistrer les modifications</button><button class="secondary-button" type="button" @click="cancelEdit">Annuler</button>
          </form>
        </div>
        <div class="card-heading"><div><h2>Gares enregistrées ({{ gares.length }})</h2><p>Consultez, filtrez et gérez les gares existantes.</p></div><RouterLink class="primary-button compact-button" to="/gares/new">+ Nouvelle gare</RouterLink></div>
        <table class="data-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Ville</th>
              <th>Coordonnées (GPS)</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in gares" :key="item.id">
              <td><strong>{{ item.nom }}</strong></td>
              <td>{{ item.ville }}</td>
              <td>
                <span v-if="item.latitude && item.longitude" class="gps-badge">
                  📍 {{ item.latitude.toFixed(4) }}, {{ item.longitude.toFixed(4) }}
                </span>
                <span v-else class="text-muted">Non géolocalisée</span>
              </td>
              <td>
                <span :class="['status-badge', item.is_active ? 'active' : 'inactive']">
                  {{ item.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td>
                <button class="table-action" @click="toggleGare(item)">
                  {{ item.is_active ? 'Désactiver' : 'Activer' }}
                </button>
                <RouterLink class="table-action table-link" :to="`/gares/${item.id}/edit`">Modifier</RouterLink>
                <button class="table-action danger-action" @click="removeGare(item)">Supprimer</button>
              </td>
            </tr>
          </tbody>
        </table>
      </BaseCard>
    </template>

    <!-- SECTION COOPERATIVES -->
    <template v-else-if="section === 'cooperatives'">
      <BaseCard v-if="!isListPage">
        <div class="card-heading">
          <div>
            <h2>Ajouter une coopérative</h2>
            <p>Enregistrez les informations juridiques, de contact et le logo.</p>
          </div>
        </div>
        <form class="management-form" @submit.prevent="addCooperative">
          <div class="form-grid">
            <input v-model="cooperative.nom" placeholder="Nom de la coopérative" required />
            <input v-model="cooperative.sigle" placeholder="Sigle / Abréviation (ex: Cotisse)" />
            <input v-model="cooperative.numero_agrement" placeholder="Numéro d’agrément / NIF" />
            <input v-model="cooperative.ville" placeholder="Ville d'attache" />
            <input v-model="cooperative.telephone" placeholder="Téléphone" />
            <input v-model="cooperative.email" type="email" placeholder="Email de contact" />
            <input v-model="cooperative.logo_url" placeholder="URL du Logo (ex: https://...)" />
          </div>
          <button class="primary-button" type="submit" :disabled="cooperativeSubmitting">{{ cooperativeSubmitting ? 'Enregistrement…' : 'Enregistrer la coopérative' }}</button>
        </form>
      </BaseCard>

      <BaseCard>
        <div v-if="false" class="edit-panel">
          <h2>Modifier la coopérative</h2>
          <form class="management-form" @submit.prevent="saveCooperative">
            <div class="form-grid"><input v-model="editingCooperative.nom" required placeholder="Nom" /><input v-model="editingCooperative.sigle" placeholder="Sigle" /><input v-model="editingCooperative.ville" placeholder="Ville" /><input v-model="editingCooperative.adresse" placeholder="Adresse" /><input v-model="editingCooperative.telephone" placeholder="Téléphone" /><input v-model="editingCooperative.email" type="email" placeholder="Email" /></div>
            <button class="primary-button" type="submit">Enregistrer les modifications</button><button class="secondary-button" type="button" @click="cancelEdit">Annuler</button>
          </form>
        </div>
        <div class="card-heading"><div><h2>Coopératives enregistrées ({{ cooperatives.length }})</h2><p>Consultez, filtrez et gérez les coopératives existantes.</p></div><RouterLink class="primary-button compact-button" to="/cooperatives/new">+ Nouvelle coopérative</RouterLink></div>
        <table class="data-table">
          <thead>
            <tr>
              <th>Logo</th>
              <th>Nom / Sigle</th>
              <th>Ville</th>
              <th>Contact</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in cooperatives" :key="item.id">
              <td>
                <img v-if="item.logo_url" :src="item.logo_url" alt="Logo" class="logo-thumb" />
                <div v-else class="logo-placeholder">{{ (item.sigle || item.nom)[0] }}</div>
              </td>
              <td>
                <strong>{{ item.nom }}</strong>
                <small v-if="item.sigle" class="d-block text-muted">({{ item.sigle }})</small>
              </td>
              <td>{{ item.ville || '—' }}</td>
              <td>{{ item.telephone || item.email || '—' }}</td>
              <td>
                <span :class="['status-badge', item.is_active ? 'active' : 'inactive']">
                  {{ item.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td>
                <button class="table-action" @click="toggleCooperative(item)">
                  {{ item.is_active ? 'Désactiver' : 'Activer' }}
                </button>
                <RouterLink class="table-action table-link" :to="`/cooperatives/${item.id}/edit`">Modifier</RouterLink>
                <button class="table-action danger-action" @click="removeCooperative(item)">Supprimer</button>
              </td>
            </tr>
          </tbody>
        </table>
      </BaseCard>
    </template>

    <!-- SECTION ROLES & PERMISSIONS -->
    <template v-else>
      <BaseCard>
        <h2>Créer un rôle</h2>
        <form class="management-form inline-form" @submit.prevent="addRole"><input v-model="roleForm.libelle" required placeholder="Libellé du rôle" /><input v-model="roleForm.description" placeholder="Description" /><button class="primary-button" :disabled="roleSubmitting">Créer le rôle</button></form>
      </BaseCard>
      <BaseCard>
        <h2>Rôles configurés ({{ roles.length }})</h2>
        <table class="data-table"><caption>Gestion des rôles</caption><thead><tr><th>Libellé</th><th>Description</th><th>Statut</th><th>Actions</th></tr></thead><tbody><tr v-for="item in roles" :key="item.id"><td><strong>{{ item.libelle.toUpperCase() }}</strong></td><td>{{ item.description || '—' }}</td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Actif' : 'Inactif' }}</span></td><td><button class="table-action" @click="toggleRole(item)">{{ item.is_active ? 'Désactiver' : 'Activer' }}</button><button class="table-action danger-action" @click="removeRole(item)">Supprimer</button></td></tr></tbody></table>
      </BaseCard>

      <BaseCard>
        <h2>Créer une permission</h2>
        <form class="management-form inline-form" @submit.prevent="addPermission"><input v-model="permissionForm.code" required placeholder="Code (ex: GARE_READ)" /><input v-model="permissionForm.libelle" required placeholder="Libellé" /><input v-model="permissionForm.module" required placeholder="Module" /><button class="primary-button" :disabled="permissionSubmitting">Créer la permission</button></form>
      </BaseCard>
      <BaseCard>
        <h2>Permissions système ({{ permissions.length }})</h2>
        <table class="data-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Module</th>
              <th>Description</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in permissions" :key="item.id">
              <td><code>{{ item.code }}</code></td>
              <td><span class="module-badge">{{ item.module }}</span></td>
              <td>{{ item.description || item.libelle }}</td><td><button class="table-action danger-action" @click="removePermission(item)">Supprimer</button></td>
            </tr>
          </tbody>
        </table>
      </BaseCard>
    </template>
    <div v-if="!loading && !error" class="pagination">
      <button class="secondary-button" :disabled="page <= 1" @click="changePage(page - 1)">Précédent</button>
      <span>Page {{ page }} / {{ pages }} · {{ total }} résultat(s)</span>
      <button class="secondary-button" :disabled="page >= pages" @click="changePage(page + 1)">Suivant</button>
    </div>
  </AppLayout>
</template>
