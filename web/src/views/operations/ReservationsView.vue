<script setup lang="ts">
import { useSessionFilters } from "../../composables/useSessionFilters";
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import ListToolbar from "../../components/ui/ListToolbar.vue";
import OperationalFilters from "../../components/ui/OperationalFilters.vue";
import SearchSelect from "../../components/ui/SearchSelect.vue";
import PaginationControls from "../../components/ui/PaginationControls.vue";
import TableViewControls from "../../components/ui/TableViewControls.vue";
import { reservationService } from "../../services/reservation/service";
import type {
  Reservation,
  ReservationStatus,
} from "../../models/reservation/model";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { userError } from "../../utils/errors";
import { useOperationalCatalog } from "../../composables/useOperationalCatalog";
import { useAutoRefresh } from "../../composables/useAutoRefresh";

const auth = useAuthenticationStore();
const items = ref<Reservation[]>([]);
const search = ref("");
const status = ref<ReservationStatus | "">("");
const sortBy = ref("created_at");
const sortOrder = ref("desc");
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
const reservationColumns = [
  { id: "number", label: "Numéro", locked: true },
  { id: "departure", label: "Départ" },
  { id: "places", label: "Places" },
  { id: "amount", label: "Montant" },
  { id: "created", label: "Créée le" },
  { id: "status", label: "Statut" },
  { id: "actions", label: "Actions", locked: true },
];
const visibleReservationColumns = ref(reservationColumns.map((column) => column.id));
const hasColumn = (column: string) => visibleReservationColumns.value.includes(column);
const tableColspan = computed(() => visibleReservationColumns.value.length);
const statuses: Record<ReservationStatus, string> = {
  EN_ATTENTE: "En attente",
  CONFIRMEE: "Confirmée",
  PAYEE: "Payée",
  ANNULEE: "Annulée",
  EXPIREE: "Expirée",
  EMBARQUEE: "Embarquée",
  TERMINEE: "Terminée",
};
const { gareOptions, cooperativeOptions, routeOptions, loadingCatalog, loadCatalog } = useOperationalCatalog();
const activeFilterCount = computed(() => [search.value, status.value, dateFrom.value, dateTo.value, cooperativeId.value, gareId.value, routeId.value].filter(Boolean).length);

useSessionFilters("reservations", { search, status, sortBy, sortOrder, dateFrom, dateTo, cooperativeId, gareId, routeId });
function showError(value: unknown) {
  error.value = userError(
    value,
    "Impossible de charger les réservations.",
    "RESERVATIONS_LIST_ERROR",
  );
}
async function load(silent = false) {
  if (!silent) loading.value = true;
  error.value = "";
  try {
    const result = await reservationService.list({
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
    pages.value = result.pages || 1;
  } catch (value: unknown) {
    showError(value);
  } finally {
    if (!silent) loading.value = false;
  }
}
async function exportCsv() {
  try {
    const blob = await reservationService.exportCsv({
      search: search.value || undefined,
      statut: status.value || undefined,
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      id_cooperative: cooperativeId.value || undefined,
      id_gare: gareId.value || undefined,
      id_itineraire: routeId.value || undefined,
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "reservations.csv";
    link.click();
    URL.revokeObjectURL(url);
  } catch (value: unknown) {
    showError(value);
  }
}
function routeName(item: Reservation) {
  const route = item.depart?.itineraire;
  if (!route) return `Départ #${item.id_depart}`;
  return `${route.destination_depart?.nom || "?"} → ${route.destination_arrivee?.nom || "?"}${item.depart?.cooperative ? " · " + item.depart.cooperative.nom : ""}`;
}
function formatDate(value?: string) {
  return value ? new Date(value).toLocaleString("fr-FR") : "—";
}
const canCreate = () => auth.hasPermission("RESERVATION_CREATE");
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
onMounted(() => Promise.all([load(), loadCatalog()]));
</script>

<template>
  <AppLayout>
    <template #title>Réservations</template>
    <div class="page-intro">
      <div>
        <p class="eyebrow">VENTES & PLACES</p>
        <h2>Réservations</h2>
        <p>Consultez les réservations et leur cycle jusqu’au billet.</p>
      </div>
      <div class="page-actions">
        <button class="secondary-button" type="button" @click="exportCsv">
          Exporter CSV</button
        ><RouterLink
          v-if="canCreate()"
          class="primary-button compact-button"
          to="/reservations/new"
          >+ Nouvelle réservation</RouterLink
        >
      </div>
    </div>
    <BaseCard>
      <div class="card-heading">
        <div>
          <h2>Liste des réservations ({{ total }})</h2>
          <p>
            Retrouvez un voyageur, consultez les places réservées et suivez le
            règlement.
          </p>
        </div>
      </div>
      <ListToolbar
        v-model="search"
        :loading="loading"
        :show-sort="false"
        placeholder="N° de réservation"
        @search="
          page = 1;
          load();
        "
      />
      <OperationalFilters
        :active-count="activeFilterCount"
        :loading="loading || loadingCatalog"
        title="Afficher les réservations selon…"
        description="Périmètre, voyage, période, état et ordre de lecture."
        @apply="page = 1; load()"
        @reset="resetFilters"
      >
        <label class="form-field"><span>Statut</span><select v-model="status"><option value="">Tous les statuts</option><option v-for="(label, value) in statuses" :key="value" :value="value">{{ label }}</option></select></label>
        <label class="form-field"><span>Gare</span><SearchSelect v-model="gareId" :options="gareOptions" :empty-value="null" placeholder="Toutes les gares" /></label>
        <label class="form-field"><span>Coopérative</span><SearchSelect v-model="cooperativeId" :options="cooperativeOptions" :empty-value="null" placeholder="Toutes les coopératives" /></label>
        <label class="form-field"><span>Trajet</span><SearchSelect v-model="routeId" :options="routeOptions" :empty-value="null" placeholder="Tous les trajets" /></label>
        <label class="form-field"><span>Départ du</span><input v-model="dateFrom" type="date" /></label>
        <label class="form-field"><span>Départ au</span><input v-model="dateTo" type="date" /></label>
        <label class="form-field"><span>Trier par</span><select v-model="sortBy"><option value="created_at">Date de création</option><option value="date_depart">Date de départ</option><option value="date_expiration">Expiration</option><option value="montant_total">Montant</option><option value="statut">Statut</option></select></label>
        <label class="form-field"><span>Ordre</span><select v-model="sortOrder"><option value="desc">Décroissant</option><option value="asc">Croissant</option></select></label>
        <template #summary><span class="filter-summary">{{ total }} réservation{{ total > 1 ? "s" : "" }} dans la sélection</span></template>
      </OperationalFilters>
      <p v-if="loading" class="status-msg">Chargement des réservations…</p>
      <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
      <TableViewControls v-if="!loading && !error" v-model:density="tableDensity" v-model:visible-columns="visibleReservationColumns" storage-key="reservations" :columns="reservationColumns" />
      <div v-if="!loading && !error" class="table-scroll">
        <table :class="['data-table', `table-density-${tableDensity}`, ...visibleReservationColumns.map((column) => `show-${column}`)]">
          <caption>
            Réservations enregistrées
          </caption>
          <thead>
            <tr>
              <th>Numéro</th>
              <th>Départ</th>
              <th>Places</th>
              <th>Montant</th>
              <th>Créée le</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td>
                <strong>{{ item.numero_reservation }}</strong>
              </td>
              <td>
                {{ routeName(item) }}<br /><small
                  >{{ item.depart?.date_depart }}
                  {{ item.depart?.heure_depart?.slice(0, 5) }}</small
                >
              </td>
              <td>{{ item.places?.length || 0 }}</td>
              <td>{{ item.montant_total }}</td>
              <td>{{ formatDate(item.created_at) }}</td>
              <td>
                <span
                  class="status-badge"
                  :class="
                    item.statut === 'ANNULEE' || item.statut === 'EXPIREE'
                      ? 'inactive'
                      : 'active'
                  "
                  >{{ statuses[item.statut] || item.statut }}</span
                >
              </td>
              <td>
                <RouterLink
                  class="table-action table-link"
                  :to="`/reservations/${item.id}`"
                  >Détails</RouterLink
                >
              </td>
            </tr>
            <tr v-if="!items.length">
              <td colspan="7" class="empty-state">
                Aucune réservation enregistrée.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
    <PaginationControls
      v-if="!loading && !error"
      :page="page"
      :pages="pages"
      :total="total"
      @change="
        (next) => {
          page = next;
          load();
        }
      "
    />
  </AppLayout>
</template>

<style scoped>
.data-table:not(.show-departure) :is(th:nth-child(2), td:nth-child(2)), .data-table:not(.show-places) :is(th:nth-child(3), td:nth-child(3)), .data-table:not(.show-amount) :is(th:nth-child(4), td:nth-child(4)), .data-table:not(.show-created) :is(th:nth-child(5), td:nth-child(5)), .data-table:not(.show-status) :is(th:nth-child(6), td:nth-child(6)) { display: none; }
.table-density-compact :deep(th) { padding-block: .55rem; }.table-density-compact :deep(td) { padding-block: .55rem; }
</style>
