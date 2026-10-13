<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import ListToolbar from '../../components/ui/ListToolbar.vue'
import PaginationControls from '../../components/ui/PaginationControls.vue'
import { reportsService } from '../../services/reports/service'
import { localIsoDate, daysAgo } from '../../utils/date'
import { userError } from '../../utils/errors'

const type = ref('daily'); const dateFrom = ref(localIsoDate(daysAgo(29))); const dateTo = ref(localIsoDate())
const rows = ref<Array<Record<string, unknown>>>([]); const loading = ref(false); const error = ref(''); const busyExport = ref(false); const search = ref(''); const sortBy = ref(''); const sortOrder = ref<'asc' | 'desc'>('asc'); const page = ref(1); const pageSize = 20
const invalidPeriod = computed(() => !dateFrom.value || !dateTo.value || dateTo.value < dateFrom.value)
const types = [{ value: 'daily', label: 'Départs journaliers' }, { value: 'reservations', label: 'Réservations' }, { value: 'financial', label: 'Financier' }, { value: 'boarding', label: 'Embarquement' }, { value: 'cooperatives', label: 'Par coopérative' }, { value: 'destinations', label: 'Par destination' }]
const columns = computed(() => Object.keys(rows.value[0] || {}))
const columnLabels: Record<string, string> = { date: 'Date', heure: 'Heure', statut: 'Statut', cooperative: 'Coopérative', itineraire: 'Itinéraire', places_reservees: 'Places réservées', capacite: 'Capacité', reservation: 'Réservation', montant: 'Montant', methode: 'Méthode', reference: 'Référence', fournisseur: 'Fournisseur', billet: 'Billet', passager: 'Passager', date_depart: 'Date du départ', date_embarquement: 'Date d’embarquement', reservations: 'Réservations' }
const selectedSortKey = computed(() => sortBy.value || columns.value[0] || '')
const filteredRows = computed(() => {
  const term = search.value.trim().toLowerCase()
  const result = rows.value.filter((row) => !term || Object.values(row).some((value) => String(value ?? '').toLowerCase().includes(term)))
  return result.sort((left, right) => {
    const a = left[selectedSortKey.value]; const b = right[selectedSortKey.value]
    const numericA = Number(a); const numericB = Number(b)
    const comparison = Number.isFinite(numericA) && Number.isFinite(numericB) ? numericA - numericB : String(a ?? '').localeCompare(String(b ?? ''), 'fr', { numeric: true, sensitivity: 'base' })
    return sortOrder.value === 'asc' ? comparison : -comparison
  })
})
const visibleRows = computed(() => filteredRows.value.slice((page.value - 1) * pageSize, page.value * pageSize))
const pages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / pageSize)))
function resetList() { page.value = 1 }
function toggleSort() { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'; resetList() }
function columnLabel(key: string) { return columnLabels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (letter: string) => letter.toUpperCase()) }
function valueText(value: unknown, key: string) { if (value === null || value === undefined || value === '') return '—'; const labels: Record<string, string> = { EN_ATTENTE: 'En attente', CONFIRMEE: 'Confirmée', PAYEE: 'Payée', ANNULEE: 'Annulée', ANNULE: 'Annulé', EXPIREE: 'Expirée', EMBARQUEE: 'Embarquée', TERMINEE: 'Terminée', TERMINE: 'Terminé', PROGRAMME: 'Programmé', EMBARQUEMENT: 'Embarquement', RETARDE: 'Retardé', PARTI: 'Parti', VALIDE: 'Validé', REFUSE: 'Refusé', REMBOURSE: 'Remboursé', ESPECES: 'Espèces' }; return labels[String(value)] || (key === 'montant' && Number.isFinite(Number(value)) ? `${Number(value).toLocaleString('fr-FR')} Ar` : String(value)) }
function showError(value: unknown, fallback: string) { error.value = userError(value, fallback, 'REPORT_ERROR') }
async function load() { resetList(); if (invalidPeriod.value) { error.value = 'La date de fin doit être postérieure ou égale à la date de début.'; rows.value = []; return } loading.value = true; error.value = ''; try { const data = await reportsService.get(type.value, { date_from: dateFrom.value, date_to: dateTo.value }); rows.value = data.rows || []; sortBy.value = Object.keys(rows.value[0] || {})[0] || '' } catch (value: unknown) { showError(value, 'Impossible de charger le rapport.') } finally { loading.value = false } }
async function download(format: 'csv' | 'pdf') { if (invalidPeriod.value) return; busyExport.value = true; error.value = ''; try { const blob = format === 'csv' ? await reportsService.csv(type.value, { date_from: dateFrom.value, date_to: dateTo.value }) : await reportsService.pdf(type.value, { date_from: dateFrom.value, date_to: dateTo.value }); const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `rapport-${type.value}.${format}`; document.body.appendChild(anchor); anchor.click(); anchor.remove(); URL.revokeObjectURL(url) } catch (value: unknown) { showError(value, `Impossible d’exporter le rapport en ${format.toUpperCase()}.`) } finally { busyExport.value = false } }
watch([search, sortBy, sortOrder], resetList)
onMounted(load)
</script>
<template>
  <AppLayout><template #title>Rapports</template><section class="page-intro"><div><p class="eyebrow">PILOTAGE</p><h2>Rapports d’activité</h2><p>Consultez les données filtrées et exportez-les en CSV ou PDF.</p></div><div class="period-filter reports-period-filter"><label>Rapport<select v-model="type" @change="load"><option v-for="item in types" :key="item.value" :value="item.value">{{ item.label }}</option></select></label><label>Du<input v-model="dateFrom" type="date"></label><label>Au<input v-model="dateTo" type="date"></label><button class="primary-button compact-button" type="button" :disabled="loading || invalidPeriod" @click="load">Actualiser</button><button class="secondary-button" type="button" :disabled="loading || busyExport || invalidPeriod || !rows.length" @click="download('csv')">CSV</button><button class="secondary-button" type="button" :disabled="loading || busyExport || invalidPeriod" @click="download('pdf')">PDF</button></div></section><p v-if="loading" class="status-msg">Chargement du rapport…</p><p v-else-if="error" class="error-banner" role="alert">{{ error }}</p><BaseCard v-else><div class="card-heading"><div><h2>{{ types.find(item => item.value === type)?.label }} ({{ filteredRows.length }})</h2><p>Recherchez dans les résultats puis triez la colonne utile.</p></div></div><ListToolbar v-model="search" :loading="loading" placeholder="Rechercher dans le rapport" :sort-label="sortOrder === 'asc' ? 'Tri croissant ↑' : 'Tri décroissant ↓'" @search="resetList" @sort="toggleSort" /><div class="filter-row"><select v-model="sortBy" aria-label="Colonne de tri" @change="resetList"><option v-for="key in columns" :key="key" :value="key">Trier par : {{ key }}</option></select></div><div v-if="filteredRows.length" class="table-scroll"><table class="data-table"><caption>{{ types.find(item => item.value === type)?.label }}</caption><thead><tr><th v-for="key in columns" :key="key">{{ columnLabel(key) }}</th></tr></thead><tbody><tr v-for="(row, index) in visibleRows" :key="index"><td v-for="key in columns" :key="key">{{ valueText(row[key], key) }}</td></tr></tbody></table></div><div v-else class="empty-state">Aucune donnée ne correspond aux filtres.</div><PaginationControls :page="page" :pages="pages" :total="filteredRows.length" item-label="ligne(s)" @change="page = $event" /></BaseCard></AppLayout>
</template>
<style scoped>
.reports-period-filter { display: flex; align-items: end; gap: .6rem; flex-wrap: wrap; }
.reports-period-filter label { display: grid; gap: .25rem; color: #64748b; font-size: .75rem; }
.reports-period-filter input, .reports-period-filter select { min-height: 36px; padding: 0 .6rem; border: 1px solid #dfe5f0; border-radius: .65rem; color: #192238; background: #fff; font: inherit; }
</style>
