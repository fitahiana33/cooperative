<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import ListToolbar from '../../components/ui/ListToolbar.vue'
import { vehiculeService } from '../../services/vehicule/service'
import { chauffeurService } from '../../services/chauffeur/service'
import { marqueService } from '../../services/marque/service'
import { modeleService } from '../../services/modele/service'
import { cooperativeService } from '../../services/cooperative/service'
import type { Vehicule } from '../../models/vehicule/model'
import type { Chauffeur } from '../../models/chauffeur/model'
import type { Marque } from '../../models/marque/model'
import type { Modele } from '../../models/modele/model'
import type { Cooperative } from '../../models/cooperative/model'
import { userError } from '../../utils/errors'
import { useAuthenticationStore } from '../../stores/authentication/store'

type FleetSection = 'vehicules' | 'chauffeurs' | 'marques' | 'modeles'
const route = useRoute()
const auth = useAuthenticationStore()
const section = computed<FleetSection>(() => {
  const name = String(route.name || 'vehicules')
  return ['vehicules', 'chauffeurs', 'marques', 'modeles'].includes(name) ? name as FleetSection : 'vehicules'
})
const title = computed(() => ({ vehicules: 'Véhicules', chauffeurs: 'Chauffeurs', marques: 'Marques', modeles: 'Modèles' }[section.value]))
const description = computed(() => ({
  vehicules: 'Consultez le parc automobile, sa disponibilité et son état.',
  chauffeurs: 'Consultez les conducteurs, leurs permis et leurs disponibilités.',
  marques: 'Consultez les marques utilisées par votre flotte.',
  modeles: 'Consultez les modèles rattachés à chaque marque.',
}[section.value]))
const createPath = computed(() => `/${section.value}/new`)
const canManageCatalog = computed(() => auth.userRole.toLowerCase() === 'admin')

const vehicules = ref<Vehicule[]>([])
const chauffeurs = ref<Chauffeur[]>([])
const marques = ref<Marque[]>([])
const modeles = ref<Modele[]>([])
const cooperatives = ref<Cooperative[]>([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const search = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const loading = ref(true)
const error = ref('')
const success = ref('')
const busyAction = ref<string | null>(null)

function showError(errorValue: unknown, fallback: string) {
  error.value = userError(errorValue, fallback, 'FLEET_LIST_ERROR')
  success.value = ''
}

async function loadReferences() {
  const results = await Promise.allSettled([
    marqueService.listMarques({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
    modeleService.listModeles({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
    cooperativeService.listCooperatives({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
  ])
  if (results[0].status === 'fulfilled') marques.value = results[0].value.items
  if (results[1].status === 'fulfilled') modeles.value = results[1].value.items
  if (results[2].status === 'fulfilled') cooperatives.value = results[2].value.items
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = section.value === 'vehicules'
      ? await vehiculeService.listVehicules({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'immatriculation', sort_order: sortOrder.value })
      : section.value === 'chauffeurs'
        ? await chauffeurService.listChauffeurs({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'created_at', sort_order: sortOrder.value })
        : section.value === 'marques'
          ? await marqueService.listMarques({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'nom', sort_order: sortOrder.value })
          : await modeleService.listModeles({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'nom', sort_order: sortOrder.value })

    if (section.value === 'vehicules') vehicules.value = result.items
    if (section.value === 'chauffeurs') chauffeurs.value = result.items
    if (section.value === 'marques') marques.value = result.items
    if (section.value === 'modeles') modeles.value = result.items
    total.value = result.total
    pages.value = result.pages || 1
  } catch (errorValue: unknown) {
    showError(errorValue, 'Impossible de charger cette liste.')
  } finally {
    loading.value = false
  }
}

function displayCooperative(item: Vehicule | number) {
  if (typeof item === 'number') return cooperatives.value.find(value => value.id === item)?.nom || `Coopérative #${item}`
  return item.cooperative?.nom || cooperatives.value.find(value => value.id === item.id_cooperative)?.nom || `Coopérative #${item.id_cooperative}`
}
function displayUser(item: Chauffeur | number) {
  if (typeof item === 'number') return `Utilisateur #${item}`
  return item.user ? `${item.user.first_name || ''} ${item.user.name}`.trim() : `Utilisateur #${item.id_user}`
}
function displayModele(item: Vehicule | number) {
  if (typeof item === 'number') {
    const model = modeles.value.find(value => value.id === item)
    const brand = model ? marques.value.find(value => value.id === model.id_marque)?.nom : undefined
    return model ? `${brand || ''} ${model.nom}`.trim() : `Modèle #${item}`
  }
  const brand = item.modele?.id_marque ? marques.value.find(value => value.id === item.modele?.id_marque)?.nom : undefined
  return item.modele ? `${brand || ''} ${item.modele.nom}`.trim() : `Modèle #${item.id_modele}`
}

async function toggle(item: Vehicule | Chauffeur | Marque | Modele) {
  if (busyAction.value) return
  busyAction.value = `toggle-${item.id}`
  try {
    error.value = ''
    if (section.value === 'vehicules') Object.assign(item, await vehiculeService.toggleVehicule(item.id))
    if (section.value === 'chauffeurs') Object.assign(item, await chauffeurService.toggleChauffeur(item.id))
    if (section.value === 'marques') Object.assign(item, await marqueService.toggleMarque(item.id))
    if (section.value === 'modeles') Object.assign(item, await modeleService.toggleModele(item.id))
    success.value = 'Statut mis à jour avec succès.'
  } catch (errorValue: unknown) { showError(errorValue, 'Modification du statut impossible.') }
  finally { busyAction.value = null }
}

async function remove(item: Vehicule | Chauffeur | Marque | Modele) {
  const label = 'immatriculation' in item ? item.immatriculation : 'numero_permis' in item ? item.numero_permis : item.nom
  if (!window.confirm(`Supprimer « ${label} » ?`)) return
  if (busyAction.value) return
  busyAction.value = `delete-${item.id}`
  try {
    if (section.value === 'vehicules') await vehiculeService.deleteVehicule(item.id)
    if (section.value === 'chauffeurs') await chauffeurService.deleteChauffeur(item.id)
    if (section.value === 'marques') await marqueService.deleteMarque(item.id)
    if (section.value === 'modeles') await modeleService.deleteModele(item.id)
    success.value = 'Élément supprimé avec succès.'
    await load()
  } catch (errorValue: unknown) { showError(errorValue, 'Suppression impossible.') }
  finally { busyAction.value = null }
}

function changePage(next: number) { if (next >= 1 && next <= pages.value) { page.value = next; load() } }
function toggleSort() { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'; page.value = 1; load() }

onMounted(async () => { await loadReferences(); await load(); if (typeof route.query.success === 'string') success.value = route.query.success })
watch(section, async () => { page.value = 1; search.value = ''; success.value = ''; await loadReferences(); await load() })
</script>

<template>
  <AppLayout>
    <template #title>{{ title }}</template>
    <div class="page-intro">
      <div><p class="eyebrow">GESTION DE LA FLOTTE</p><h2>{{ title }}</h2><p>{{ description }}</p></div>
       <RouterLink v-if="section === 'vehicules' || section === 'chauffeurs' || canManageCatalog" class="primary-button compact-button" :to="createPath">+ Ajouter</RouterLink>
    </div>
    <div class="section-links">
      <RouterLink to="/vehicules" :class="{ active: section === 'vehicules' }">Véhicules</RouterLink>
      <RouterLink to="/chauffeurs" :class="{ active: section === 'chauffeurs' }">Chauffeurs</RouterLink>
      <RouterLink to="/marques" :class="{ active: section === 'marques' }">Marques</RouterLink>
      <RouterLink to="/modeles" :class="{ active: section === 'modeles' }">Modèles</RouterLink>
    </div>
    <p v-if="loading" class="status-msg" role="status">Chargement des données en cours…</p>
    <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
    <p v-if="success" class="success-banner" role="status">{{ success }}</p>
    <ListToolbar v-if="!loading" v-model="search" :loading="busyAction !== null" :placeholder="'Rechercher dans les ' + title.toLowerCase()" :sort-label="'Tri ' + (sortOrder === 'asc' ? 'croissant ↑' : 'décroissant ↓')" @search="page = 1; load()" @sort="toggleSort" />

    <BaseCard v-if="section === 'vehicules'">
      <div class="card-heading"><div><h2>Véhicules enregistrés ({{ total }})</h2><p>Consultez et actualisez les informations du parc.</p></div></div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Immatriculation</th><th>Modèle</th><th>Coopérative</th><th>Places</th><th>État</th><th>Disponibilité</th><th>Statut</th><th>Actions</th></tr></thead><tbody>
        <tr v-for="item in vehicules" :key="item.id"><td><strong>{{ item.immatriculation }}</strong></td><td>{{ displayModele(item.id_modele) }}</td><td>{{ displayCooperative(item.id_cooperative) }}</td><td>{{ item.nombre_places }}</td><td><span class="module-badge">{{ item.etat }}</span></td><td><span :class="['status-badge', item.disponibilite ? 'active' : 'inactive']">{{ item.disponibilite ? 'Disponible' : 'Indisponible' }}</span></td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Actif' : 'Inactif' }}</span></td><td><button class="table-action" :disabled="busyAction !== null" @click="toggle(item)">{{ busyAction === `toggle-${item.id}` ? 'Traitement…' : (item.is_active ? 'Désactiver' : 'Activer') }}</button><RouterLink class="table-action table-link" :to="`/vehicules/${item.id}`">Détails</RouterLink><RouterLink class="table-action table-link" :to="`/vehicules/${item.id}/edit`">Modifier</RouterLink><button class="table-action danger-action" :disabled="busyAction !== null" @click="remove(item)">{{ busyAction === `delete-${item.id}` ? 'Suppression…' : 'Supprimer' }}</button></td></tr>
        <tr v-if="!vehicules.length"><td colspan="8"><div class="empty-state">Aucun véhicule trouvé.</div></td></tr>
      </tbody></table></div>
    </BaseCard>

    <BaseCard v-else-if="section === 'chauffeurs'">
      <div class="card-heading"><div><h2>Chauffeurs enregistrés ({{ total }})</h2><p>Suivez les permis, disponibilités et statuts.</p></div></div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Utilisateur</th><th>Permis</th><th>Catégorie</th><th>Coopérative</th><th>Expiration</th><th>Disponibilité</th><th>Statut</th><th>Actions</th></tr></thead><tbody>
        <tr v-for="item in chauffeurs" :key="item.id"><td><strong>{{ displayUser(item) }}</strong></td><td>{{ item.numero_permis }}</td><td><span class="module-badge">{{ item.categorie_permis }}</span></td><td>{{ displayCooperative(item.id_cooperative) }}</td><td>{{ item.date_expiration_permis }}</td><td><span :class="['status-badge', item.disponibilite ? 'active' : 'inactive']">{{ item.disponibilite ? 'Disponible' : 'Indisponible' }}</span></td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Actif' : 'Inactif' }}</span></td><td><button class="table-action" :disabled="busyAction !== null" @click="toggle(item)">{{ busyAction === `toggle-${item.id}` ? 'Traitement…' : (item.is_active ? 'Désactiver' : 'Activer') }}</button><RouterLink class="table-action table-link" :to="`/chauffeurs/${item.id}`">Détails</RouterLink><RouterLink class="table-action table-link" :to="`/chauffeurs/${item.id}/edit`">Modifier</RouterLink><button class="table-action danger-action" :disabled="busyAction !== null" @click="remove(item)">{{ busyAction === `delete-${item.id}` ? 'Suppression…' : 'Supprimer' }}</button></td></tr>
        <tr v-if="!chauffeurs.length"><td colspan="8"><div class="empty-state">Aucun chauffeur trouvé.</div></td></tr>
      </tbody></table></div>
    </BaseCard>

    <BaseCard v-else-if="section === 'marques'">
      <div class="card-heading"><div><h2>Marques enregistrées ({{ total }})</h2><p>Consultez et gérez les marques disponibles.</p></div></div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Nom</th><th>Description</th><th>Statut</th><th>Actions</th></tr></thead><tbody>
        <tr v-for="item in marques" :key="item.id"><td><strong>{{ item.nom }}</strong></td><td>{{ item.description || '—' }}</td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Active' : 'Inactive' }}</span></td><td><button class="table-action" :disabled="busyAction !== null" @click="toggle(item)">{{ busyAction === `toggle-${item.id}` ? 'Traitement…' : (item.is_active ? 'Désactiver' : 'Activer') }}</button><RouterLink class="table-action table-link" :to="`/marques/${item.id}`">Détails</RouterLink><RouterLink class="table-action table-link" :to="`/marques/${item.id}/edit`">Modifier</RouterLink><button class="table-action danger-action" :disabled="busyAction !== null" @click="remove(item)">{{ busyAction === `delete-${item.id}` ? 'Suppression…' : 'Supprimer' }}</button></td></tr>
        <tr v-if="!marques.length"><td colspan="4"><div class="empty-state">Aucune marque trouvée.</div></td></tr>
      </tbody></table></div>
    </BaseCard>

    <BaseCard v-else>
      <div class="card-heading"><div><h2>Modèles enregistrés ({{ total }})</h2><p>Consultez les modèles associés à vos marques.</p></div></div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Modèle</th><th>Marque</th><th>Description</th><th>Statut</th><th>Actions</th></tr></thead><tbody>
        <tr v-for="item in modeles" :key="item.id"><td><strong>{{ item.nom }}</strong></td><td>{{ marques.find(brand => brand.id === item.id_marque)?.nom || ('Marque #' + item.id_marque) }}</td><td>{{ item.description || '—' }}</td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Actif' : 'Inactif' }}</span></td><td><button class="table-action" :disabled="busyAction !== null" @click="toggle(item)">{{ busyAction === `toggle-${item.id}` ? 'Traitement…' : (item.is_active ? 'Désactiver' : 'Activer') }}</button><RouterLink class="table-action table-link" :to="`/modeles/${item.id}`">Détails</RouterLink><RouterLink class="table-action table-link" :to="`/modeles/${item.id}/edit`">Modifier</RouterLink><button class="table-action danger-action" :disabled="busyAction !== null" @click="remove(item)">{{ busyAction === `delete-${item.id}` ? 'Suppression…' : 'Supprimer' }}</button></td></tr>
        <tr v-if="!modeles.length"><td colspan="5"><div class="empty-state">Aucun modèle trouvé.</div></td></tr>
      </tbody></table></div>
    </BaseCard>

    <div v-if="!loading && !error" class="pagination"><button class="secondary-button" :disabled="page <= 1" @click="changePage(page - 1)">Précédent</button><span>Page {{ page }} / {{ pages }} · {{ total }} résultat(s)</span><button class="secondary-button" :disabled="page >= pages" @click="changePage(page + 1)">Suivant</button></div>
  </AppLayout>
</template>
