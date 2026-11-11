<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { localIsoDate, daysAgo } from "../../utils/date";
import AppLayout from "../../components/layout/AppLayout.vue";
import PageTabs from "../../components/ui/PageTabs.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import ListToolbar from "../../components/ui/ListToolbar.vue";
import PaginationControls from "../../components/ui/PaginationControls.vue";
import type { DashboardStatistics } from "../../models/dashboard/model";
import { dashboardService } from "../../services/dashboard/service";
import { userError } from "../../utils/errors";

const data = ref<DashboardStatistics | null>(null);
const loading = ref(true);
const error = ref("");
const today = localIsoDate();
const defaultFrom = localIsoDate(daysAgo(29));
const dateFrom = ref(defaultFrom);
const dateTo = ref(today);
const viewMode = ref("trends");
const detailSearch = ref("");
const detailSortBy = ref<"date" | "total" | "reservations">("date");
const detailSortOrder = ref<"asc" | "desc">("desc");
const detailPage = ref(1);
const routePage = ref(1);
const detailPageSize = 20;
const invalidPeriod = computed(
  () => !dateFrom.value || !dateTo.value || dateTo.value < dateFrom.value,
);

const totals = computed(() => {
  const departs = data.value?.departs || [];
  const reservations = data.value?.reservations || [];
  const totalDepartures = departs.reduce((sum, row) => sum + row.total, 0);
  const reserved = departs.reduce((sum, row) => sum + row.places_reservees, 0);
  const capacity = departs.reduce((sum, row) => sum + row.places_total, 0);
  return {
    totalDepartures,
    reservations: reservations.reduce((sum, row) => sum + row.total, 0),
    reserved,
    capacity,
    occupancy: capacity ? Math.round((reserved / capacity) * 100) : 0,
  };
});

const chartMetric = ref<"total" | "reservations" | "occupancy">("total");
const metricLabels = {
  total: "Départs par jour",
  reservations: "Réservations par jour",
  occupancy: "Remplissage par jour",
};
const trendMetrics = computed(() => {
  const comparison = data.value?.comparison;
  return [
    {
      label: "Départs",
      current: comparison?.departs.current ?? 0,
      previous: comparison?.departs.previous ?? 0,
      unit: "nombre",
    },
    {
      label: "Réservations",
      current: comparison?.reservations.current ?? 0,
      previous: comparison?.reservations.previous ?? 0,
      unit: "nombre",
    },
    {
      label: "Remplissage",
      current: comparison?.remplissage.current ?? 0,
      previous: comparison?.remplissage.previous ?? 0,
      unit: "%",
    },
  ].map((metric) => {
    const difference = metric.current - metric.previous;
    const change =
      metric.unit === "%"
        ? Math.round(difference * 10) / 10
        : metric.previous
          ? Math.round((difference / metric.previous) * 100)
          : null;
    return {
      ...metric,
      difference,
      comparison:
        change === null
          ? metric.current
            ? "Nouvelle activité sur cette période"
            : "Aucune activité sur les deux périodes"
          : `${change > 0 ? "+" : ""}${change}${metric.unit === "%" ? " points" : " %"} par rapport à la période précédente`,
    };
  });
});
const chartRows = computed(() => {
  const departures = new Map(
    (data.value?.departs || []).map((row) => [row.date, row]),
  );
  const reservations = new Map(
    (data.value?.reservations || []).map((row) => [row.date, row.total]),
  );
  const rows: Array<{
    date: string;
    total: number;
    reservations: number;
    occupancy: number;
  }> = [];
  const current = new Date(
    `${data.value?.date_from || dateFrom.value}T00:00:00`,
  );
  const end = new Date(`${data.value?.date_to || dateTo.value}T00:00:00`);
  while (current <= end) {
    const date = localIsoDate(current);
    const row = departures.get(date);
    rows.push({
      date,
      total: row?.total || 0,
      reservations: reservations.get(date) || 0,
      occupancy: row?.places_total
        ? Math.round((row.places_reservees * 100) / row.places_total)
        : 0,
    });
    current.setDate(current.getDate() + 1);
  }
  return rows;
});
const chartMax = computed(() =>
  chartMetric.value === "occupancy"
    ? 100
    : Math.max(...chartRows.value.map((row) => row[chartMetric.value]), 1),
);
const hasChartData = computed(() =>
  chartRows.value.some((row) => row[chartMetric.value] > 0),
);

const detailRows = computed(() => {
  const term = detailSearch.value.trim().toLowerCase();
  return [...(data.value?.departs || [])]
    .filter((row) => !term || row.date.toLowerCase().includes(term))
    .sort((left, right) => {
      const a =
        detailSortBy.value === "date"
          ? left.date
          : detailSortBy.value === "total"
            ? left.total
            : left.places_reservees;
      const b =
        detailSortBy.value === "date"
          ? right.date
          : detailSortBy.value === "total"
            ? right.total
            : right.places_reservees;
      const comparison =
        typeof a === "number" && typeof b === "number"
          ? a - b
          : String(a).localeCompare(String(b), "fr", { numeric: true });
      return detailSortOrder.value === "asc" ? comparison : -comparison;
    });
});
const routeRows = computed(() => {
  const term = detailSearch.value.trim().toLowerCase();
  return [...(data.value?.destinations || [])]
    .filter(
      (row) =>
        !term ||
        String(row.libelle || `Itinéraire #${row.id_itineraire}`)
          .toLowerCase()
          .includes(term),
    )
    .sort((left, right) => {
      const comparison = left.reservations - right.reservations;
      return detailSortOrder.value === "asc" ? comparison : -comparison;
    });
});
const detailPages = computed(() =>
  Math.max(1, Math.ceil(detailRows.value.length / detailPageSize)),
);
const routePages = computed(() =>
  Math.max(1, Math.ceil(routeRows.value.length / detailPageSize)),
);
const visibleDetailRows = computed(() =>
  detailRows.value.slice(
    (detailPage.value - 1) * detailPageSize,
    detailPage.value * detailPageSize,
  ),
);
const visibleRouteRows = computed(() =>
  routeRows.value.slice(
    (routePage.value - 1) * detailPageSize,
    routePage.value * detailPageSize,
  ),
);
function resetDetailPages() {
  detailPage.value = 1;
  routePage.value = 1;
}
function toggleDetailSort() {
  detailSortOrder.value = detailSortOrder.value === "asc" ? "desc" : "asc";
  resetDetailPages();
}
watch([detailSearch, detailSortBy, detailSortOrder], resetDetailPages);

async function load() {
  loading.value = true;
  error.value = "";
  resetDetailPages();
  if (invalidPeriod.value) {
    error.value =
      "La date de fin doit être postérieure ou égale à la date de début.";
    loading.value = false;
    return;
  }
  try {
    data.value = (await dashboardService.statistics({
      date_from: dateFrom.value,
      date_to: dateTo.value,
    })) as DashboardStatistics;
  } catch (value: unknown) {
    error.value = userError(
      value,
      "Impossible de charger les statistiques.",
      "STATISTICS_ERROR",
    );
  } finally {
    loading.value = false;
  }
}

function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "short",
  });
}
onMounted(load);
</script>
<template>
  <AppLayout>
    <template #title>Statistiques</template>
    <section class="page-intro">
      <div>
        <p class="eyebrow">ANALYSE MÉTIER</p>
        <h2>Statistiques d’activité</h2>
        <p>
          Analyse des départs et réservations enregistrés sur la période
          choisie.
        </p>
      </div>
      <div class="period-filter">
        <label>Du <input v-model="dateFrom" type="date" /></label
        ><label>Au <input v-model="dateTo" type="date" /></label
        ><button
          class="primary-button"
          type="button"
          :disabled="loading || invalidPeriod"
          @click="load"
        >
          Appliquer
        </button>
      </div>
    </section>
    <p v-if="loading" class="status-msg">Chargement des statistiques…</p>
    <p v-else-if="error" class="error-banner">{{ error }}</p>
    <template v-else-if="data">
      <PageTabs
        v-model="viewMode"
        :tabs="[
          { id: 'trends', label: 'Tendances' },
          { id: 'details', label: 'Détail des données' },
        ]"
        aria-label="Présentation des statistiques"
      />
      <template v-if="viewMode === 'trends'">
        <section class="trend-grid">
          <BaseCard v-for="metric in trendMetrics" :key="metric.label"
            ><div class="trend-panel">
              <span class="stat-label">{{ metric.label }}</span
              ><strong
                >{{ metric.current.toLocaleString("fr-FR")
                }}{{ metric.unit === "%" ? " %" : "" }}</strong
              ><small>{{ metric.comparison }}</small
              ><small class="trend-baseline"
                >Période précédente :
                {{ metric.previous.toLocaleString("fr-FR")
                }}{{ metric.unit === "%" ? " %" : "" }}</small
              >
            </div></BaseCard
          >
        </section>
        <BaseCard class="main-chart"
          ><div class="card-heading">
            <div>
              <h2>Activité quotidienne</h2>
              <p>
                Un indicateur à la fois. Les jours sans activité sont inclus
                dans la période sélectionnée.
              </p>
            </div>
            <label class="chart-metric-control"
              >Indicateur<select v-model="chartMetric">
                <option value="total">Départs</option>
                <option value="reservations">Réservations</option>
                <option value="occupancy">Remplissage</option>
              </select></label
            >
          </div>
          <figure class="daily-chart">
            <figcaption>{{ metricLabels[chartMetric] }}</figcaption>
            <p class="chart-unit">
              {{
                chartMetric === "occupancy"
                  ? "Taux de remplissage (%)"
                  : "Nombre par jour"
              }}
              · Échelle : 0 à {{ chartMax }}
            </p>
            <p v-if="!hasChartData" class="chart-no-data" role="status">
              Aucune activité pour cet indicateur sur la période.
            </p>
            <div
              v-else
              class="daily-chart-scroll"
              tabindex="0"
              aria-label="Graphique défilant, activité par jour"
            >
              <div
                class="daily-chart-bars"
                role="list"
                :style="{
                  minWidth: `${Math.max(460, chartRows.length * 38)}px`,
                }"
              >
                <div
                  v-for="row in chartRows"
                  :key="row.date"
                  class="daily-chart-column"
                  role="listitem"
                  :aria-label="`${formatDate(row.date)} : ${row[chartMetric]}${chartMetric === 'occupancy' ? ' %' : ''}`"
                >
                  <span
                    >{{ row[chartMetric]
                    }}{{ chartMetric === "occupancy" ? "%" : "" }}</span
                  >
                  <div class="daily-bar-track">
                    <i
                      :style="{
                        height: `${(row[chartMetric] / chartMax) * 100}%`,
                      }"
                    />
                  </div>
                  <small>{{ formatDate(row.date) }}</small>
                </div>
              </div>
            </div>
            <p class="chart-date-unit">Date de départ · jour</p>
          </figure>
        </BaseCard>
      </template>
      <ListToolbar
        v-if="viewMode === 'details'"
        v-model="detailSearch"
        :loading="loading"
        placeholder="Rechercher une date ou un itinéraire"
        :sort-label="
          detailSortOrder === 'asc' ? 'Tri croissant ↑' : 'Tri décroissant ↓'
        "
        @search="resetDetailPages"
        @sort="toggleDetailSort"
      />
      <div v-if="viewMode === 'details'" class="filter-row statistics-filter">
        <select
          v-model="detailSortBy"
          aria-label="Colonne de tri"
          @change="resetDetailPages"
        >
          <option value="date">Trier par date</option>
          <option value="total">Trier par départs</option>
          <option value="reservations">Trier par réservées</option>
        </select>
      </div>
      <section
        v-if="viewMode === 'details'"
        class="content-grid statistics-grid"
      >
        <BaseCard
          ><div class="card-heading">
            <div>
              <h2>Détail des départs</h2>
              <p>Capacité et remplissage par date.</p>
            </div>
          </div>
          <div class="table-scroll">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Départs</th>
                  <th>Réservées</th>
                  <th>Capacité</th>
                  <th>Remplissage</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in visibleDetailRows"
                  :key="`detail-${row.date}`"
                >
                  <td>{{ formatDate(row.date) }}</td>
                  <td>{{ row.total }}</td>
                  <td>{{ row.places_reservees }}</td>
                  <td>{{ row.places_total }}</td>
                  <td>
                    {{
                      row.places_total
                        ? Math.round(
                            (row.places_reservees * 100) / row.places_total,
                          )
                        : 0
                    }}%
                  </td>
                </tr>
                <tr v-if="!detailRows.length">
                  <td colspan="5" class="empty-state">
                    Aucune donnée ne correspond à la recherche.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <PaginationControls
            :page="detailPage"
            :pages="detailPages"
            :total="detailRows.length"
            item-label="date(s)"
            @change="detailPage = $event"
        /></BaseCard>
        <BaseCard
          ><div class="card-heading">
            <div>
              <h2>Itinéraires demandés</h2>
              <p>Classement par réservations.</p>
            </div>
          </div>
          <div class="route-ranking">
            <div
              v-for="(row, index) in visibleRouteRows"
              :key="row.id_itineraire"
              class="route-row"
            >
              <span class="rank">{{
                Number(index) + 1 + (routePage - 1) * detailPageSize
              }}</span
              ><span>{{
                row.libelle || "Itinéraire #" + row.id_itineraire
              }}</span
              ><strong>{{ row.reservations }}</strong>
            </div>
            <p v-if="!routeRows.length" class="empty-state">
              Aucun itinéraire ne correspond à la recherche.
            </p>
          </div>
          <PaginationControls
            :page="routePage"
            :pages="routePages"
            :total="routeRows.length"
            item-label="itinéraire(s)"
            @change="routePage = $event"
        /></BaseCard>
      </section>
    </template>
  </AppLayout>
</template>

<style scoped>
.period-filter {
  display: flex;
  align-items: end;
  flex-wrap: wrap;
  gap: 12px;
}
.period-filter label {
  display: grid;
  gap: 6px;
  font-size: 12px;
}
.trend-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}
.trend-panel {
  display: grid;
  gap: 12px;
  padding: 24px;
}
.trend-panel strong {
  color: var(--ink-strong);
  font: 800 28px var(--font-heading);
}
.trend-panel small {
  color: var(--ink-muted);
  font-size: 12px;
  line-height: 1.7;
}
.trend-panel .trend-baseline {
  font-size: 11px;
}
.main-chart {
  margin-top: 24px;
  padding: 24px;
}
.chart-metric-control {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 170px;
}
.daily-chart {
  margin: 24px 0 0;
}
.daily-chart figcaption {
  color: var(--ink-strong);
  font-weight: 600;
}
.chart-unit,
.chart-date-unit {
  color: var(--ink-muted);
  font-size: 11px;
}
.chart-date-unit {
  text-align: center;
  margin-bottom: 0;
}
.chart-no-data {
  display: grid;
  place-items: center;
  min-height: 220px;
  border: 1px dashed var(--line);
  border-radius: 10px;
  color: var(--ink-muted);
  background: var(--canvas);
  text-align: center;
}
.daily-chart-scroll {
  max-width: 100%;
  overflow-x: auto;
}
.daily-chart-bars {
  display: flex;
  align-items: end;
  gap: 8px;
  padding: 20px 12px;
}
.daily-chart-column {
  display: grid;
  grid-template-rows: 22px 180px 26px;
  flex: 1;
  min-width: 28px;
  gap: 8px;
  text-align: center;
}
.daily-chart-column > span,
.daily-chart-column > small {
  color: var(--ink-muted);
  font-size: 10px;
  white-space: nowrap;
}
.daily-bar-track {
  display: flex;
  align-items: end;
  border-bottom: 1px solid var(--line);
  background: repeating-linear-gradient(
    to top,
    transparent,
    transparent 44px,
    #e5eae1 44px,
    #e5eae1 45px
  );
}
.daily-bar-track i {
  display: block;
  width: 100%;
  border-radius: 4px 4px 0 0;
  background: var(--brand);
}
.statistics-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 24px;
}
.statistics-grid > .base-card {
  padding: 24px;
}
.route-ranking {
  display: grid;
  gap: 16px;
  margin-top: 24px;
}
.route-row {
  display: grid;
  grid-template-columns: 26px 1fr auto;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
  font-size: 12px;
}
.rank {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: var(--brand);
  background: var(--brand-soft);
  font-size: 11px;
}
@media (max-width: 900px) {
  .trend-grid,
  .statistics-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 600px) {
  .period-filter {
    width: 100%;
  }
  .period-filter label {
    flex: 1;
    min-width: 120px;
  }
  .period-filter button {
    width: 100%;
  }
  .main-chart {
    padding: 18px;
  }
  .chart-metric-control {
    width: 100%;
  }
}
</style>
