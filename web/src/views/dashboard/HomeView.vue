<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import StatCard from '../../components/ui/StatCard.vue'
import { dashboardService } from '../../services/dashboard/service'
import { userError } from '../../utils/errors'

const data = ref<any>(null)
const loading = ref(true)
const error = ref('')
const stats = ref<Array<{ label: string; value: string; detail: string; icon: string; tone: string }>>([])

function buildStats(value: any) {
  stats.value = [
    { label: 'Départs aujourd’hui', value: String(value.departs_du_jour ?? 0), detail: 'Départs programmés', icon: '◷', tone: 'stat-blue' },
    { label: 'Réservations', value: String(value.reservations_du_jour ?? 0), detail: 'Réservations actives', icon: '▤', tone: 'stat-purple' },
    { label: 'Coopératives actives', value: String(value.cooperatives_actives ?? 0), detail: 'Données réelles', icon: '♧', tone: 'stat-orange' },
    { label: 'Recettes du jour', value: `${value.recettes_du_jour ?? 0}`, detail: 'Paiements enregistrés', icon: '◈', tone: 'stat-green' },
  ]
}

async function load() {
  try { data.value = await dashboardService.summary(); buildStats(data.value) }
  catch (value: unknown) { error.value = userError(value, 'Le tableau de bord est momentanément indisponible.', 'DASHBOARD_ERROR') }
  finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>Vue d’ensemble</template>
    <section class="page-intro"><div><span class="eyebrow">AUJOURD’HUI</span><h2>Bonjour, bienvenue</h2><p>Les indicateurs sont calculés depuis les données métier réelles.</p></div><RouterLink class="secondary-button" to="/statistiques">Voir les statistiques</RouterLink></section>
    <p v-if="loading" class="status-msg">Chargement du tableau de bord…</p><p v-else-if="error" class="error-banner">{{ error }}</p>
    <template v-else>
      <section class="stats-grid"><StatCard v-for="stat in stats" :key="stat.label" v-bind="stat" /></section>
      <section class="content-grid">
        <BaseCard><div class="card-heading"><div><h2>Prochains départs</h2><p>Départs à venir issus du planning.</p></div><RouterLink class="card-link" to="/departs">Voir tout →</RouterLink></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Date</th><th>Heure</th><th>Itinéraire</th><th>Statut</th></tr></thead><tbody><tr v-for="item in data.departs_imminents" :key="item.id"><td>{{ item.date_depart }}</td><td>{{ item.heure_depart?.slice(0, 5) }}</td><td>#{{ item.id_itineraire }}</td><td>{{ item.statut }}</td></tr><tr v-if="!data.departs_imminents?.length"><td colspan="4" class="empty-state">Aucun départ à venir.</td></tr></tbody></table></div></BaseCard>
        <BaseCard><div class="card-heading"><div><h2>Activité du jour</h2><p>Capacité et fréquentation.</p></div><RouterLink class="card-link" to="/reservations">Réservations →</RouterLink></div><div class="detail-grid"><div class="detail-item"><span class="detail-label">Places disponibles</span><strong>{{ data.places_disponibles }}</strong></div><div class="detail-item"><span class="detail-label">Véhicules actifs</span><strong>{{ data.vehicules_actifs }}</strong></div><div class="detail-item"><span class="detail-label">Chauffeurs actifs</span><strong>{{ data.chauffeurs_actifs }}</strong></div><div class="detail-item"><span class="detail-label">Passagers du jour</span><strong>{{ data.passagers_du_jour }}</strong></div></div></BaseCard>
      </section>
    </template>
  </AppLayout>
</template>
