<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import ListToolbar from '../../components/ui/ListToolbar.vue'
import { destinationService } from '../../services/destination/service'
import { itineraireService } from '../../services/itineraire/service'
import { tarifService } from '../../services/tarif/service'
import { userError } from '../../utils/errors'
import { useAuthenticationStore } from '../../stores/authentication/store'

const route = useRoute()
const auth = useAuthenticationStore()
const section = computed(() => String(route.name).startsWith('destination') ? 'destinations' : String(route.name).startsWith('itineraire') ? 'itineraires' : 'tarifs')
const title = computed(() => ({ destinations: 'Destinations', itineraires: 'Itineraires', tarifs: 'Tarifs' }[section.value]))
const createPath = computed(() => `/${section.value}/new`)
const canWrite = computed(() => auth.hasPermission(section.value === 'destinations' ? 'DESTINATION_CREATE' : section.value === 'itineraires' ? 'ITINERAIRE_CREATE' : 'TARIF_CREATE'))
const canUpdate = computed(() => auth.hasPermission(section.value === 'destinations' ? 'DESTINATION_UPDATE' : section.value === 'itineraires' ? 'ITINERAIRE_UPDATE' : 'TARIF_UPDATE'))
const canDelete = computed(() => auth.hasPermission(section.value === 'destinations' ? 'DESTINATION_DELETE' : section.value === 'itineraires' ? 'ITINERAIRE_DELETE' : 'TARIF_DELETE'))
const items = ref<any[]>([])
const destinations = ref<any[]>([])
const total = ref(0); const page = ref(1); const pages = ref(1)
const search = ref(''); const sortOrder = ref<'asc' | 'desc'>('asc')
const loading = ref(true); const busy = ref<string | null>(null); const error = ref(''); const success = ref('')

function showError(value: unknown, fallback: string) { error.value = userError(value, fallback, 'ROUTES_LIST_ERROR'); success.value = '' }
function destinationName(id: number) { return destinations.value.find(item => item.id === id)?.nom || `Destination #${id}` }
function itineraryName(item: any) { return `${item.destination_depart?.nom || destinationName(item.id_destination_depart)} - ${item.destination_arrivee?.nom || destinationName(item.id_destination_arrivee)}` }
function formatDate(value?: string | null) { return value ? new Date(value).toLocaleDateString('fr-FR') : '-' }

async function loadReferences() {
  try { destinations.value = (await destinationService.list({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' })).items } catch { destinations.value = [] }
}
async function load() {
  loading.value = true; error.value = ''
  try {
    const params = { page: page.value, page_size: 20, search: search.value || undefined, sort_by: section.value === 'destinations' ? 'nom' : section.value === 'tarifs' ? 'date_debut' : 'created_at', sort_order: sortOrder.value }
    const result = section.value === 'destinations' ? await destinationService.list(params) : section.value === 'itineraires' ? await itineraireService.list(params) : await tarifService.list(params)
    items.value = result.items; total.value = result.total; pages.value = result.pages || 1
  } catch (value: unknown) { showError(value, `Impossible de charger les ${title.value.toLowerCase()}.`) }
  finally { loading.value = false }
}
async function toggle(item: any) {
  if (busy.value) return; busy.value = `toggle-${item.id}`; error.value = ''
  try { const updated = section.value === 'destinations' ? await destinationService.toggle(item.id) : section.value === 'itineraires' ? await itineraireService.toggle(item.id) : await tarifService.toggle(item.id); Object.assign(item, updated); success.value = 'Statut mis a jour avec succes.' }
  catch (value: unknown) { showError(value, 'Modification du statut impossible.') } finally { busy.value = null }
}
async function remove(item: any) {
  if (!window.confirm(`Supprimer ${section.value.slice(0, -1)} ?`) || busy.value) return
  busy.value = `delete-${item.id}`
  try { if (section.value === 'destinations') await destinationService.remove(item.id); else if (section.value === 'itineraires') await itineraireService.remove(item.id); else await tarifService.remove(item.id); success.value = 'Element supprime avec succes.'; await load() }
  catch (value: unknown) { showError(value, 'Suppression impossible.') } finally { busy.value = null }
}
function changePage(next: number) { if (next >= 1 && next <= pages.value) { page.value = next; void load() } }
function sort() { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'; page.value = 1; void load() }
watch(section, () => { page.value = 1; search.value = ''; void load() })
onMounted(async () => { await loadReferences(); await load(); if (typeof route.query.success === 'string') success.value = route.query.success })
</script>

<template>
  <AppLayout><template #title>{{ title }}</template>
    <div class="page-intro"><div><p class="eyebrow">RESEAU & TARIFICATION</p><h2>{{ title }}</h2><p>Consultez, recherchez et gerez les donnees du reseau.</p></div><RouterLink v-if="canWrite" class="primary-button compact-button" :to="createPath">+ Ajouter</RouterLink></div>
    <div class="section-links"><RouterLink to="/destinations" :class="{ active: section === 'destinations' }">Destinations</RouterLink><RouterLink to="/itineraires" :class="{ active: section === 'itineraires' }">Itineraires</RouterLink><RouterLink to="/tarifs" :class="{ active: section === 'tarifs' }">Tarifs</RouterLink></div>
    <BaseCard><div class="card-heading"><div><h2>{{ title }} ({{ total }})</h2><p>La pagination, la recherche et le tri restent disponibles.</p></div></div><ListToolbar v-model="search" :loading="loading || busy !== null" :placeholder="`Rechercher dans les ${title.toLowerCase()}`" :sort-label="sortOrder === 'asc' ? 'Tri croissant' : 'Tri decroissant'" @search="page = 1; load()" @sort="sort"/><p v-if="loading" class="status-msg">Chargement des donnees...</p><p v-else-if="error" class="error-banner" role="alert">{{ error }}</p><p v-if="success" class="success-banner" role="status">{{ success }}</p>
      <div v-if="!loading && !error" class="table-scroll">
        <table v-if="section === 'destinations'" class="data-table"><caption>Liste des destinations</caption><thead><tr><th>Nom</th><th>Region</th><th>Statut</th><th>Actions</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td><strong>{{ item.nom }}</strong></td><td>{{ item.region || '-' }}</td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Active' : 'Inactive' }}</span></td><td><button v-if="canUpdate" class="table-action" :disabled="busy !== null" @click="toggle(item)">{{ item.is_active ? 'Desactiver' : 'Activer' }}</button><RouterLink class="table-action table-link" :to="`/destinations/${item.id}`">Details</RouterLink><RouterLink v-if="canUpdate" class="table-action table-link" :to="`/destinations/${item.id}/edit`">Modifier</RouterLink><button v-if="canDelete" class="table-action danger-action" :disabled="busy !== null" @click="remove(item)">Supprimer</button></td></tr><tr v-if="!items.length"><td colspan="4" class="empty-state">Aucune destination enregistree.</td></tr></tbody></table>
        <table v-else-if="section === 'itineraires'" class="data-table"><caption>Liste des itineraires</caption><thead><tr><th>Depart</th><th>Arrivee</th><th>Distance</th><th>Duree</th><th>Statut</th><th>Actions</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td><strong>{{ item.destination_depart?.nom || destinationName(item.id_destination_depart) }}</strong></td><td>{{ item.destination_arrivee?.nom || destinationName(item.id_destination_arrivee) }}</td><td>{{ item.distance_km ?? '-' }} km</td><td>{{ item.duree_estimee_minutes ?? '-' }} min</td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Actif' : 'Inactif' }}</span></td><td><button v-if="canUpdate" class="table-action" :disabled="busy !== null" @click="toggle(item)">{{ item.is_active ? 'Desactiver' : 'Activer' }}</button><RouterLink class="table-action table-link" :to="`/itineraires/${item.id}`">Details</RouterLink><RouterLink v-if="canUpdate" class="table-action table-link" :to="`/itineraires/${item.id}/edit`">Modifier</RouterLink><button v-if="canDelete" class="table-action danger-action" :disabled="busy !== null" @click="remove(item)">Supprimer</button></td></tr><tr v-if="!items.length"><td colspan="6" class="empty-state">Aucun itineraire enregistre.</td></tr></tbody></table>
        <table v-else class="data-table"><caption>Liste des tarifs</caption><thead><tr><th>Itineraire</th><th>Portee</th><th>Prix</th><th>Periode</th><th>Statut</th><th>Actions</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td><strong>{{ item.itineraire ? itineraryName(item.itineraire) : `Itineraire #${item.id_itineraire}` }}</strong></td><td>{{ item.id_cooperative ? (item.cooperative?.nom || `Cooperative #${item.id_cooperative}`) : 'General' }}</td><td>{{ item.prix }} {{ item.devise }}</td><td>{{ formatDate(item.date_debut) }} - {{ formatDate(item.date_fin) }}</td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Actif' : 'Inactif' }}</span></td><td><button v-if="canUpdate" class="table-action" :disabled="busy !== null" @click="toggle(item)">{{ item.is_active ? 'Desactiver' : 'Activer' }}</button><RouterLink class="table-action table-link" :to="`/tarifs/${item.id}`">Details</RouterLink><RouterLink v-if="canUpdate" class="table-action table-link" :to="`/tarifs/${item.id}/edit`">Modifier</RouterLink><button v-if="canDelete" class="table-action danger-action" :disabled="busy !== null" @click="remove(item)">Supprimer</button></td></tr><tr v-if="!items.length"><td colspan="6" class="empty-state">Aucun tarif enregistre.</td></tr></tbody></table>
      </div>
    </BaseCard><div v-if="!loading && !error" class="pagination"><button class="secondary-button" :disabled="page <= 1" @click="changePage(page - 1)">Precedent</button><span>Page {{ page }} / {{ pages }} - {{ total }} resultat(s)</span><button class="secondary-button" :disabled="page >= pages" @click="changePage(page + 1)">Suivant</button></div>
  </AppLayout>
</template>
