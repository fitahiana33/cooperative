<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import ListToolbar from '../../components/ui/ListToolbar.vue'
import { reservationService } from '../../services/reservation/service'
import type { Reservation, ReservationStatus } from '../../models/reservation/model'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { userError } from '../../utils/errors'

const auth = useAuthenticationStore()
const items = ref<Reservation[]>([])
const search = ref('')
const status = ref<ReservationStatus | ''>('')
const page = ref(1)
const pages = ref(1)
const total = ref(0)
const loading = ref(true)
const error = ref('')
const statuses: Record<ReservationStatus, string> = { EN_ATTENTE: 'En attente', CONFIRMEE: 'Confirmée', PAYEE: 'Payée', ANNULEE: 'Annulée', EXPIREE: 'Expirée', EMBARQUEE: 'Embarquée', TERMINEE: 'Terminée' }

function showError(value: unknown) { error.value = userError(value, 'Impossible de charger les réservations.', 'RESERVATIONS_LIST_ERROR') }
async function load() {
  loading.value = true; error.value = ''
  try {
    const result = await reservationService.list({ page: page.value, page_size: 20, search: search.value || undefined, statut: status.value || undefined })
    items.value = result.items; total.value = result.total; pages.value = result.pages || 1
  } catch (value: unknown) { showError(value) } finally { loading.value = false }
}
function routeName(item: Reservation) { return item.depart ? `Départ #${item.id_depart}` : `Départ #${item.id_depart}` }
function formatDate(value?: string) { return value ? new Date(value).toLocaleString('fr-FR') : '—' }
const canCreate = () => auth.hasPermission('RESERVATION_CREATE')
onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>Réservations</template>
    <div class="page-intro"><div><p class="eyebrow">VENTES & PLACES</p><h2>Réservations</h2><p>Consultez les réservations et leur cycle jusqu’au billet.</p></div><RouterLink v-if="canCreate()" class="primary-button compact-button" to="/reservations/new">+ Nouvelle réservation</RouterLink></div>
    <BaseCard>
      <div class="card-heading"><div><h2>Liste des réservations ({{ total }})</h2><p>Les places sont verrouillées par le serveur pour empêcher les doubles réservations.</p></div></div>
      <ListToolbar v-model="search" :loading="loading" placeholder="N° de réservation" @search="page = 1; load()" />
      <div class="filter-row"><select v-model="status" aria-label="Filtrer par statut" @change="page = 1; load()"><option value="">Tous les statuts</option><option v-for="(label, value) in statuses" :key="value" :value="value">{{ label }}</option></select></div>
      <p v-if="loading" class="status-msg">Chargement des réservations…</p><p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
      <div v-if="!loading && !error" class="table-scroll"><table class="data-table"><caption>Réservations enregistrées</caption><thead><tr><th>Numéro</th><th>Départ</th><th>Places</th><th>Montant</th><th>Créée le</th><th>Statut</th><th>Actions</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td><strong>{{ item.numero_reservation }}</strong></td><td>{{ routeName(item) }}<br><small>{{ item.depart?.date_depart }} {{ item.depart?.heure_depart?.slice(0, 5) }}</small></td><td>{{ item.places?.length || 0 }}</td><td>{{ item.montant_total }}</td><td>{{ formatDate(item.created_at) }}</td><td><span class="status-badge" :class="item.statut === 'ANNULEE' || item.statut === 'EXPIREE' ? 'inactive' : 'active'">{{ statuses[item.statut] || item.statut }}</span></td><td><RouterLink class="table-action table-link" :to="`/reservations/${item.id}`">Détails</RouterLink></td></tr><tr v-if="!items.length"><td colspan="7" class="empty-state">Aucune réservation enregistrée.</td></tr></tbody></table></div>
    </BaseCard>
    <div v-if="!loading && !error" class="pagination"><button class="secondary-button" :disabled="page <= 1" @click="page--; load()">Précédent</button><span>Page {{ page }} / {{ pages }} — {{ total }} résultat(s)</span><button class="secondary-button" :disabled="page >= pages" @click="page++; load()">Suivant</button></div>
  </AppLayout>
</template>
