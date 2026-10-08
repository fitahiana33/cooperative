<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { localIsoDate, daysAgo } from '../../utils/date'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import type { DashboardStatistics } from '../../models/dashboard/model'
import { dashboardService } from '../../services/dashboard/service'
import { userError } from '../../utils/errors'

const data = ref<DashboardStatistics | null>(null)
const loading = ref(true)
const error = ref('')
const today = localIsoDate()
const defaultFrom = localIsoDate(daysAgo(29))
const dateFrom = ref(defaultFrom)
const dateTo = ref(today)
const viewMode = ref<'trends' | 'details'>('trends')
const invalidPeriod = computed(() => !dateFrom.value || !dateTo.value || dateTo.value < dateFrom.value)

const totals = computed(() => {
  const departs = data.value?.departs || []
  const reservations = data.value?.reservations || []
  const totalDepartures = departs.reduce((sum, row) => sum + row.total, 0)
  const reserved = departs.reduce((sum, row) => sum + row.places_reservees, 0)
  const capacity = departs.reduce((sum, row) => sum + row.places_total, 0)
  return { totalDepartures, reservations: reservations.reduce((sum, row) => sum + row.total, 0), reserved, capacity, occupancy: capacity ? Math.round((reserved / capacity) * 100) : 0 }
})

const variation = (current: number, previous: number) => previous ? Math.round(((current - previous) / previous) * 100) : current ? 100 : 0
const trends = computed(() => {
  const comparison = data.value?.comparison
  const departures = comparison?.departs || { current: 0, previous: 0 }
  const reservations = comparison?.reservations || { current: 0, previous: 0 }
  const occupancy = comparison?.remplissage || { current: 0, previous: 0 }
  return { departures, reservations, occupancy, variations: { departures: variation(departures.current, departures.previous), reservations: variation(reservations.current, reservations.previous), occupancy: variation(occupancy.current, occupancy.previous) } }
})

const chartRows = computed(() => {
  const departures = data.value?.departs || []
  const reservations = new Map((data.value?.reservations || []).map((row) => [row.date, row.total]))
  return departures.map((row) => ({ ...row, reservations: reservations.get(row.date) || 0, occupancy: row.places_total ? Math.round((row.places_reservees * 100) / row.places_total) : 0 }))
})
const chartMax = computed(() => Math.max(...chartRows.value.flatMap((row) => [row.total, row.reservations]), 1))
const chartPoints = computed(() => (key: 'total' | 'reservations') => chartRows.value.map((row, index) => `${chartRows.value.length > 1 ? (index / (chartRows.value.length - 1)) * 100 : 50},${100 - (row[key] / chartMax.value) * 88}`))
const occupancyPoints = computed(() => chartRows.value.map((row, index) => `${chartRows.value.length > 1 ? (index / (chartRows.value.length - 1)) * 100 : 50},${100 - (row.occupancy / 100) * 88}`))
const chartXAxis = computed(() => {
  const rows = chartRows.value
  if (rows.length <= 6) return rows.map((row, index) => ({ date: row.date, position: rows.length > 1 ? (index / (rows.length - 1)) * 100 : 50 }))
  const indexes = [...new Set([0, Math.round((rows.length - 1) / 4), Math.round((rows.length - 1) / 2), Math.round(((rows.length - 1) * 3) / 4), rows.length - 1])]
  return indexes.map((index) => ({ date: rows[index].date, position: (index / (rows.length - 1)) * 100 }))
})

async function load() {
  loading.value = true
  error.value = ''
  if (invalidPeriod.value) {
    error.value = 'La date de fin doit être postérieure ou égale à la date de début.'
    loading.value = false
    return
  }
  try { data.value = await dashboardService.statistics({ date_from: dateFrom.value, date_to: dateTo.value }) as DashboardStatistics } catch (value: unknown) { error.value = userError(value, 'Impossible de charger les statistiques.', 'STATISTICS_ERROR') } finally { loading.value = false }
}

function formatDate(value: string) { return new Date(`${value}T00:00:00`).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }) }
onMounted(load)
</script>
<template>
	<AppLayout>
		<template #title>Statistiques</template>
    <section class="page-intro"><div><p class="eyebrow">ANALYSE MÉTIER</p><h2>Statistiques d’activité</h2><p>Analyse des départs et réservations enregistrés sur la période choisie.</p></div><div class="period-filter"><label>Du <input v-model="dateFrom" type="date"></label><label>Au <input v-model="dateTo" type="date"></label><button class="primary-button" type="button" :disabled="loading || invalidPeriod" @click="load">Appliquer</button></div></section>
		<p v-if="loading" class="status-msg">Chargement des statistiques…</p><p v-else-if="error" class="error-banner">{{ error }}</p>
		<template v-else-if="data">
      <div class="view-tabs" role="tablist"><button :class="{ active: viewMode === 'trends' }" :aria-selected="viewMode === 'trends'" role="tab" type="button" @click="viewMode = 'trends'">Tendances</button><button :class="{ active: viewMode === 'details' }" :aria-selected="viewMode === 'details'" role="tab" type="button" @click="viewMode = 'details'">Détail des données</button></div>
			<template v-if="viewMode === 'trends'">
        <section class="trend-grid"><BaseCard><div class="trend-panel"><span class="stat-label">Évolution des départs</span><strong>{{ trends.departures.current }} départ(s)</strong><small :class="trends.variations.departures >= 0 ? 'positive' : 'negative'">{{ trends.variations.departures >= 0 ? '+' : '' }}{{ trends.variations.departures }}% par rapport à la période précédente</small></div></BaseCard><BaseCard><div class="trend-panel"><span class="stat-label">Évolution des réservations</span><strong>{{ trends.reservations.current }} réservation(s)</strong><small :class="trends.variations.reservations >= 0 ? 'positive' : 'negative'">{{ trends.variations.reservations >= 0 ? '+' : '' }}{{ trends.variations.reservations }}% par rapport à la période précédente</small></div></BaseCard><BaseCard><div class="trend-panel"><span class="stat-label">Évolution du remplissage</span><strong>{{ trends.occupancy.current }}%</strong><small :class="trends.variations.occupancy >= 0 ? 'positive' : 'negative'">{{ trends.variations.occupancy >= 0 ? '+' : '' }}{{ trends.variations.occupancy }}% par rapport à la période précédente</small></div></BaseCard></section>
        <BaseCard class="main-chart"><div class="card-heading"><div><h2>Évolution quotidienne de l’activité</h2><p>Une tendance nécessite au moins deux dates. Les courbes comparent les départs et réservations (nombre) ainsi que le remplissage (%).</p></div></div><div v-if="chartRows.length < 2" class="single-point-state"><div class="single-point-icon">•</div><strong>Pas encore assez de données pour tracer une évolution</strong><span>{{ chartRows.length ? `Donnée disponible : ${formatDate(chartRows[0].date)}` : 'Aucune donnée sur cette période.' }}</span><small>Élargissez la période ou enregistrez une autre journée d’activité.</small></div><template v-else><div class="chart-shell"><div class="axis-y left"><span>{{ chartMax }}</span><span>{{ Math.round(chartMax / 2) }}</span><span>0</span></div><svg class="trend-chart" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Évolution des départs et réservations par jour"><line x1="0" y1="12" x2="100" y2="12" class="grid-line"/><line x1="0" y1="56" x2="100" y2="56" class="grid-line"/><line x1="0" y1="100" x2="100" y2="100" class="axis-line"/><polyline :points="chartPoints('total').join(' ')" class="line departures-line"/><polyline :points="chartPoints('reservations').join(' ')" class="line reservations-line"/><polyline :points="occupancyPoints.join(' ')" class="line occupancy-line"/></svg><div class="axis-y right"><span>100%</span><span>50%</span><span>0%</span></div></div><div class="axis-x"><span v-for="tick in chartXAxis" :key="tick.date" :style="{ left: `${tick.position}%` }">{{ formatDate(tick.date) }}</span></div><div class="chart-legend"><span><i class="legend departures"></i>Départs (nombre)</span><span><i class="legend reservations"></i>Réservations (nombre)</span><span><i class="legend occupancy"></i>Remplissage (%)</span></div></template></BaseCard>
			</template>
			<section v-else class="content-grid statistics-grid">



				<BaseCard><div class="card-heading"><div><h2>Détail des départs</h2><p>Capacité et remplissage par date.</p></div></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Date</th><th>Départs</th><th>Réservées</th><th>Capacité</th><th>Remplissage</th></tr></thead><tbody><tr v-for="row in data.departs" :key="`detail-${row.date}`"><td>{{ formatDate(row.date) }}</td><td>{{ row.total }}</td><td>{{ row.places_reservees }}</td><td>{{ row.places_total }}</td><td>{{ row.places_total ? Math.round(row.places_reservees * 100 / row.places_total) : 0 }}%</td></tr><tr v-if="!data.departs.length"><td colspan="5" class="empty-state">Aucune donnée.</td></tr></tbody></table></div></BaseCard>
				<BaseCard><div class="card-heading"><div><h2>Itinéraires demandés</h2><p>Classement par réservations.</p></div></div><div class="route-ranking"><div v-for="(row, index) in data.destinations" :key="row.id_itineraire" class="route-row"><span class="rank">{{ Number(index) + 1 }}</span><span>{{ row.libelle || 'Itinéraire #' + row.id_itineraire }}</span><strong>{{ row.reservations }}</strong></div><p v-if="!data.destinations.length" class="empty-state">Aucun itinéraire réservé.</p></div></BaseCard>
			</section>
		</template>
	</AppLayout>
</template>

<style scoped>
.period-filter { display: flex; align-items: end; gap: 0.75rem; }
.period-filter label { display: grid; gap: 0.25rem; color: #64748b; font-size: 0.75rem; }
.period-filter input { min-height: 36px; padding: 0.45rem 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; color: #0f172a; background: #fff; }
.stats-grid { margin-bottom: 1rem; }
.stat-panel { display: grid; min-height: 112px; padding: 1.25rem; gap: 0.2rem; }
.stat-panel strong { color: #0f172a; font-size: 1.8rem; }
.stat-panel small { color: #64748b; }
.statistics-grid { margin-top: 1rem; }
.statistics-grid > .base-card { padding: 1.25rem; }
.view-tabs { display: flex; gap: 0.25rem; margin: 1rem 0; padding: 0.25rem; border-radius: 8px; background: #e2e8f0; width: fit-content; }
.view-tabs button { padding: 0.55rem 0.9rem; border: 0; border-radius: 6px; color: #475569; background: transparent; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.view-tabs button.active { color: #1d4ed8; background: #fff; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.12); }
.trend-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
.trend-panel { display: grid; min-height: 118px; padding: 1.2rem; gap: 0.35rem; }
.trend-panel strong { color: #0f172a; font-size: 1.45rem; }
.trend-panel small { color: #64748b; line-height: 1.35; }
.trend-panel .positive { color: #15803d; }
.trend-panel .negative { color: #b91c1c; }
.main-chart { margin-top: 1rem; padding: 1.25rem; }
.chart-shell { position: relative; display: grid; grid-template-columns: 42px 1fr 42px; gap: 0.5rem; height: 230px; min-height: 230px; margin-top: 1rem; }
.trend-chart { width: 100%; height: 230px; min-height: 0; overflow: hidden; border-left: 1px solid #94a3b8; border-bottom: 1px solid #94a3b8; background: linear-gradient(#fff, #f8fafc); }
.grid-line { stroke: #e2e8f0; stroke-width: 0.5; vector-effect: non-scaling-stroke; }
.axis-line { stroke: #94a3b8; stroke-width: 0.8; vector-effect: non-scaling-stroke; }
.line { fill: none; stroke-width: 1.8; vector-effect: non-scaling-stroke; }
.departures-line { stroke: #2563eb; }
.reservations-line { stroke: #14b8a6; }
.occupancy-line { stroke: #f59e0b; stroke-dasharray: 4 3; }
.axis-y { display: flex; flex-direction: column; justify-content: space-between; padding: 0 0 0.2rem; color: #64748b; font-size: 0.7rem; }
.axis-y.right { text-align: left; }
.axis-x { position: relative; height: 20px; margin: 0.2rem 42px 0 42px; overflow: hidden; color: #64748b; font-size: 0.68rem; }
.axis-x span { position: absolute; top: 0; white-space: nowrap; transform: translateX(-50%); }
.axis-x span:first-child { transform: translateX(0); }
.axis-x span:last-child { transform: translateX(-100%); }
.chart-legend { display: flex; flex-wrap: wrap; gap: 0.75rem 1.25rem; margin-top: 1rem; color: #475569; font-size: 0.78rem; }
.legend { display: inline-block; width: 18px; margin-right: 0.35rem; border-top: 2px solid; vertical-align: middle; }
.legend.departures { border-color: #2563eb; }
.legend.reservations { border-color: #14b8a6; }
.legend.occupancy { border-color: #f59e0b; border-top-style: dashed; }
.single-point-state { display: grid; min-height: 230px; place-items: center; align-content: center; gap: 0.5rem; margin-top: 1rem; padding: 2rem; border: 1px dashed #cbd5e1; border-radius: 8px; color: #475569; text-align: center; background: #f8fafc; }
.single-point-state strong { color: #0f172a; }
.single-point-state small { color: #64748b; }
.single-point-icon { display: grid; width: 42px; height: 42px; place-items: center; border-radius: 50%; color: #2563eb; background: #dbeafe; font-size: 1.8rem; line-height: 1; }
.bar-chart { display: flex; align-items: end; gap: 0.65rem; min-height: 190px; padding-top: 1.25rem; overflow-x: auto; }
.bar-column { display: grid; flex: 1 0 34px; min-width: 34px; height: 165px; grid-template-rows: 20px 1fr 22px; align-items: end; text-align: center; }
.bar-value { color: #475569; font-size: 0.72rem; }
.bar-stack { display: flex; align-items: end; justify-content: center; height: 120px; border-radius: 5px 5px 0 0; background: #e2e8f0; }
.bar-stack span { display: block; width: 100%; min-height: 2px; border-radius: 5px 5px 0 0; background: #2563eb; }
.reservation-chart .bar-stack span { background: #14b8a6; }
.bar-column small { color: #64748b; font-size: 0.68rem; white-space: nowrap; }
.route-ranking { display: grid; gap: 0.75rem; margin-top: 1rem; }
.route-row { display: grid; grid-template-columns: 28px 1fr auto; gap: 0.65rem; align-items: center; padding-bottom: 0.65rem; border-bottom: 1px solid #e2e8f0; color: #475569; }
.route-row strong { color: #0f172a; }
.rank { display: grid; width: 24px; height: 24px; place-items: center; border-radius: 50%; color: #1d4ed8; background: #dbeafe; font-size: 0.75rem; font-weight: 700; }
@media (max-width: 900px) { .trend-grid { grid-template-columns: 1fr; } }
@media (max-width: 767px) { .period-filter { width: 100%; flex-wrap: wrap; } .period-filter label { flex: 1 1 130px; } .period-filter button { width: 100%; } .view-tabs { width: 100%; } .view-tabs button { flex: 1; } .chart-shell { grid-template-columns: 34px 1fr 34px; } .axis-x { margin-left: 34px; margin-right: 34px; } }
</style>
