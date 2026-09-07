<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import ListToolbar from '../../components/ui/ListToolbar.vue'
import { departService } from '../../services/depart/service'
import type { Depart, DepartStatus } from '../../models/depart/model'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { userError } from '../../utils/errors'

const auth = useAuthenticationStore()
const items = ref<Depart[]>([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const search = ref('')
const status = ref<DepartStatus | ''>('')
const dateFrom = ref('')
const dateTo = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const loading = ref(true)
const busy = ref<number | null>(null)
const error = ref('')
const success = ref('')

const canCreate = () => auth.hasPermission('DEPART_CREATE')
const canUpdate = () => auth.hasPermission('DEPART_UPDATE')
const canCancel = () => auth.hasPermission('DEPART_CANCEL')
const statusLabels: Record<DepartStatus, string> = {
  PROGRAMME: 'Programmé', EMBARQUEMENT: 'Embarquement', RETARDE: 'Retardé',
  PARTI: 'Parti', TERMINE: 'Terminé', ANNULE: 'Annulé',
}

function routeName(item: Depart) {
  return `${item.itineraire?.destination_depart?.nom || `#${item.id_itineraire}`} → ${item.itineraire?.destination_arrivee?.nom || ''}`
}
function formatDate(value: string) { return new Date(`${value}T00:00:00`).toLocaleDateString('fr-FR') }
function showError(value: unknown, fallback: string) { error.value = userError(value, fallback, 'DEPARTS_LIST_ERROR'); success.value = '' }
async function load() {
  loading.value = true; error.value = ''
  try {
    const result = await departService.list({
      page: page.value, page_size: 20, search: search.value || undefined,
      statut: status.value || undefined, date_from: dateFrom.value || undefined, date_to: dateTo.value || undefined,
      sort_by: 'date_depart', sort_order: sortOrder.value,
    })
    items.value = result.items; total.value = result.total; pages.value = result.pages || 1
  } catch (value: unknown) { showError(value, 'Impossible de charger les départs.') }
  finally { loading.value = false }
}
async function cancel(item: Depart) {
  if (busy.value || !window.confirm('Annuler ce départ ?')) return
  busy.value = item.id; error.value = ''
  try { Object.assign(item, await departService.cancel(item.id)); success.value = 'Départ annulé avec succès.' }
  catch (value: unknown) { showError(value, 'Impossible d’annuler ce départ.') }
  finally { busy.value = null }
}
function sort() { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'; page.value = 1; void load() }
function changePage(next: number) { if (next >= 1 && next <= pages.value) { page.value = next; void load() } }
onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>Départs & planning</template>
    <div class="page-intro"><div><p class="eyebrow">PLANIFICATION</p><h2>Départs & planning</h2><p>Programmez les départs et suivez leur état.</p></div><RouterLink v-if="canCreate()" class="primary-button compact-button" to="/departs/new">+ Programmer un départ</RouterLink></div>
    <BaseCard>
      <div class="card-heading"><div><h2>Liste des départs ({{ total }})</h2><p>Les conflits de véhicule et de chauffeur sont contrôlés automatiquement.</p></div></div>
      <ListToolbar v-model="search" :loading="loading || busy !== null" placeholder="Rechercher un statut" :sort-label="sortOrder === 'asc' ? 'Plus anciens' : 'Plus récents'" @search="page = 1; load()" @sort="sort" />
      <div class="filter-row"><select v-model="status" aria-label="Filtrer par statut" @change="page = 1; load()"><option value="">Tous les statuts</option><option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option></select><input v-model="dateFrom" type="date" aria-label="Date de début" @change="page = 1; load()" /><input v-model="dateTo" type="date" aria-label="Date de fin" @change="page = 1; load()" /></div>
      <p v-if="loading" class="status-msg">Chargement des départs…</p><p v-else-if="error" class="error-banner" role="alert">{{ error }}</p><p v-if="success" class="success-banner" role="status">{{ success }}</p>
      <div v-if="!loading && !error" class="table-scroll"><table class="data-table"><caption>Planning des départs</caption><thead><tr><th>Date / heure</th><th>Itinéraire</th><th>Coopérative</th><th>Véhicule</th><th>Places</th><th>Remplissage</th><th>Statut</th><th>Actions</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td><strong>{{ formatDate(item.date_depart) }}</strong><br />{{ item.heure_depart.slice(0, 5) }}</td><td>{{ routeName(item) }}</td><td>{{ item.cooperative?.nom || `#${item.id_cooperative}` }}</td><td>{{ item.vehicule?.immatriculation || `#${item.id_vehicule}` }}</td><td>{{ item.places_disponibles }} / {{ item.nombre_places }} disponibles</td><td>{{ item.taux_remplissage }} %</td><td><span :class="['status-badge', item.statut === 'ANNULE' ? 'inactive' : 'active']">{{ statusLabels[item.statut] }}</span></td><td><RouterLink class="table-action table-link" :to="`/departs/${item.id}`">Détails</RouterLink><RouterLink v-if="canUpdate() && ['PROGRAMME', 'RETARDE'].includes(item.statut)" class="table-action table-link" :to="`/departs/${item.id}/edit`">Modifier</RouterLink><button v-if="canCancel() && !['ANNULE', 'PARTI', 'TERMINE'].includes(item.statut)" class="table-action danger-action" :disabled="busy !== null" @click="cancel(item)">Annuler</button></td></tr><tr v-if="!items.length"><td colspan="8" class="empty-state">Aucun départ enregistré.</td></tr></tbody></table></div>
    </BaseCard>
    <div v-if="!loading && !error" class="pagination"><button class="secondary-button" :disabled="page <= 1" @click="changePage(page - 1)">Précédent</button><span>Page {{ page }} / {{ pages }} — {{ total }} résultat(s)</span><button class="secondary-button" :disabled="page >= pages" @click="changePage(page + 1)">Suivant</button></div>
  </AppLayout>
</template>
