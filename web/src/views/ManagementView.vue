<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../components/layout/AppLayout.vue'
import BaseCard from '../components/ui/BaseCard.vue'
import ListToolbar from '../components/ui/ListToolbar.vue'
import { managementService } from '../services/management/service'
import type { Gare } from '../models/gare/model'
import type { Cooperative } from '../models/cooperative/model'
import { userError } from '../utils/errors'

type Section = 'gares' | 'cooperatives'
const route = useRoute()
const section = computed<Section>(() => route.name === 'cooperatives' ? 'cooperatives' : 'gares')
const title = computed(() => section.value === 'gares' ? 'Gares' : 'Coopératives')
const description = computed(() => section.value === 'gares' ? 'Consultez et gérez les gares routières enregistrées.' : 'Consultez et gérez les coopératives partenaires.')
const createPath = computed(() => `/${section.value}/new`)
const gares = ref<Gare[]>([])
const cooperatives = ref<Cooperative[]>([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const search = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const loading = ref(true)
const busyAction = ref<string | null>(null)
const error = ref('')
const success = ref('')

function showError(errorValue: unknown, fallback: string) { error.value = userError(errorValue, fallback, 'MANAGEMENT_LIST_ERROR'); success.value = '' }
async function load() {
  loading.value = true; error.value = ''; success.value = ''
  try {
    if (section.value === 'gares') {
      const result = await managementService.listGares({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'nom', sort_order: sortOrder.value })
      gares.value = result.items; total.value = result.total; pages.value = result.pages || 1
    } else {
      const result = await managementService.listCooperatives({ page: page.value, page_size: 20, search: search.value || undefined, sort_by: 'nom', sort_order: sortOrder.value })
      cooperatives.value = result.items; total.value = result.total; pages.value = result.pages || 1
    }
  } catch (errorValue: unknown) { showError(errorValue, `Impossible de charger les ${title.value.toLowerCase()}.`) }
  finally { loading.value = false }
}
function changePage(next: number) { if (next >= 1 && next <= pages.value && !busyAction.value) { page.value = next; void load() } }
function toggleSort() { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'; page.value = 1; void load() }
async function toggle(item: Gare | Cooperative) {
  if (busyAction.value) return
  busyAction.value = `toggle-${item.id}`; error.value = ''
  try { Object.assign(item, section.value === 'gares' ? await managementService.toggleGare(item.id) : await managementService.toggleCooperative(item.id)); success.value = 'Statut mis à jour avec succès.' }
  catch (errorValue: unknown) { showError(errorValue, 'Modification du statut impossible.') }
  finally { busyAction.value = null }
}
async function remove(item: Gare | Cooperative) {
  if (!window.confirm(`Supprimer « ${item.nom} » ?`) || busyAction.value) return
  busyAction.value = `delete-${item.id}`; error.value = ''
  try {
    if (section.value === 'gares') { await managementService.deleteGare(item.id); gares.value = gares.value.filter(value => value.id !== item.id) }
    else { await managementService.deleteCooperative(item.id); cooperatives.value = cooperatives.value.filter(value => value.id !== item.id) }
    total.value = Math.max(0, total.value - 1); success.value = 'Élément supprimé avec succès.'
  } catch (errorValue: unknown) { showError(errorValue, 'Suppression impossible.') }
  finally { busyAction.value = null }
}
watch(section, () => { page.value = 1; search.value = ''; void load() })
onMounted(async () => { await load(); if (typeof route.query.success === 'string') success.value = route.query.success })
</script>

<template>
  <AppLayout>
    <template #title>{{ title }}</template>
    <div class="page-intro"><div><p class="eyebrow">GESTION ADMINISTRATIVE</p><h2>{{ title }}</h2><p>{{ description }}</p></div><RouterLink class="primary-button compact-button" :to="createPath">+ Ajouter</RouterLink></div>
    <div class="section-links"><RouterLink to="/gares" :class="{ active: section === 'gares' }">Gares</RouterLink><RouterLink to="/cooperatives" :class="{ active: section === 'cooperatives' }">Coopératives</RouterLink></div>
    <BaseCard><div class="card-heading"><div><h2>{{ title }} enregistrées ({{ total }})</h2><p>Utilisez la recherche, le tri et la pagination pour retrouver rapidement une donnée.</p></div></div><ListToolbar v-model="search" :loading="loading || busyAction !== null" :placeholder="`Rechercher dans les ${title.toLowerCase()}`" :sort-label="sortOrder === 'asc' ? 'Tri croissant ↑' : 'Tri décroissant ↓'" @search="page = 1; load()" @sort="toggleSort" /><p v-if="loading" class="status-msg" role="status">Chargement des données…</p><p v-else-if="error" class="error-banner" role="alert">{{ error }}</p><p v-if="success" class="success-banner" role="status">{{ success }}</p>
      <div v-if="!loading && !error" class="table-scroll"><table class="data-table"><caption>Liste des {{ title.toLowerCase() }}</caption><thead><tr v-if="section === 'gares'"><th>Nom</th><th>Ville</th><th>Adresse</th><th>Statut</th><th>Actions</th></tr><tr v-else><th>Nom</th><th>Sigle</th><th>Ville</th><th>Contact</th><th>Statut</th><th>Actions</th></tr></thead><tbody><template v-if="section === 'gares'"><tr v-for="item in gares" :key="item.id"><td><strong>{{ item.nom }}</strong></td><td>{{ item.ville }}</td><td>{{ item.adresse }}</td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Active' : 'Inactive' }}</span></td><td><RouterLink class="table-action table-link" :to="`/gares/${item.id}/edit`">Modifier</RouterLink><button class="table-action" :disabled="busyAction !== null" @click="toggle(item)">{{ busyAction === `toggle-${item.id}` ? 'Traitement…' : (item.is_active ? 'Désactiver' : 'Activer') }}</button><button class="table-action danger-action" :disabled="busyAction !== null" @click="remove(item)">{{ busyAction === `delete-${item.id}` ? 'Suppression…' : 'Supprimer' }}</button></td></tr><tr v-if="!gares.length"><td colspan="5"><div class="empty-state">Aucune gare trouvée.</div></td></tr></template><template v-else><tr v-for="item in cooperatives" :key="item.id"><td><strong>{{ item.nom }}</strong></td><td>{{ item.sigle || '—' }}</td><td>{{ item.ville || '—' }}</td><td>{{ item.telephone || item.email || '—' }}</td><td><span :class="['status-badge', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? 'Active' : 'Inactive' }}</span></td><td><RouterLink class="table-action table-link" :to="`/cooperatives/${item.id}/edit`">Modifier</RouterLink><button class="table-action" :disabled="busyAction !== null" @click="toggle(item)">{{ busyAction === `toggle-${item.id}` ? 'Traitement…' : (item.is_active ? 'Désactiver' : 'Activer') }}</button><button class="table-action danger-action" :disabled="busyAction !== null" @click="remove(item)">{{ busyAction === `delete-${item.id}` ? 'Suppression…' : 'Supprimer' }}</button></td></tr><tr v-if="!cooperatives.length"><td colspan="6"><div class="empty-state">Aucune coopérative trouvée.</div></td></tr></template></tbody></table></div><div v-if="!loading && !error" class="pagination"><button class="secondary-button" :disabled="page <= 1 || busyAction !== null" @click="changePage(page - 1)">Précédent</button><span>Page {{ page }} / {{ pages }} · {{ total }} résultat(s)</span><button class="secondary-button" :disabled="page >= pages || busyAction !== null" @click="changePage(page + 1)">Suivant</button></div>
    </BaseCard>
  </AppLayout>
</template>
