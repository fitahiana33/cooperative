<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import ListToolbar from "../../components/ui/ListToolbar.vue";
import OperationalFilters from "../../components/ui/OperationalFilters.vue";
import PaginationControls from "../../components/ui/PaginationControls.vue";
import SearchSelect from "../../components/ui/SearchSelect.vue";
import TableViewControls from "../../components/ui/TableViewControls.vue";
import { useOperationalCatalog } from "../../composables/useOperationalCatalog";
import { useSessionFilters } from "../../composables/useSessionFilters";
import { useAutoRefresh } from "../../composables/useAutoRefresh";
import type { Billet } from "../../models/billet/model";
import { billetService } from "../../services/billet/service";
import { userError } from "../../utils/errors";

const items = ref<Billet[]>([]);
const search = ref("");
const status = ref("");
const sortBy = ref("date_emission");
const sortOrder = ref<"asc" | "desc">("desc");
const dateFrom = ref("");
const dateTo = ref("");
const cooperativeId = ref<number | null>(null);
const gareId = ref<number | null>(null);
const routeId = ref<number | null>(null);
const page = ref(1);
const pages = ref(1);
const total = ref(0);
const loading = ref(true);
const error = ref("");
const tableDensity = ref<"compact" | "comfortable">("comfortable");
const ticketColumns = [
  { id: "ticket", label: "Billet", locked: true }, { id: "passenger", label: "Passager" }, { id: "trip", label: "Voyage" }, { id: "coop", label: "Coopérative" }, { id: "seat", label: "Place" }, { id: "price", label: "Tarif" }, { id: "status", label: "Statut" }, { id: "actions", label: "Actions", locked: true },
];
const visibleTicketColumns = ref(ticketColumns.map((column) => column.id));
const { gareOptions, cooperativeOptions, routeOptions, loadingCatalog, loadCatalog } = useOperationalCatalog();

const activeFilterCount = computed(() => [search.value, status.value, dateFrom.value, dateTo.value, cooperativeId.value, gareId.value, routeId.value].filter(Boolean).length);
useSessionFilters("billets", { search, status, sortBy, sortOrder, dateFrom, dateTo, cooperativeId, gareId, routeId });

function statusLabel(value: string) {
  return ({ VALIDE: "Valide", UTILISE: "Utilisé", ANNULE: "Annulé", EXPIRE: "Expiré" } as Record<string, string>)[value] || value;
}
function statusTone(value: string) {
  return value === "VALIDE" ? "active" : value === "UTILISE" ? "neutral" : "inactive";
}
function money(value?: number, currency?: string) {
  if (value == null) return "—";
  return `${Number(value).toLocaleString("fr-FR")} ${currency || "Ar"}`;
}
async function load(silent = false) {
  if (!silent) loading.value = true;
  error.value = "";
  try {
    const result = await billetService.list({
      page: page.value,
      page_size: 20,
      search: search.value || undefined,
      statut: status.value || undefined,
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      id_cooperative: cooperativeId.value || undefined,
      id_gare: gareId.value || undefined,
      id_itineraire: routeId.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    });
    items.value = result.items;
    total.value = result.total;
    pages.value = Math.max(result.pages || 1, 1);
  } catch (value: unknown) {
    error.value = userError(value, "Impossible de charger les billets.", "BILLETS_LIST_ERROR");
  } finally { if (!silent) loading.value = false; }
}
function resetFilters() {
  search.value = ""; status.value = ""; dateFrom.value = ""; dateTo.value = "";
  cooperativeId.value = null; gareId.value = null; routeId.value = null; page.value = 1;
  void load();
}
function toggleSort() { sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc"; page.value = 1; void load(); }
function changePage(next: number) { page.value = next; void load(); }
useAutoRefresh(() => load(true));
onMounted(() => Promise.all([load(), loadCatalog()]));
</script>

<template>
  <AppLayout>
    <template #title>Billets & QR Code</template>
    <section class="page-intro">
      <div><p class="eyebrow">RÉSERVATIONS</p><h2>Billets & QR Code</h2><p>Retrouvez chaque titre de transport selon son réseau, son trajet et son voyage.</p></div>
    </section>
    <BaseCard>
      <div class="card-heading"><div><h2>Registre des billets ({{ total }})</h2><p>Recherche par billet, réservation ou nom du passager.</p></div></div>
      <ListToolbar v-model="search" :loading="loading" placeholder="Billet, réservation ou passager" :sort-label="sortOrder === 'asc' ? 'Plus anciens' : 'Plus récents'" @search="page = 1; load()" @sort="toggleSort" />
      <OperationalFilters :active-count="activeFilterCount" :loading="loading || loadingCatalog" title="Afficher les billets selon…" description="Réseau, trajet, période, statut et ordre de lecture." @apply="page = 1; load()" @reset="resetFilters">
        <label class="form-field"><span>Statut</span><select v-model="status"><option value="">Tous les statuts</option><option value="VALIDE">Valide</option><option value="UTILISE">Utilisé</option><option value="ANNULE">Annulé</option><option value="EXPIRE">Expiré</option></select></label>
        <label class="form-field"><span>Gare</span><SearchSelect v-model="gareId" :options="gareOptions" :empty-value="null" placeholder="Toutes les gares" /></label>
        <label class="form-field"><span>Coopérative</span><SearchSelect v-model="cooperativeId" :options="cooperativeOptions" :empty-value="null" placeholder="Toutes les coopératives" /></label>
        <label class="form-field"><span>Trajet</span><SearchSelect v-model="routeId" :options="routeOptions" :empty-value="null" placeholder="Tous les trajets" /></label>
        <label class="form-field"><span>Départ du</span><input v-model="dateFrom" type="date" /></label>
        <label class="form-field"><span>Départ au</span><input v-model="dateTo" type="date" /></label>
        <label class="form-field"><span>Trier par</span><select v-model="sortBy"><option value="date_emission">Date d’émission</option><option value="numero_billet">Numéro du billet</option><option value="numero_reservation">Réservation</option><option value="statut">Statut</option></select></label>
        <template #summary><span class="filter-summary">{{ total }} billet{{ total > 1 ? "s" : "" }} dans la sélection</span></template>
      </OperationalFilters>
      <p v-if="loading" class="status-msg">Chargement des billets…</p>
      <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
      <TableViewControls v-if="!loading && !error" v-model:density="tableDensity" v-model:visible-columns="visibleTicketColumns" storage-key="billets" :columns="ticketColumns" />
      <div v-if="!loading && !error" class="table-scroll ticket-table-wrap">
        <table :class="['data-table', `table-density-${tableDensity}`, ...visibleTicketColumns.map((column) => `show-${column}`)]">
          <caption class="sr-only">Billets générés</caption>
          <thead><tr><th>Billet / réservation</th><th>Passager</th><th>Voyage</th><th>Coopérative</th><th>Place</th><th>Tarif</th><th>Statut</th><th></th></tr></thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td><strong>{{ item.numero_billet }}</strong><br /><small>{{ item.numero_reservation || "—" }}</small></td>
              <td><strong>{{ item.nom_passager || "Non renseigné" }}</strong><br /><small>{{ item.telephone_passager || "—" }}</small></td>
              <td><strong>{{ item.destination_depart || "—" }} → {{ item.destination_arrivee || "—" }}</strong><br /><small>{{ item.date_depart }} · {{ item.heure_depart?.slice(0, 5) }}</small></td>
              <td>{{ item.nom_cooperative || "—" }}</td><td>{{ item.numero_place || "—" }}</td><td>{{ money(item.prix, item.devise) }}</td>
              <td><span :class="['status-badge', statusTone(item.statut)]">{{ statusLabel(item.statut) }}</span></td>
              <td><RouterLink class="table-action table-link" :to="`/billets/${item.id}`">Détails</RouterLink></td>
            </tr>
            <tr v-if="!items.length"><td colspan="8" class="empty-state">Aucun billet pour ces critères.</td></tr>
          </tbody>
        </table>
      </div>
      <PaginationControls v-if="!loading && !error" :page="page" :pages="pages" :total="total" item-label="billet(s)" @change="changePage" />
    </BaseCard>
  </AppLayout>
</template>

<style scoped>
.data-table:not(.show-passenger) :is(th:nth-child(2), td:nth-child(2)), .data-table:not(.show-trip) :is(th:nth-child(3), td:nth-child(3)), .data-table:not(.show-coop) :is(th:nth-child(4), td:nth-child(4)), .data-table:not(.show-seat) :is(th:nth-child(5), td:nth-child(5)), .data-table:not(.show-price) :is(th:nth-child(6), td:nth-child(6)), .data-table:not(.show-status) :is(th:nth-child(7), td:nth-child(7)) { display: none; }
.table-density-compact :deep(th) { padding-block: .55rem; }.table-density-compact :deep(td) { padding-block: .55rem; }
.ticket-table-wrap { max-height: 650px; overflow: auto; }
.ticket-table-wrap thead { position: sticky; top: 0; z-index: 1; }
.ticket-table-wrap td:first-child strong { white-space: nowrap; }
</style>
