<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import PaginationControls from "../../components/ui/PaginationControls.vue";
import SearchSelect from "../../components/ui/SearchSelect.vue";
import type { Chauffeur } from "../../models/chauffeur/model";
import type { Depart, DepartStatus } from "../../models/depart/model";
import { chauffeurService } from "../../services/chauffeur/service";
import { departService } from "../../services/depart/service";
import { allPages } from "../../services/pagination";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { localIsoDate } from "../../utils/date";
import { userError } from "../../utils/errors";
import { useAutoRefresh } from "../../composables/useAutoRefresh";

const auth = useAuthenticationStore();
const items = ref<Depart[]>([]);
const chauffeurs = ref<Chauffeur[]>([]);
const loading = ref(true);
const refreshing = ref(false);
const error = ref("");
const actionError = ref("");
const success = ref("");
const busyId = ref<number | null>(null);
const page = ref(1);
const pageSize = 6;
const activePanel = ref<"active" | "history">("active");
const historyItems = ref<Depart[]>([]);
const historyLoading = ref(false);
const historyError = ref("");
const historyLoaded = ref(false);
const historyPage = ref(1);
const historyPageSize = 15;
const selectedChauffeur = ref("");
const historyFrom = ref("");
const historyTo = ref("");

const isDriver = computed(() => [auth.user?.role, ...(auth.user?.roles || []).map((role) => role.libelle)]
  .filter(Boolean).map((role) => String(role).toLowerCase()).includes("chauffeur"));
const statusLabels: Record<DepartStatus, string> = { PROGRAMME: "Programmé", EMBARQUEMENT: "Embarquement", RETARDE: "Retardé", PARTI: "Parti", TERMINE: "Terminé", ANNULE: "Annulé" };
const statusClass = (status: DepartStatus) => ({ PROGRAMME: "planned", EMBARQUEMENT: "boarding", RETARDE: "late", PARTI: "departed", TERMINE: "arrived", ANNULE: "cancelled" })[status];
const routeName = (item: Depart) => `${item.itineraire?.destination_depart?.nom || `#${item.id_itineraire}`} → ${item.itineraire?.destination_arrivee?.nom || "Destination"}`;
const shortDate = (value: string) => new Date(`${value}T12:00:00`).toLocaleDateString("fr-FR", { weekday: "short", day: "2-digit", month: "short" });
const formatTime = (value?: string | null) => value ? new Date(value).toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "Non pointé";
const canLeave = (item: Depart) => ["PROGRAMME", "EMBARQUEMENT", "RETARDE"].includes(item.statut);
const canArrive = (item: Depart) => item.statut === "PARTI";
const chauffeurLabel = (chauffeur: Chauffeur) => `${chauffeur.user?.first_name || ""} ${chauffeur.user?.name || ""}`.trim() || `Chauffeur #${chauffeur.id}`;
const historyDriverName = (item: Depart) => chauffeurs.value.find((value) => value.id === item.id_chauffeur)?.user
  ? chauffeurLabel(chauffeurs.value.find((value) => value.id === item.id_chauffeur)!)
  : item.chauffeur?.numero_permis || `Chauffeur #${item.id_chauffeur}`;

const operationalItems = computed(() => items.value.filter((item) => !["TERMINE", "ANNULE"].includes(item.statut)));
const pages = computed(() => Math.max(Math.ceil(operationalItems.value.length / pageSize), 1));
const visibleItems = computed(() => operationalItems.value.slice((page.value - 1) * pageSize, page.value * pageSize));
const inTransit = computed(() => operationalItems.value.filter((item) => item.statut === "PARTI").length);
const attention = computed(() => operationalItems.value.filter((item) => ["RETARDE", "EMBARQUEMENT"].includes(item.statut)).length);
const historyPages = computed(() => Math.max(Math.ceil(historyItems.value.length / historyPageSize), 1));
const visibleHistory = computed(() => historyItems.value.slice((historyPage.value - 1) * historyPageSize, historyPage.value * historyPageSize));

function rangeDate(amount: number) { const value = new Date(); value.setDate(value.getDate() + amount); return localIsoDate(value); }
async function loadChauffeurs() {
  if (isDriver.value) return;
  try { chauffeurs.value = (await allPages((params) => chauffeurService.listChauffeurs(params), { page: 1, page_size: 100, sort_by: "created_at", sort_order: "asc" })).items || []; }
  catch { chauffeurs.value = []; }
}
async function load(showLoader = true) {
  if (showLoader) loading.value = true; else refreshing.value = true;
  error.value = "";
  try {
    const params = { page: 1, page_size: 100, sort_by: "date_depart", sort_order: "asc", date_from: rangeDate(-1), date_to: rangeDate(7) };
    const result = isDriver.value ? await allPages((next) => departService.listMine(next), params) : await allPages((next) => departService.list(next), params);
    items.value = result.items || []; page.value = 1;
  } catch (value: unknown) { error.value = userError(value, "Impossible de charger le suivi des pointages.", "DRIVER_POINTAGE_WEB_ERROR"); }
  finally { loading.value = false; refreshing.value = false; }
}
async function loadHistory() {
  historyLoading.value = true; historyError.value = "";
  try {
    const params = { page: 1, page_size: 100, date_from: historyFrom.value || undefined, date_to: historyTo.value || undefined, sort_by: "date_depart", sort_order: "desc" };
    const result = isDriver.value ? await allPages((next) => departService.listMine(next), params) : await allPages((next) => departService.list(next), { ...params, id_chauffeur: selectedChauffeur.value ? Number(selectedChauffeur.value) : undefined });
    historyItems.value = (result.items || []).filter((item: Depart) => item.date_heure_depart || item.date_heure_arrivee);
    historyLoaded.value = true; historyPage.value = 1;
  } catch (value: unknown) { historyError.value = userError(value, "Impossible de charger l’historique des pointages.", "DRIVER_POINTAGE_HISTORY_ERROR"); }
  finally { historyLoading.value = false; }
}
async function point(item: Depart, type: "DEPART" | "ARRIVEE") {
  if (busyId.value || !window.confirm(`Confirmer ${type === "DEPART" ? "le départ" : "l’arrivée"} pour ${routeName(item)} ?`)) return;
  busyId.value = item.id; actionError.value = ""; success.value = "";
  try {
    Object.assign(item, await departService.pointage(item.id, type));
    success.value = type === "DEPART" ? "Départ enregistré : le véhicule est maintenant en route." : "Arrivée enregistrée : le trajet est terminé.";
    if (historyLoaded.value) await loadHistory();
  } catch (value: unknown) { actionError.value = userError(value, "Le pointage n’a pas été enregistré.", "DRIVER_POINTAGE_ACTION_ERROR"); }
  finally { busyId.value = null; }
}
useAutoRefresh(() => load(false), 45_000);
onMounted(async () => { await Promise.all([load(), loadChauffeurs()]); await loadHistory(); });
</script>

<template>
  <AppLayout>
    <template #title>Pointage chauffeur</template>
    <section class="page-intro"><div><p class="eyebrow">SUIVI OPÉRATIONNEL</p><h2>Pointage des chauffeurs</h2><p>Une vue courte des trajets à pointer, séparée de l’historique.</p></div><button class="secondary-button" type="button" :disabled="loading || refreshing" @click="load(false)">{{ refreshing ? "Actualisation…" : "Actualiser" }}</button></section>
    <p v-if="error" class="error-banner" role="alert">{{ error }} <button class="text-button" type="button" @click="load()">Réessayer</button></p>
    <p v-if="success" class="success-banner" role="status">{{ success }}</p><p v-if="actionError" class="error-banner" role="alert">{{ actionError }}</p>

    <section class="pointage-summary" aria-label="Résumé des pointages"><div><small>À suivre sur 7 jours</small><strong>{{ operationalItems.length }}</strong></div><div><small>En route</small><strong>{{ inTransit }}</strong></div><div><small>À surveiller</small><strong>{{ attention }}</strong></div><div><small>Fenêtre affichée</small><strong>{{ rangeDate(-1) }} → {{ rangeDate(7) }}</strong></div></section>

    <nav class="pointage-tabs" aria-label="Sections du pointage">
      <button type="button" :class="{ active: activePanel === 'active' }" @click="activePanel = 'active'">À pointer <span>{{ operationalItems.length }}</span></button>
      <button type="button" :class="{ active: activePanel === 'history' }" @click="activePanel = 'history'">Historique <span>{{ historyItems.length }}</span></button>
    </nav>

    <BaseCard v-if="activePanel === 'active'" class="operations-card">
      <div class="card-heading"><div><p class="eyebrow">À POINTER</p><h2>Départs actifs</h2><p>Seulement les trajets utiles maintenant et dans les sept prochains jours.</p></div><span class="result-count">{{ operationalItems.length }} trajet{{ operationalItems.length > 1 ? "s" : "" }}</span></div>
      <p v-if="loading" class="status-msg">Chargement des départs…</p>
      <div v-else-if="!operationalItems.length" class="empty-state"><strong>Aucun départ à suivre.</strong><span>Les prochains départs affectés apparaîtront ici.</span></div>
      <div v-else class="pointage-table-wrap"><table class="pointage-table"><thead><tr><th>Prévu</th><th>Trajet</th><th>Ressources</th><th>État</th><th>Pointage réel</th><th>Action</th></tr></thead><tbody>
        <tr v-for="item in visibleItems" :key="item.id">
          <td data-label="Prévu"><strong>{{ shortDate(item.date_depart) }}</strong><small>{{ item.heure_depart.slice(0, 5) }}</small></td>
          <td data-label="Trajet"><strong>{{ routeName(item) }}</strong><small>{{ item.gare?.nom || "Gare non renseignée" }} · {{ item.vehicule?.immatriculation || `Véhicule #${item.id_vehicule}` }}</small></td>
          <td data-label="Ressources"><strong>{{ item.vehicule?.immatriculation || `Véhicule #${item.id_vehicule}` }}</strong><small>{{ item.cooperative?.nom || "Coopérative" }} · {{ item.places_reservees }}/{{ item.nombre_places }} places</small></td>
          <td data-label="État"><span :class="['pointage-status', statusClass(item.statut)]">{{ statusLabels[item.statut] }}</span></td>
          <td data-label="Pointage"><small>Départ : {{ formatTime(item.date_heure_depart) }}</small><small>Arrivée : {{ formatTime(item.date_heure_arrivee) }}</small></td>
          <td data-label="Action"><div class="row-actions"><button v-if="isDriver && canLeave(item)" class="primary-button compact-button" type="button" :disabled="busyId === item.id" @click="point(item, 'DEPART')">Pointer départ</button><button v-if="isDriver && canArrive(item)" class="primary-button compact-button" type="button" :disabled="busyId === item.id" @click="point(item, 'ARRIVEE')">Pointer arrivée</button><RouterLink class="secondary-button compact-button" :to="`/departs/${item.id}`">Détail</RouterLink></div></td>
        </tr>
      </tbody></table></div>
      <PaginationControls v-if="!loading && operationalItems.length > pageSize" :page="page" :pages="pages" :total="operationalItems.length" item-label="trajet(s)" @change="page = $event" />
    </BaseCard>

    <BaseCard v-else class="history-card">
      <div class="card-heading history-heading"><div><p class="eyebrow">HISTORIQUE</p><h2>Pointages enregistrés</h2><p>Filtrez l’archive sans allonger la liste des actions courantes.</p></div><button class="secondary-button" type="button" :disabled="historyLoading" @click="loadHistory">{{ historyLoading ? "Chargement…" : "Rechercher" }}</button></div>
      <form class="history-filters" @submit.prevent="loadHistory"><label v-if="!isDriver" class="form-field"><span>Chauffeur</span><SearchSelect v-model="selectedChauffeur" :options="chauffeurs.map((chauffeur) => ({ value: String(chauffeur.id), label: `${chauffeurLabel(chauffeur)} · ${chauffeur.numero_permis}` }))" placeholder="Tous les chauffeurs" /></label><label class="form-field"><span>Du</span><input v-model="historyFrom" type="date" /></label><label class="form-field"><span>Au</span><input v-model="historyTo" type="date" /></label></form>
      <p v-if="historyError" class="error-banner" role="alert">{{ historyError }}</p><p v-else-if="historyLoading" class="status-msg">Chargement de l’historique…</p>
      <div v-else-if="historyLoaded && !historyItems.length" class="empty-state"><strong>Aucun pointage trouvé.</strong><span>Modifiez les dates ou le chauffeur.</span></div>
      <div v-else class="history-table-wrap"><table class="pointage-table"><thead><tr><th>Chauffeur</th><th>Trajet prévu</th><th>Départ réel</th><th>Arrivée réelle</th><th>Statut</th></tr></thead><tbody><tr v-for="item in visibleHistory" :key="`history-${item.id}`"><td><strong>{{ historyDriverName(item) }}</strong><small>{{ item.chauffeur?.numero_permis || `#${item.id_chauffeur}` }}</small></td><td><strong>{{ routeName(item) }}</strong><small>{{ shortDate(item.date_depart) }} · {{ item.heure_depart.slice(0, 5) }}</small></td><td>{{ formatTime(item.date_heure_depart) }}</td><td>{{ formatTime(item.date_heure_arrivee) }}</td><td><span :class="['pointage-status', statusClass(item.statut)]">{{ statusLabels[item.statut] }}</span></td></tr></tbody></table></div>
      <PaginationControls v-if="!historyLoading && historyItems.length > historyPageSize" :page="historyPage" :pages="historyPages" :total="historyItems.length" item-label="pointage(s)" @change="historyPage = $event" />
    </BaseCard>
  </AppLayout>
</template>

<style scoped>
.pointage-summary { display: grid; grid-template-columns: repeat(3, minmax(130px, 0.7fr)) minmax(220px, 1.4fr); gap: 1px; margin-bottom: 1rem; overflow: hidden; border: 1px solid var(--line); border-radius: 12px; background: var(--line); }
.pointage-summary > div { display: grid; gap: 0.15rem; padding: 0.8rem 1rem; background: #fff; }.pointage-summary small { color: var(--ink-muted); font-size: 0.72rem; }.pointage-summary strong { color: var(--ink-strong); font-size: 1rem; }
.pointage-tabs { display: inline-flex; gap: 0.25rem; margin-bottom: 1rem; padding: 0.25rem; border: 1px solid var(--line); border-radius: 10px; background: #f6f8f6; }.pointage-tabs button { display: flex; align-items: center; gap: 0.45rem; min-height: 38px; padding: 0.45rem 0.8rem; color: var(--ink-muted); border: 0; border-radius: 8px; background: transparent; font-size: 0.8rem; font-weight: 750; }.pointage-tabs button.active { color: #fff; background: var(--brand-dark); }.pointage-tabs span { display: grid; place-items: center; min-width: 21px; height: 21px; padding: 0 0.25rem; border-radius: 6px; color: inherit; background: #ffffff24; font-size: 0.67rem; }
.result-count { padding: 0.3rem 0.6rem; color: var(--brand-dark); border-radius: 99px; background: var(--brand-soft); font-size: 0.75rem; font-weight: 800; }
.pointage-table-wrap, .history-table-wrap { overflow-x: auto; }.pointage-table { width: 100%; min-width: 900px; border-collapse: collapse; }.pointage-table th, .pointage-table td { padding: 0.75rem; border-top: 1px solid var(--line); text-align: left; vertical-align: middle; font-size: 0.8rem; }.pointage-table th { color: var(--ink-muted); background: #f8faf8; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.05em; }.pointage-table td strong, .pointage-table td small { display: block; }.pointage-table td strong { color: var(--ink-strong); }.pointage-table td small { margin-top: 0.2rem; color: var(--ink-muted); }
.pointage-status { display: inline-flex; padding: 0.3rem 0.55rem; border-radius: 99px; font-size: 0.68rem; font-weight: 800; white-space: nowrap; }.pointage-status.planned { color: #496174; background: #edf2f6; }.pointage-status.boarding { color: #8d5a00; background: #fff2d8; }.pointage-status.late, .pointage-status.cancelled { color: #a13f36; background: #fff0ed; }.pointage-status.departed { color: #70458e; background: #f5edfb; }.pointage-status.arrived { color: #16704d; background: #e8f8ef; }
.row-actions { display: flex; justify-content: flex-end; gap: 0.4rem; }.history-card { margin-top: 1rem; }.history-filters { display: grid; grid-template-columns: minmax(220px, 1.5fr) repeat(2, minmax(150px, 1fr)); gap: 0.8rem; margin: 1rem 0; }.history-filters .form-field { display: grid; gap: 0.35rem; }.history-filters span { color: var(--ink-muted); font-size: 0.75rem; font-weight: 700; }.history-filters input { min-height: 42px; }
@media (max-width: 900px) { .pointage-summary { grid-template-columns: 1fr 1fr; } }
@media (max-width: 700px) {
  .pointage-summary { grid-template-columns: 1fr 1fr; }.pointage-summary > div:last-child { grid-column: 1 / -1; }
  .history-filters { grid-template-columns: 1fr; }
  .pointage-table { min-width: 0; }.pointage-table thead { display: none; }.pointage-table tbody, .pointage-table tr, .pointage-table td { display: block; width: 100%; }.pointage-table tr { display: grid; gap: 0.45rem; margin-bottom: 0.75rem; padding: 0.75rem; border: 1px solid var(--line); border-radius: 10px; }.pointage-table td { display: grid; grid-template-columns: 88px minmax(0, 1fr); gap: 0.5rem; padding: 0; border: 0; }.pointage-table td::before { content: attr(data-label); color: var(--ink-muted); font-size: 0.68rem; font-weight: 700; text-transform: uppercase; }.history-table-wrap .pointage-table td { display: block; }.history-table-wrap .pointage-table td::before { display: none; }.row-actions { justify-content: stretch; }.row-actions > * { flex: 1; }
  .operations-card .pointage-table td:nth-child(3), .operations-card .pointage-table td:nth-child(5) { display: none; }
}
</style>
