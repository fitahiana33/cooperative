<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import StatCard from '../../components/ui/StatCard.vue'
import type { DashboardStatistics, DashboardSummary } from '../../models/dashboard/model'
import { dashboardService } from '../../services/dashboard/service'
import { userError } from '../../utils/errors'

const data = ref<DashboardSummary>({ date: '', departs_du_jour: 0, reservations_du_jour: 0, places_disponibles: 0, cooperatives_actives: 0, vehicules_actifs: 0, chauffeurs_actifs: 0, passagers_du_jour: 0, recettes_du_jour: 0, departs_imminents: [] })
const period = ref<DashboardStatistics | null>(null)
const loading = ref(true)
const error = ref('')
let refreshTimer: number | undefined

const totalCapacity = computed(() => period.value?.departs?.find((row) => row.date === data.value?.date)?.places_total || data.value?.departs_imminents?.filter((item) => item.date_depart === data.value?.date).reduce((sum, item) => sum + item.nombre_places, 0) || 0)
const reservedCapacity = computed(() => Math.max(totalCapacity.value - (data.value?.places_disponibles || 0), 0))
const occupancy = computed(() => totalCapacity.value ? Math.round((reservedCapacity.value / totalCapacity.value) * 100) : 0)
const money = computed(() => Number(data.value?.recettes_du_jour || 0).toLocaleString('fr-FR') + ' MGA')
const stats = computed(() => [
  { label: 'Départs aujourd’hui', value: String(data.value?.departs_du_jour ?? 0), detail: 'Planning du jour', icon: '◷', tone: 'stat-blue' },
  { label: 'Réservations', value: String(data.value?.reservations_du_jour ?? 0), detail: `${data.value?.passagers_du_jour ?? 0} passager(s) distinct(s)`, icon: '▤', tone: 'stat-purple' },
  { label: 'Places disponibles', value: String(data.value?.places_disponibles ?? 0), detail: `${occupancy.value}% de remplissage`, icon: '▦', tone: 'stat-orange' },
  { label: 'Recettes du jour', value: money.value, detail: 'Paiements validés', icon: '◈', tone: 'stat-green' },
])

function routeName(item: DashboardSummary['departs_imminents'][number]) {
  const departure = item.itineraire?.destination_depart?.nom
  const arrival = item.itineraire?.destination_arrivee?.nom
  return departure && arrival ? `${departure} → ${arrival}` : `Itinéraire #${item.id_itineraire}`
}

function statusLabel(status: string) { return ({ PROGRAMME: 'Programmé', EMBARQUEMENT: 'Embarquement', RETARDE: 'Retardé' } as Record<string, string>)[status] || status }

async function load() {
  try {
    const [summary, statistics] = await Promise.all([dashboardService.summary(), dashboardService.statistics()])
    data.value = summary as DashboardSummary
    period.value = statistics as DashboardStatistics
  }
  catch (value: unknown) { error.value = userError(value, 'Le tableau de bord est momentanément indisponible.', 'DASHBOARD_ERROR') }
  finally { loading.value = false }
}
onMounted(load)
onMounted(() => { refreshTimer = window.setInterval(load, 30000) })
onUnmounted(() => { if (refreshTimer) window.clearInterval(refreshTimer) })
</script>

<template>
  <AppLayout>
    <template #title>Tableau de bord</template>
    <section class="page-intro">
      <div><span class="eyebrow">PILOTAGE OPÉRATIONNEL</span><h2>Tableau de bord</h2><p>État réel de l’activité au {{ data?.date || '—' }}.</p></div>
      <div class="dashboard-actions"><button class="secondary-button" type="button" @click="load">Actualiser</button><RouterLink class="primary-button" to="/reservations/new">Nouvelle réservation</RouterLink></div>
    </section>
    <p v-if="loading" class="status-msg">Chargement des données métier…</p><p v-else-if="error" class="error-banner">{{ error }}</p>
    <template v-else>
      <section class="stats-grid"><StatCard v-for="stat in stats" :key="stat.label" v-bind="stat" /></section>
      <section class="dashboard-grid">
        <BaseCard><div class="card-heading"><div><h2>Occupation du jour</h2><p>Places réservées par rapport à la capacité planifiée.</p></div><strong class="metric-accent">{{ occupancy }}%</strong></div><div class="progress-track"><span :style="{ width: `${occupancy}%` }"></span></div><div class="metric-row"><span><strong>{{ reservedCapacity }}</strong> réservées</span><span><strong>{{ data.places_disponibles }}</strong> disponibles</span><span><strong>{{ totalCapacity }}</strong> capacité</span></div><div class="detail-grid compact-details"><div class="detail-item"><span class="detail-label">Véhicules actifs</span><strong>{{ data.vehicules_actifs }}</strong></div><div class="detail-item"><span class="detail-label">Chauffeurs actifs</span><strong>{{ data.chauffeurs_actifs }}</strong></div><div class="detail-item"><span class="detail-label">Coopératives actives</span><strong>{{ data.cooperatives_actives }}</strong></div></div></BaseCard>
        <BaseCard><div class="card-heading"><div><h2>Activité récente</h2><p>Réservations et passagers du jour.</p></div><RouterLink class="card-link" to="/statistiques">Analyse complète →</RouterLink></div><div class="activity-list"><div><span>Réservations actives</span><strong>{{ data.reservations_du_jour }}</strong></div><div><span>Passagers distincts</span><strong>{{ data.passagers_du_jour }}</strong></div><div><span>Recettes encaissées</span><strong>{{ money }}</strong></div></div></BaseCard>
      </section>
      <BaseCard class="upcoming-card"><div class="card-heading"><div><h2>Prochains départs</h2><p>Les huit prochains départs enregistrés dans le planning.</p></div><RouterLink class="card-link" to="/departs">Voir le planning →</RouterLink></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Date</th><th>Heure</th><th>Itinéraire</th><th>Véhicule</th><th>Occupation</th><th>Statut</th></tr></thead><tbody><tr v-for="item in data.departs_imminents" :key="item.id"><td>{{ item.date_depart }}</td><td>{{ item.heure_depart?.slice(0, 5) }}</td><td>{{ routeName(item) }}</td><td>{{ item.vehicule?.immatriculation || `#${item.id}` }}</td><td>{{ item.places_reservees }}/{{ item.nombre_places }}</td><td><span class="status-badge active">{{ statusLabel(item.statut) }}</span></td></tr><tr v-if="!data.departs_imminents?.length"><td colspan="6" class="empty-state">Aucun départ à venir.</td></tr></tbody></table></div></BaseCard>
    </template>
  </AppLayout>
</template>

<style scoped>
.dashboard-actions { display: flex; gap: 0.75rem; }
.dashboard-grid { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 1rem; margin-top: 1rem; }
.dashboard-grid > .base-card, .upcoming-card { padding: 1.25rem; }
.metric-accent { color: #2563eb; font-size: 1.5rem; }
.progress-track { height: 12px; margin: 1.5rem 0 0.75rem; overflow: hidden; border-radius: 999px; background: #e2e8f0; }
.progress-track span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #2563eb, #14b8a6); transition: width 300ms ease; }
.metric-row { display: flex; justify-content: space-between; gap: 1rem; color: #64748b; font-size: 0.8rem; }
.metric-row strong { color: #0f172a; font-size: 1rem; }
.compact-details { margin-top: 1.5rem; }
.activity-list { display: grid; gap: 0.75rem; margin-top: 1.25rem; }
.activity-list div { display: flex; justify-content: space-between; gap: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 0.85rem; }
.activity-list strong { color: #0f172a; }
.upcoming-card { margin-top: 1rem; padding: 1.25rem; }
@media (max-width: 767px) { .dashboard-actions { width: 100%; flex-direction: column; } .dashboard-grid { grid-template-columns: 1fr; } .metric-row { flex-wrap: wrap; } }
</style>
