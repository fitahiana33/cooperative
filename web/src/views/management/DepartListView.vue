<script setup lang="ts">
import { allPages } from "../../services/pagination";
import { useSessionFilters } from "../../composables/useSessionFilters";
import SearchSelect from "../../components/ui/SearchSelect.vue";
import OperationalFilters from "../../components/ui/OperationalFilters.vue";
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import PaginationControls from "../../components/ui/PaginationControls.vue";
import ListToolbar from "../../components/ui/ListToolbar.vue";
import SensitiveActionDialog from "../../components/ui/SensitiveActionDialog.vue";
import TableViewControls from "../../components/ui/TableViewControls.vue";
import type { Caisse } from "../../models/finance/model";
import type { Depart, DepartStatus } from "../../models/depart/model";
import { departService } from "../../services/depart/service";
import { financeService } from "../../services/finance/service";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { userError } from "../../utils/errors";
import { useOperationalCatalog } from "../../composables/useOperationalCatalog";
import { useAutoRefresh } from "../../composables/useAutoRefresh";

const auth = useAuthenticationStore();
const items = ref<Depart[]>([]);
const caisses = ref<Caisse[]>([]);
const cancelCaisseId = ref<number | null>(null);
const total = ref(0);
const page = ref(1);
const pages = ref(1);
const search = ref("");
const status = ref<DepartStatus | "">("");
const dateFrom = ref("");
const dateTo = ref("");
const cooperativeId = ref<number | null>(null);
const gareId = ref<number | null>(null);
const routeId = ref<number | null>(null);
const sortOrder = ref<"asc" | "desc">("asc");
const loading = ref(true);
const busy = ref<number | null>(null);
const cancelTarget = ref<Depart | null>(null);
const cancellationApproved = ref(false);
const error = ref("");
const success = ref("");
const tableDensity = ref<"compact" | "comfortable">("comfortable");
const departColumns = [
  { id: "schedule", label: "Date / heure", locked: true }, { id: "route", label: "Itinéraire" }, { id: "station", label: "Gare" }, { id: "coop", label: "Coopérative" }, { id: "vehicle", label: "Véhicule" }, { id: "places", label: "Places" }, { id: "load", label: "Remplissage" }, { id: "status", label: "Statut" }, { id: "actions", label: "Actions", locked: true },
];
const visibleDepartColumns = ref(departColumns.map((column) => column.id));
const canCreate = () => auth.hasPermission("DEPART_CREATE");
const canUpdate = () => auth.hasPermission("DEPART_UPDATE");
const canCancel = () => auth.hasPermission("DEPART_CANCEL");
const canProcessRefund = () => auth.hasPermission("PAIEMENT_REFUND");
const statusLabels: Record<DepartStatus, string> = {
  PROGRAMME: "Programmé",
  EMBARQUEMENT: "Embarquement",
  RETARDE: "Retardé",
  PARTI: "Parti",
  TERMINE: "Terminé",
  ANNULE: "Annulé",
};
const { gareOptions, cooperativeOptions, routeOptions, loadingCatalog, loadCatalog } = useOperationalCatalog();
const activeFilterCount = computed(() => [search.value, status.value, dateFrom.value, dateTo.value, cooperativeId.value, gareId.value, routeId.value].filter(Boolean).length);
useSessionFilters("departs", { search, status, dateFrom, dateTo, sortOrder, cooperativeId, gareId, routeId });
function routeName(item: Depart) {
  return `${item.itineraire?.destination_depart?.nom || `#${item.id_itineraire}`} → ${item.itineraire?.destination_arrivee?.nom || ""}`;
}
function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString("fr-FR");
}
function showError(value: unknown, fallback: string) {
  error.value = userError(value, fallback, "DEPARTS_LIST_ERROR");
  success.value = "";
}
async function loadCaisses() {
  if (!canProcessRefund()) return;
  try {
    const result = await allPages((params) => financeService.caisses(params), { page: 1, page_size: 100 });
    caisses.value = (result.items || result).filter(
      (caisse: Caisse) => caisse.statut === "OUVERTE",
    );
  } catch (value: unknown) {
    showError(value, "Impossible de charger les caisses ouvertes.");
  }
}
async function load(silent = false) {
  if (!silent) loading.value = true;
  error.value = "";
  try {
    const result = await departService.list({
      page: page.value,
      page_size: 20,
      search: search.value || undefined,
      statut: status.value || undefined,
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      id_cooperative: cooperativeId.value || undefined,
      id_gare: gareId.value || undefined,
      id_itineraire: routeId.value || undefined,
      sort_by: "date_depart",
      sort_order: sortOrder.value,
    });
    items.value = result.items;
    total.value = result.total;
    pages.value = result.pages || 1;
  } catch (value: unknown) {
    showError(value, "Impossible de charger les départs.");
  } finally {
    if (!silent) loading.value = false;
  }
}
async function cancel(item: Depart) {
  if (
    busy.value ||
    !cancellationApproved.value && !window.confirm(
      "Annuler ce départ ? Les paiements éventuels seront remboursés dans la caisse sélectionnée.",
    )
  )
    return;
  busy.value = item.id;
  error.value = "";
  try {
    Object.assign(
      item,
      await departService.cancel(item.id, cancelCaisseId.value || undefined),
    );
    success.value = "Départ annulé avec succès.";
  } catch (value: unknown) {
    showError(
      value,
      "Impossible d’annuler ce départ. Pour un départ payé, sélectionnez une caisse ouverte.",
    );
  } finally {
    busy.value = null;
  }
}
function requestCancel(item: Depart) {
  if (!busy.value) cancelTarget.value = item;
}
async function confirmCancel() {
  if (!cancelTarget.value) return;
  cancellationApproved.value = true;
  await cancel(cancelTarget.value);
  cancellationApproved.value = false;
  if (!busy.value) cancelTarget.value = null;
}
function sort() {
  sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
  page.value = 1;
  void load();
}
function changePage(next: number) {
  if (next >= 1 && next <= pages.value) {
    page.value = next;
    void load();
  }
}
function resetFilters() {
  search.value = "";
  status.value = "";
  dateFrom.value = "";
  dateTo.value = "";
  cooperativeId.value = null;
  gareId.value = null;
  routeId.value = null;
  page.value = 1;
  void load();
}
useAutoRefresh(() => load(true));
onMounted(async () => {
  await Promise.all([load(), loadCaisses(), loadCatalog()]);
});
</script>

<template>
  <AppLayout
    ><template #title>Départs & planning</template>
    <div class="page-intro">
      <div>
        <p class="eyebrow">PLANIFICATION</p>
        <h2>Départs & planning</h2>
        <p>Programmez les départs et suivez leur état.</p>
      </div>
      <RouterLink
        v-if="canCreate()"
        class="primary-button compact-button"
        to="/departs/new"
        >+ Programmer un départ</RouterLink
      >
    </div>
    <BaseCard
      ><div class="card-heading">
        <div>
          <h2>Liste des départs ({{ total }})</h2>
          <p>
            Les conflits de véhicule et de chauffeur sont contrôlés
            automatiquement.
          </p>
        </div>
      </div>
      <ListToolbar
        v-model="search"
        :loading="loading || busy !== null"
        placeholder="Rechercher un statut"
        :sort-label="sortOrder === 'asc' ? 'Plus anciens' : 'Plus récents'"
        @search="
          page = 1;
          load();
        "
        @sort="sort"
      />
      <OperationalFilters
        :active-count="activeFilterCount"
        :loading="loading || loadingCatalog"
        title="Afficher les départs selon…"
        description="Gare, coopérative, trajet, statut et période."
        @apply="page = 1; load()"
        @reset="resetFilters"
      >
        <label class="form-field"><span>Statut</span><select v-model="status"><option value="">Tous les statuts</option><option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option></select></label>
        <label class="form-field"><span>Gare</span><SearchSelect v-model="gareId" :options="gareOptions" :empty-value="null" placeholder="Toutes les gares" /></label>
        <label class="form-field"><span>Coopérative</span><SearchSelect v-model="cooperativeId" :options="cooperativeOptions" :empty-value="null" placeholder="Toutes les coopératives" /></label>
        <label class="form-field"><span>Trajet</span><SearchSelect v-model="routeId" :options="routeOptions" :empty-value="null" placeholder="Tous les trajets" /></label>
        <label class="form-field"><span>Du</span><input v-model="dateFrom" type="date" /></label>
        <label class="form-field"><span>Au</span><input v-model="dateTo" type="date" /></label>
        <template #summary><span class="filter-summary">{{ total }} départ{{ total > 1 ? "s" : "" }} trouvé{{ total > 1 ? "s" : "" }}</span></template>
      </OperationalFilters>
      <div
        v-if="canCancel() && canProcessRefund()"
        class="form-grid cancellation-cash"
      >
        <label class="form-field"
          ><span>Caisse de remboursement (si nécessaire)</span
          ><SearchSelect
            aria-label="Annulation sans remboursement"
            v-model="cancelCaisseId"
            :options="
              caisses.map((caisse) => ({
                value: caisse.id,
                label: `Gare #${caisse.id_gare} · solde ${caisse.solde}`,
              }))
            "
            placeholder="Annulation sans remboursement"
            :empty-value="null"
        /></label>
      </div>
      <p v-if="loading" class="status-msg">Chargement des départs…</p>
      <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
      <p v-if="success" class="success-banner" role="status">{{ success }}</p>
      <TableViewControls v-if="!loading && !error" v-model:density="tableDensity" v-model:visible-columns="visibleDepartColumns" storage-key="departs" :columns="departColumns" />
      <div v-if="!loading && !error" class="table-scroll">
        <table :class="['data-table', `table-density-${tableDensity}`, ...visibleDepartColumns.map((column) => `show-${column}`)]">
          <caption>
            Planning des départs
          </caption>
          <thead>
            <tr>
              <th>Date / heure</th>
              <th>Itinéraire</th>
              <th>Gare</th>
              <th>Coopérative</th>
              <th>Véhicule</th>
              <th>Places</th>
              <th>Remplissage</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td>
                <strong>{{ formatDate(item.date_depart) }}</strong
                ><br />{{ item.heure_depart.slice(0, 5) }}
              </td>
              <td>{{ routeName(item) }}</td>
              <td>{{ item.gare?.nom || `#${item.id_gare || "—"}` }}</td>
              <td>{{ item.cooperative?.nom || `#${item.id_cooperative}` }}</td>
              <td>
                {{ item.vehicule?.immatriculation || `#${item.id_vehicule}` }}
              </td>
              <td>
                {{ item.places_disponibles }} /
                {{ item.nombre_places }} disponibles
              </td>
              <td>{{ item.taux_remplissage }} %</td>
              <td>
                <span
                  :class="[
                    'status-badge',
                    item.statut === 'ANNULE' ? 'inactive' : 'active',
                  ]"
                  >{{ statusLabels[item.statut] }}</span
                >
              </td>
              <td>
                <RouterLink
                  class="table-action table-link"
                  :to="`/departs/${item.id}`"
                  >Détails</RouterLink
                ><RouterLink
                  v-if="
                    canUpdate() &&
                    ['PROGRAMME', 'RETARDE'].includes(item.statut)
                  "
                  class="table-action table-link"
                  :to="`/departs/${item.id}/edit`"
                  >Modifier</RouterLink
                ><button
                  v-if="
                    canCancel() &&
                    !['ANNULE', 'PARTI', 'TERMINE'].includes(item.statut)
                  "
                  class="table-action danger-action"
                  :disabled="busy !== null"
                  @click="requestCancel(item)"
                >
                  Annuler
                </button>
              </td>
            </tr>
            <tr v-if="!items.length">
              <td colspan="9" class="empty-state">Aucun départ enregistré.</td>
            </tr>
          </tbody>
        </table>
      </div></BaseCard
    ><SensitiveActionDialog :open="Boolean(cancelTarget)" :busy="busy !== null" danger title="Annuler ce départ" confirm-label="Confirmer l’annulation" @cancel="cancelTarget = null" @confirm="confirmCancel">
      <p><strong>{{ cancelTarget ? routeName(cancelTarget) : "" }}</strong></p>
      <p>Les places seront libérées. Les paiements éventuels seront remboursés depuis la caisse sélectionnée.</p>
      <p v-if="canProcessRefund() && !cancelCaisseId" class="field-hint">Choisissez une caisse ouverte si un remboursement est attendu.</p>
    </SensitiveActionDialog><PaginationControls
      v-if="!loading && !error"
      :page="page"
      :pages="pages"
      :total="total"
      :disabled="busy !== null"
      item-label="résultat(s)"
      @change="changePage"
  /></AppLayout>
</template>

<style scoped>
.data-table:not(.show-route) :is(th:nth-child(2), td:nth-child(2)), .data-table:not(.show-station) :is(th:nth-child(3), td:nth-child(3)), .data-table:not(.show-coop) :is(th:nth-child(4), td:nth-child(4)), .data-table:not(.show-vehicle) :is(th:nth-child(5), td:nth-child(5)), .data-table:not(.show-places) :is(th:nth-child(6), td:nth-child(6)), .data-table:not(.show-load) :is(th:nth-child(7), td:nth-child(7)), .data-table:not(.show-status) :is(th:nth-child(8), td:nth-child(8)) { display: none; }
.table-density-compact :deep(th) { padding-block: .55rem; }.table-density-compact :deep(td) { padding-block: .55rem; }
.cancellation-cash {
  max-width: 420px;
  margin: 1rem 0;
}
</style>
