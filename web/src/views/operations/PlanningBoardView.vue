<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import AppIcon from "../../components/ui/AppIcon.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import OperationalFilters from "../../components/ui/OperationalFilters.vue";
import PaginationControls from "../../components/ui/PaginationControls.vue";
import SearchSelect from "../../components/ui/SearchSelect.vue";
import { useOperationalCatalog } from "../../composables/useOperationalCatalog";
import { useSessionFilters } from "../../composables/useSessionFilters";
import { useAutoRefresh } from "../../composables/useAutoRefresh";
import type { Depart, DepartStatus } from "../../models/depart/model";
import { departService } from "../../services/depart/service";
import { allPages } from "../../services/pagination";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { localIsoDate } from "../../utils/date";
import { userError } from "../../utils/errors";

type ViewMode = "agenda" | "week" | "table" | "resources";

const auth = useAuthenticationStore();
const items = ref<Depart[]>([]);
const loading = ref(false);
const error = ref("");
const viewMode = ref<ViewMode>("agenda");
const weekStart = ref(startOfWeek(new Date(`${localIsoDate()}T00:00:00`)));
const selectedDay = ref(localIsoDate());
const agendaPage = ref(1);
const agendaPageSize = 8;
const search = ref("");
const status = ref<DepartStatus | "">("");
const cooperativeId = ref<number | null>(null);
const gareId = ref<number | null>(null);
const routeId = ref<number | null>(null);
const resourceBy = ref<"vehicle" | "driver">("vehicle");
const selectedDepart = ref<Depart | null>(null);
const rescheduleDate = ref("");
const rescheduleTime = ref("");
const rescheduleBusy = ref(false);
const rescheduleError = ref("");

useSessionFilters("planning", {
  search,
  status,
  cooperativeId,
  gareId,
  routeId,
  viewMode,
});

const {
  gareOptions,
  cooperativeOptions,
  routeOptions,
  loadingCatalog,
  loadCatalog,
} = useOperationalCatalog();

const isDriver = computed(() => {
  const roles = [auth.user?.role, ...(auth.user?.roles || []).map((item) => item.libelle)]
    .filter(Boolean)
    .map((item) => String(item).toLowerCase());
  return roles.includes("chauffeur");
});
const statusLabels: Record<DepartStatus, string> = {
  PROGRAMME: "Programmé",
  EMBARQUEMENT: "Embarquement",
  RETARDE: "Retardé",
  PARTI: "Parti",
  TERMINE: "Terminé",
  ANNULE: "Annulé",
};

function startOfWeek(value: Date) {
  const day = value.getDay() || 7;
  const result = new Date(value);
  result.setHours(12, 0, 0, 0);
  result.setDate(value.getDate() - day + 1);
  return result;
}
function addDays(value: Date, amount: number) {
  const result = new Date(value);
  result.setDate(result.getDate() + amount);
  return result;
}
function iso(value: Date) { return localIsoDate(value); }
function shortDay(value: Date) {
  return value.toLocaleDateString("fr-FR", { weekday: "short", day: "2-digit" });
}
function longDay(value: Date) {
  return value.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
}
function routeName(item: Depart) {
  return `${item.itineraire?.destination_depart?.nom || `#${item.id_itineraire}`} → ${item.itineraire?.destination_arrivee?.nom || "Destination"}`;
}
function statusTone(value: DepartStatus) {
  if (value === "RETARDE" || value === "ANNULE") return "alert";
  if (value === "PARTI" || value === "EMBARQUEMENT") return "progress";
  if (value === "TERMINE") return "done";
  return "planned";
}
function isActive(item: Depart) { return !["ANNULE", "TERMINE"].includes(item.statut); }
function minutes(value: string) {
  const [hour = "0", minute = "0"] = value.split(":");
  return Number(hour) * 60 + Number(minute);
}
function capacity(item: Depart) { return item.nombre_places ? Math.round(item.places_reservees / item.nombre_places * 100) : 0; }

const days = computed(() => Array.from({ length: 7 }, (_, index) => addDays(weekStart.value, index)));
const byDay = computed<Record<string, Depart[]>>(() => Object.fromEntries(
  days.value.map((day) => [
    iso(day),
    items.value.filter((item) => item.date_depart === iso(day)).sort((a, b) => a.heure_depart.localeCompare(b.heure_depart)),
  ]),
));
const selectedItems = computed(() => byDay.value[selectedDay.value] || []);
const agendaPages = computed(() => Math.max(Math.ceil(selectedItems.value.length / agendaPageSize), 1));
const visibleSelectedItems = computed(() => selectedItems.value.slice((agendaPage.value - 1) * agendaPageSize, agendaPage.value * agendaPageSize));
const selectedDayLabel = computed(() => {
  const day = days.value.find((item) => iso(item) === selectedDay.value) || days.value[0];
  return longDay(day);
});
const periodLabel = computed(() => `${days.value[0].toLocaleDateString("fr-FR")} — ${days.value[6].toLocaleDateString("fr-FR")}`);
const isCurrentWeek = computed(() => {
  const today = startOfWeek(new Date(`${localIsoDate()}T12:00:00`));
  return iso(weekStart.value) === iso(today);
});
const activeFilterCount = computed(() => [search.value, status.value, cooperativeId.value, gareId.value, routeId.value].filter(Boolean).length);
const reservedSeats = computed(() => items.value.reduce((total, item) => total + item.places_reservees, 0));
const delayedCount = computed(() => items.value.filter((item) => item.statut === "RETARDE").length);
const averageCapacity = computed(() => items.value.length ? Math.round(items.value.reduce((total, item) => total + capacity(item), 0) / items.value.length) : 0);
const conflictById = computed(() => {
  const values = new Map<number, string[]>();
  for (let index = 0; index < items.value.length; index += 1) {
    const item = items.value[index];
    if (!isActive(item)) continue;
    for (const other of items.value.slice(index + 1)) {
      if (!isActive(other) || item.date_depart !== other.date_depart || Math.abs(minutes(item.heure_depart) - minutes(other.heure_depart)) >= 120) continue;
      const shared = [item.id_vehicule === other.id_vehicule ? "véhicule" : "", item.id_chauffeur === other.id_chauffeur ? "chauffeur" : ""].filter(Boolean);
      if (!shared.length) continue;
      for (const candidate of [item, other]) values.set(candidate.id, [...new Set([...(values.get(candidate.id) || []), ...shared])]);
    }
  }
  return values;
});
const conflictCount = computed(() => conflictById.value.size);
const resourceGroups = computed(() => {
  const groups = new Map<string, { label: string; detail: string; items: Depart[] }>();
  for (const item of items.value) {
    const id = resourceBy.value === "vehicle" ? item.id_vehicule : item.id_chauffeur;
    const label = resourceBy.value === "vehicle" ? item.vehicule?.immatriculation || `Véhicule #${id}` : item.chauffeur?.numero_permis || `Chauffeur #${id}`;
    const detail = resourceBy.value === "vehicle" ? item.cooperative?.nom || "Coopérative" : item.vehicule?.immatriculation || `Véhicule #${item.id_vehicule}`;
    const current = groups.get(String(id)) || { label, detail, items: [] };
    current.items.push(item); groups.set(String(id), current);
  }
  return [...groups.values()].map((group) => ({ ...group, items: group.items.sort((a, b) => `${a.date_depart}${a.heure_depart}`.localeCompare(`${b.date_depart}${b.heure_depart}`)) }));
});
const filterChips = computed(() => [
  search.value ? { id: "search", label: `Recherche : ${search.value}` } : null,
  status.value ? { id: "status", label: statusLabels[status.value] } : null,
  gareId.value ? { id: "gare", label: `Gare : ${gareOptions.value.find((item) => item.value === gareId.value)?.label || gareId.value}` } : null,
  cooperativeId.value ? { id: "cooperative", label: `Coop. : ${cooperativeOptions.value.find((item) => item.value === cooperativeId.value)?.label || cooperativeId.value}` } : null,
  routeId.value ? { id: "route", label: `Trajet : ${routeOptions.value.find((item) => item.value === routeId.value)?.label || routeId.value}` } : null,
].filter(Boolean) as Array<{ id: string; label: string }>);
const rescheduleConflicts = computed(() => {
  const item = selectedDepart.value;
  if (!item || !rescheduleDate.value || !rescheduleTime.value) return [] as Depart[];
  return items.value.filter((other) => other.id !== item.id && isActive(other) && other.date_depart === rescheduleDate.value && Math.abs(minutes(other.heure_depart) - minutes(rescheduleTime.value)) < 120 && (other.id_vehicule === item.id_vehicule || other.id_chauffeur === item.id_chauffeur));
});
const canReschedule = computed(() => auth.hasPermission("DEPART_UPDATE") && selectedDepart.value && ["PROGRAMME", "RETARDE"].includes(selectedDepart.value.statut));

async function load(silent: boolean | MouseEvent = false) {
  if (silent !== true) loading.value = true;
  error.value = "";
  const params = {
    page: 1,
    page_size: 100,
    date_from: iso(days.value[0]),
    date_to: iso(days.value[6]),
    search: search.value || undefined,
    statut: status.value || undefined,
    id_cooperative: cooperativeId.value || undefined,
    id_gare: gareId.value || undefined,
    id_itineraire: routeId.value || undefined,
    sort_by: "date_depart",
    sort_order: "asc",
  };
  try {
    const result = isDriver.value
      ? await allPages((next) => departService.listMine(next), params)
      : await allPages((next) => departService.list(next), params);
    items.value = result.items || [];
    agendaPage.value = 1;
  } catch (value: unknown) {
    error.value = userError(value, "Impossible de charger le planning.", "PLANNING_ERROR");
  } finally {
    if (silent !== true) loading.value = false;
  }
}
function selectWeekDay(day: Date) { selectedDay.value = iso(day); agendaPage.value = 1; }
function openDetails(item: Depart) {
  selectedDepart.value = item;
  rescheduleDate.value = item.date_depart;
  rescheduleTime.value = item.heure_depart.slice(0, 5);
  rescheduleError.value = "";
}
function removeChip(id: string) {
  if (id === "search") search.value = "";
  if (id === "status") status.value = "";
  if (id === "gare") gareId.value = null;
  if (id === "cooperative") cooperativeId.value = null;
  if (id === "route") routeId.value = null;
  void load();
}
async function reschedule() {
  const item = selectedDepart.value;
  if (!item || !canReschedule.value || rescheduleConflicts.value.length) return;
  rescheduleBusy.value = true; rescheduleError.value = "";
  try {
    const updated = await departService.update(item.id, { date_depart: rescheduleDate.value, heure_depart: rescheduleTime.value });
    Object.assign(item, updated); selectedDepart.value = item;
    await load(true);
  } catch (value: unknown) {
    rescheduleError.value = userError(value, "Le déplacement est refusé : le serveur a détecté un conflit ou une règle non respectée.", "PLANNING_RESCHEDULE_ERROR");
  } finally { rescheduleBusy.value = false; }
}
function moveWeek(amount: number) {
  weekStart.value = addDays(weekStart.value, amount * 7);
  selectedDay.value = iso(weekStart.value);
  void load();
}
function goToday() {
  const today = new Date(`${localIsoDate()}T12:00:00`);
  weekStart.value = startOfWeek(today);
  selectedDay.value = localIsoDate(today);
  void load();
}
function resetFilters() {
  search.value = "";
  status.value = "";
  cooperativeId.value = null;
  gareId.value = null;
  routeId.value = null;
  void load();
}

useAutoRefresh(() => load(true));
onMounted(async () => { await Promise.all([load(), loadCatalog()]); });
</script>

<template>
  <AppLayout>
    <template #title>Planning opérationnel</template>
    <section class="page-intro planning-intro">
      <div>
        <p class="eyebrow">PLANIFICATION</p>
        <h2>Planning des départs</h2>
        <p>{{ periodLabel }} · {{ items.length }} départ{{ items.length > 1 ? "s" : "" }} dans la sélection.</p>
      </div>
      <div class="planning-navigation" aria-label="Navigation du planning">
        <button class="secondary-button compact-button" type="button" @click="moveWeek(-1)" aria-label="Semaine précédente"><AppIcon name="back" :size="15" /></button>
        <button class="secondary-button compact-button" type="button" :disabled="isCurrentWeek" :aria-current="isCurrentWeek ? 'date' : undefined" @click="goToday">Aujourd’hui</button>
        <button class="secondary-button compact-button" type="button" @click="moveWeek(1)" aria-label="Semaine suivante"><AppIcon name="arrow" :size="15" /></button>
      </div>
    </section>

    <section class="planning-kpis" aria-label="Résumé de la semaine">
      <div><small>Départs</small><strong>{{ items.length }}</strong></div>
      <div><small>Places réservées</small><strong>{{ reservedSeats }}</strong></div>
      <div><small>Retards</small><strong>{{ delayedCount }}</strong></div>
      <div><small>Occupation moyenne</small><strong>{{ averageCapacity }} %</strong></div>
      <div><small>Conflits possibles</small><strong :class="{ 'kpi-alert': conflictCount }">{{ conflictCount }}</strong></div>
      <div><small>Période</small><strong>{{ periodLabel }}</strong></div>
    </section>

    <BaseCard class="planning-workspace">
      <div class="planning-toolbar">
        <div>
          <p class="card-eyebrow">ESPACE DE LECTURE</p>
          <h2>Organisation des départs</h2>
        </div>
        <div class="view-switch" role="group" aria-label="Mode d’affichage">
          <button v-for="mode in ([['agenda', 'Agenda'], ['week', 'Semaine'], ['resources', 'Ressources'], ['table', 'Tableau']] as const)" :key="mode[0]" type="button" :class="{ active: viewMode === mode[0] }" :aria-pressed="viewMode === mode[0]" @click="viewMode = mode[0]">{{ mode[1] }}</button>
        </div>
      </div>

      <OperationalFilters :active-count="activeFilterCount" :loading="loading || loadingCatalog" :open="false" @apply="load" @reset="resetFilters">
        <label class="form-field"><span>Recherche</span><input v-model.trim="search" type="search" placeholder="Ville, plaque, coopérative…" /></label>
        <label class="form-field"><span>Gare</span><SearchSelect v-model="gareId" :options="gareOptions" :empty-value="null" placeholder="Toutes les gares" /></label>
        <label class="form-field"><span>Coopérative</span><SearchSelect v-model="cooperativeId" :options="cooperativeOptions" :empty-value="null" placeholder="Toutes les coopératives" /></label>
        <label class="form-field"><span>Trajet</span><SearchSelect v-model="routeId" :options="routeOptions" :empty-value="null" placeholder="Tous les trajets" /></label>
        <label class="form-field"><span>Statut</span><select v-model="status"><option value="">Tous les statuts</option><option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option></select></label>
        <template #summary><span class="filter-summary">Les filtres respectent automatiquement le périmètre autorisé du compte.</span></template>
      </OperationalFilters>
      <div v-if="filterChips.length" class="filter-chips" aria-label="Filtres actifs">
        <span v-for="chip in filterChips" :key="chip.id">{{ chip.label }} <button type="button" :aria-label="`Retirer ${chip.label}`" @click="removeChip(chip.id)">×</button></span>
      </div>

      <p v-if="loading" class="status-msg">Chargement du planning…</p>
      <p v-else-if="error" class="error-banner" role="alert">{{ error }} <button class="text-button" type="button" @click="load">Réessayer</button></p>

      <template v-else>
        <div v-if="viewMode === 'agenda'" class="agenda-view">
          <nav class="day-strip" aria-label="Jours de la semaine">
            <button v-for="day in days" :key="iso(day)" type="button" :class="{ active: selectedDay === iso(day), today: iso(day) === localIsoDate() }" @click="selectWeekDay(day)">
              <span>{{ shortDay(day) }}</span><strong>{{ byDay[iso(day)]?.length || 0 }}</strong>
            </button>
          </nav>
          <div class="agenda-heading"><div><p class="eyebrow">JOUR SÉLECTIONNÉ</p><h3>{{ selectedDayLabel }}</h3></div><span>{{ selectedItems.length }} départ{{ selectedItems.length > 1 ? "s" : "" }}</span></div>
          <div v-if="selectedItems.length" class="agenda-list">
            <button v-for="item in visibleSelectedItems" :key="item.id" class="agenda-row" type="button" @click="openDetails(item)">
              <time>{{ item.heure_depart.slice(0, 5) }}</time>
              <div class="agenda-route"><strong>{{ routeName(item) }}</strong><small>{{ item.gare?.nom || "Gare non renseignée" }} · {{ item.cooperative?.nom || "Coopérative" }}</small></div>
              <div class="agenda-resource"><span>{{ item.vehicule?.immatriculation || `Véhicule #${item.id_vehicule}` }}</span><small>{{ item.places_reservees }}/{{ item.nombre_places }} places</small></div>
              <span class="capacity-bar" :aria-label="`${capacity(item)} % de remplissage`"><i :style="{ width: `${capacity(item)}%` }" /></span>
              <span :class="['planning-status', statusTone(item.statut), { conflict: conflictById.has(item.id) }]">{{ conflictById.has(item.id) ? 'Conflit à vérifier' : statusLabels[item.statut] }}</span>
              <AppIcon name="chevron" :size="16" />
            </button>
          </div>
          <div v-else class="planning-empty"><strong>Aucun départ ce jour.</strong><span>Choisissez un autre jour ou élargissez les filtres.</span></div>
          <PaginationControls v-if="selectedItems.length > agendaPageSize" :page="agendaPage" :pages="agendaPages" :total="selectedItems.length" item-label="départ(s)" @change="agendaPage = $event" />
        </div>

        <div v-else-if="viewMode === 'week'" class="calendar-grid">
          <section v-for="day in days" :key="iso(day)" class="calendar-day">
            <header><h3>{{ shortDay(day) }}</h3><span>{{ byDay[iso(day)]?.length || 0 }}</span></header>
            <div class="calendar-day__scroll">
              <p v-if="!byDay[iso(day)]?.length" class="empty-day">Aucun départ</p>
              <button v-for="item in byDay[iso(day)]" :key="item.id" class="calendar-item" type="button" @click="openDetails(item)">
                <span><strong>{{ item.heure_depart.slice(0, 5) }}</strong><i :class="statusTone(item.statut)" /></span>
                <b>{{ routeName(item) }}</b>
                <small>{{ item.places_reservees }}/{{ item.nombre_places }} · {{ statusLabels[item.statut] }}</small>
              </button>
            </div>
          </section>
        </div>

        <section v-else-if="viewMode === 'resources'" class="resource-view">
          <div class="resource-toolbar"><p>Répartissez les départs par ressource pour détecter rapidement une surcharge.</p><div class="density-switch" role="group" aria-label="Regrouper les ressources"><button type="button" :class="{ active: resourceBy === 'vehicle' }" @click="resourceBy = 'vehicle'">Véhicules</button><button type="button" :class="{ active: resourceBy === 'driver' }" @click="resourceBy = 'driver'">Chauffeurs</button></div></div>
          <div v-if="resourceGroups.length" class="resource-grid"><article v-for="group in resourceGroups" :key="group.label" class="resource-card"><header><div><strong>{{ group.label }}</strong><small>{{ group.detail }}</small></div><span>{{ group.items.length }} départ{{ group.items.length > 1 ? 's' : '' }}</span></header><button v-for="item in group.items" :key="item.id" type="button" class="resource-item" @click="openDetails(item)"><time>{{ item.date_depart.slice(8) }}/{{ item.date_depart.slice(5, 7) }} · {{ item.heure_depart.slice(0, 5) }}</time><strong>{{ routeName(item) }}</strong><small>{{ item.places_reservees }}/{{ item.nombre_places }} places</small><span class="capacity-bar"><i :style="{ width: `${capacity(item)}%` }" /></span><em v-if="conflictById.has(item.id)">Conflit à vérifier</em></button></article></div>
          <div v-else class="planning-empty"><strong>Aucune ressource pour cette sélection.</strong><span>Modifiez les filtres ou la période.</span></div>
        </section>

        <div v-else class="table-scroll planning-table-wrap">
          <table class="data-table">
            <caption class="sr-only">Départs de la semaine filtrée</caption>
            <thead><tr><th>Date / heure</th><th>Trajet</th><th>Gare</th><th>Coopérative</th><th>Véhicule</th><th>Occupation</th><th>Statut</th><th></th></tr></thead>
            <tbody>
              <tr v-for="item in items" :key="item.id"><td><strong>{{ item.date_depart }}</strong><br /><small>{{ item.heure_depart.slice(0, 5) }}</small></td><td><strong>{{ routeName(item) }}</strong></td><td>{{ item.gare?.nom || "—" }}</td><td>{{ item.cooperative?.nom || "—" }}</td><td>{{ item.vehicule?.immatriculation || "—" }}</td><td>{{ item.places_reservees }}/{{ item.nombre_places }}</td><td><span :class="['planning-status', statusTone(item.statut)]">{{ statusLabels[item.statut] }}</span></td><td><RouterLink class="table-link" :to="`/departs/${item.id}`">Voir</RouterLink></td></tr>
              <tr v-if="!items.length"><td colspan="8" class="empty-state">Aucun départ pour ces critères.</td></tr>
            </tbody>
          </table>
        </div>
      </template>
    </BaseCard>
    <Teleport to="body">
      <div v-if="selectedDepart" class="planning-drawer-backdrop" @mousedown.self="selectedDepart = null">
        <aside class="planning-drawer" role="dialog" aria-modal="true" aria-label="Détail du départ">
          <button class="drawer-close" type="button" aria-label="Fermer le détail" @click="selectedDepart = null">×</button>
          <p class="eyebrow">DÉPART SÉLECTIONNÉ</p><h2>{{ routeName(selectedDepart) }}</h2>
          <p class="drawer-schedule">{{ selectedDepart.date_depart }} · {{ selectedDepart.heure_depart.slice(0, 5) }} · {{ selectedDepart.gare?.nom || 'Gare non renseignée' }}</p>
          <dl class="drawer-facts"><div><dt>Véhicule</dt><dd>{{ selectedDepart.vehicule?.immatriculation || `#${selectedDepart.id_vehicule}` }}</dd></div><div><dt>Chauffeur</dt><dd>{{ selectedDepart.chauffeur?.numero_permis || `#${selectedDepart.id_chauffeur}` }}</dd></div><div><dt>Occupation</dt><dd>{{ selectedDepart.places_reservees }}/{{ selectedDepart.nombre_places }} places · {{ capacity(selectedDepart) }} %</dd></div><div><dt>État</dt><dd><span :class="['planning-status', statusTone(selectedDepart.statut)]">{{ statusLabels[selectedDepart.statut] }}</span></dd></div></dl>
          <p v-if="conflictById.has(selectedDepart.id)" class="drawer-alert"><strong>Conflit possible :</strong> même {{ conflictById.get(selectedDepart.id)?.join(' et ') }} qu’un autre départ proche. La validation serveur reste obligatoire.</p>
          <section v-if="canReschedule" class="reschedule-panel"><h3>Déplacer cet horaire</h3><p>La disponibilité sera contrôlée ici puis revalidée par le serveur.</p><div><label>Date<input v-model="rescheduleDate" type="date" :disabled="rescheduleBusy" /></label><label>Heure<input v-model="rescheduleTime" type="time" :disabled="rescheduleBusy" /></label></div><p v-if="rescheduleConflicts.length" class="drawer-alert">Conflit détecté avec {{ rescheduleConflicts.map((item) => `${item.heure_depart.slice(0, 5)} · ${routeName(item)}`).join(', ') }}. Choisissez un autre créneau.</p><p v-if="rescheduleError" class="error-banner">{{ rescheduleError }}</p><button class="primary-button" type="button" :disabled="rescheduleBusy || Boolean(rescheduleConflicts.length) || (rescheduleDate === selectedDepart.date_depart && rescheduleTime === selectedDepart.heure_depart.slice(0, 5))" @click="reschedule">{{ rescheduleBusy ? 'Validation…' : 'Valider le nouvel horaire' }}</button></section>
          <RouterLink class="secondary-button drawer-link" :to="`/departs/${selectedDepart.id}`">Ouvrir la fiche complète</RouterLink>
        </aside>
      </div>
    </Teleport>
  </AppLayout>
</template>

<style scoped>
.planning-intro { align-items: center; }
.planning-navigation, .view-switch { display: flex; align-items: center; gap: 0.45rem; }
.planning-navigation .secondary-button { min-width: 42px; justify-content: center; }
.planning-kpis { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)) 1.5fr; gap: 1px; margin-bottom: 1rem; overflow: hidden; border: 1px solid var(--line); border-radius: 12px; background: var(--line); }
.planning-kpis > div { display: grid; gap: 0.15rem; min-width: 0; padding: 0.8rem 1rem; background: #fff; }
.planning-kpis small { color: var(--ink-muted); font-size: 0.72rem; }
.planning-kpis strong { overflow-wrap: anywhere; color: var(--ink-strong); font-size: 1rem; }
.kpi-alert { color: #a04435 !important; }
.planning-toolbar, .agenda-heading, .calendar-day header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.planning-toolbar h2, .agenda-heading h3 { margin: 0.15rem 0 0; color: var(--ink-strong); }
.view-switch { padding: 0.25rem; border: 1px solid var(--line); border-radius: 9px; background: #f7f9f7; }
.view-switch button { min-height: 34px; padding: 0.35rem 0.75rem; color: var(--ink-muted); border: 0; border-radius: 7px; background: transparent; font-size: 0.78rem; font-weight: 700; }
.view-switch button.active { color: #fff; background: var(--brand-dark); }
.day-strip { display: grid; grid-template-columns: repeat(7, minmax(74px, 1fr)); gap: 0.5rem; margin-bottom: 1rem; }
.day-strip button { display: flex; align-items: center; justify-content: space-between; gap: 0.4rem; min-height: 48px; padding: 0.55rem 0.7rem; color: var(--ink-muted); border: 1px solid var(--line); border-radius: 9px; background: #fff; text-transform: capitalize; }
.day-strip button strong { display: grid; place-items: center; min-width: 24px; height: 24px; border-radius: 7px; background: #f0f4f0; font-size: 0.72rem; }
.day-strip button.active { color: var(--brand-dark); border-color: var(--brand); background: #f0f6ed; }
.day-strip button.active strong { color: #fff; background: var(--brand-dark); }
.day-strip button.today span::after { content: ""; display: inline-block; width: 5px; height: 5px; margin-left: 5px; border-radius: 50%; background: var(--brand); vertical-align: middle; }
.agenda-heading { padding: 0.4rem 0 0.85rem; border-bottom: 1px solid var(--line); }
.agenda-heading > span { color: var(--ink-muted); font-size: 0.78rem; }
.agenda-list { display: grid; }
.agenda-row { display: grid; grid-template-columns: 72px minmax(190px, 1.8fr) minmax(150px, 1fr) auto 18px; align-items: center; gap: 1rem; min-height: 68px; padding: 0.75rem 0.3rem; color: var(--ink); border-bottom: 1px solid var(--line); text-decoration: none; }
.agenda-row:hover { background: #f8faf8; }
.agenda-row time { color: var(--ink-strong); font: 800 1rem var(--font-heading); }
.agenda-route, .agenda-resource { display: grid; min-width: 0; gap: 0.2rem; }
.agenda-route strong { overflow: hidden; color: var(--ink-strong); text-overflow: ellipsis; white-space: nowrap; }
.agenda-row small { color: var(--ink-muted); font-size: 0.73rem; }
.planning-status { display: inline-flex; align-items: center; justify-content: center; padding: 0.3rem 0.55rem; border-radius: 99px; font-size: 0.7rem; font-weight: 800; white-space: nowrap; }
.planning-status.planned { color: #3f5e6f; background: #edf3f5; }
.planning-status.progress { color: #775200; background: #fff2d7; }
.planning-status.done { color: #176548; background: #e8f5ed; }
.planning-status.alert { color: #963d32; background: #fff0ed; }
.planning-status.conflict { color: #933f31; background: #ffe7e2; outline: 1px solid #e8a49a; }
.capacity-bar { display: block; width: 100%; height: 5px; overflow: hidden; border-radius: 99px; background: #e6ede6; }.capacity-bar i { display: block; height: 100%; border-radius: inherit; background: var(--brand); }
.filter-chips { display: flex; flex-wrap: wrap; gap: .45rem; margin: -.5rem 0 1rem; }.filter-chips > span { display: inline-flex; align-items: center; gap: .35rem; padding: .3rem .45rem .3rem .6rem; border: 1px solid #cee0d1; border-radius: 99px; color: var(--brand-dark); background: #f1f7f1; font-size: .72rem; font-weight: 700; }.filter-chips button { display: grid; place-items: center; width: 19px; height: 19px; border-radius: 50%; color: inherit; background: #dcecdc; font-size: 15px; line-height: 1; }
.planning-empty { display: grid; place-items: center; gap: 0.25rem; min-height: 170px; color: var(--ink-muted); text-align: center; }
.planning-empty strong { color: var(--ink-strong); }
.calendar-grid { display: grid; grid-template-columns: repeat(7, minmax(145px, 1fr)); gap: 0.55rem; overflow-x: auto; }
.calendar-day { min-width: 0; border: 1px solid var(--line); border-radius: 10px; background: #f7f9f7; }
.calendar-day header { padding: 0.65rem; border-bottom: 1px solid var(--line); }
.calendar-day h3 { margin: 0; font-size: 0.8rem; text-transform: capitalize; }
.calendar-day header span { color: var(--ink-muted); font-size: 0.7rem; }
.calendar-day__scroll { display: grid; align-content: start; gap: 0.4rem; height: 480px; padding: 0.45rem; overflow-y: auto; }
.calendar-item { display: grid; width: 100%; gap: 0.25rem; padding: 0.55rem; color: var(--ink); border: 1px solid #e4eae5; border-radius: 8px; background: #fff; text-align: left; text-decoration: none; }
.calendar-item > span { display: flex; align-items: center; justify-content: space-between; }
.calendar-item i { width: 7px; height: 7px; border-radius: 50%; background: #8aa0a9; }
.calendar-item i.progress { background: #d89b27; } .calendar-item i.alert { background: #d25a4c; } .calendar-item i.done { background: #38926a; }
.calendar-item b { font-size: 0.75rem; line-height: 1.35; }
.calendar-item small, .empty-day { color: var(--ink-muted); font-size: 0.68rem; }
.planning-table-wrap { max-height: 570px; overflow: auto; }
.planning-table-wrap thead { position: sticky; top: 0; z-index: 1; }
.resource-view { display: grid; gap: .85rem; }.resource-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }.resource-toolbar p { margin: 0; color: var(--ink-muted); font-size: .78rem; }.density-switch { display: inline-flex; padding: .2rem; border: 1px solid var(--line); border-radius: 8px; background: #f7f9f7; }.density-switch button { min-height: 32px; padding: .25rem .55rem; border-radius: 6px; color: var(--ink-muted); background: transparent; font-size: .72rem; font-weight: 700; }.density-switch button.active { color: #fff; background: var(--brand-dark); }.resource-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; }.resource-card { overflow: hidden; border: 1px solid var(--line); border-radius: 10px; }.resource-card > header { display: flex; align-items: center; justify-content: space-between; gap: .75rem; padding: .75rem; background: #f8faf8; }.resource-card header div { display: grid; gap: .12rem; }.resource-card header strong { color: var(--ink-strong); font-size: .82rem; }.resource-card header small, .resource-card header span { color: var(--ink-muted); font-size: .7rem; }.resource-item { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; width: 100%; gap: .4rem .65rem; padding: .7rem .75rem; border-top: 1px solid var(--line); color: var(--ink); background: #fff; text-align: left; }.resource-item:hover { background: #f8faf8; }.resource-item time, .resource-item small { color: var(--ink-muted); font-size: .68rem; }.resource-item strong { overflow: hidden; color: var(--ink-strong); font-size: .76rem; text-overflow: ellipsis; white-space: nowrap; }.resource-item .capacity-bar { grid-column: 2 / -1; }.resource-item em { grid-column: 1 / -1; color: #9a4638; font-size: .68rem; font-style: normal; }
.planning-drawer-backdrop { position: fixed; inset: 0; z-index: 90; display: flex; justify-content: flex-end; background: #142f265c; backdrop-filter: blur(2px); }.planning-drawer { width: min(510px, 100%); min-height: 100%; padding: 1.4rem; overflow-y: auto; background: #fff; box-shadow: -18px 0 45px #0b1e1740; }.drawer-close { display: grid; place-items: center; width: 34px; height: 34px; margin-left: auto; border: 1px solid var(--line); border-radius: 8px; color: var(--ink); background: #fff; font-size: 21px; }.planning-drawer h2 { margin: .25rem 0 .35rem; color: var(--ink-strong); font: 800 1.35rem/1.3 var(--font-heading); }.drawer-schedule { margin: 0; color: var(--ink-muted); font-size: .82rem; }.drawer-facts { display: grid; grid-template-columns: 1fr 1fr; gap: .65rem; margin: 1.2rem 0; }.drawer-facts div { padding: .7rem; border: 1px solid var(--line); border-radius: 8px; background: #f8faf8; }.drawer-facts dt { color: var(--ink-muted); font-size: .68rem; }.drawer-facts dd { margin: .2rem 0 0; color: var(--ink-strong); font-size: .78rem; font-weight: 700; }.drawer-alert { padding: .75rem; border: 1px solid #edc9c2; border-radius: 8px; color: #963d32; background: #fff1ee; font-size: .78rem; }.reschedule-panel { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--line); }.reschedule-panel h3 { margin: 0; color: var(--ink-strong); font-size: .9rem; }.reschedule-panel > p { color: var(--ink-muted); font-size: .75rem; }.reschedule-panel > div { display: grid; grid-template-columns: 1fr 1fr; gap: .65rem; }.reschedule-panel label { display: grid; gap: .3rem; color: var(--ink-muted); font-size: .7rem; font-weight: 700; }.reschedule-panel input { min-height: 40px; }.drawer-link { margin-top: 1rem; }
@media (max-width: 1050px) { .calendar-grid { grid-template-columns: repeat(7, 180px); } .planning-kpis { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 760px) {
  .planning-toolbar { align-items: stretch; flex-direction: column; }
  .view-switch { width: 100%; } .view-switch button { flex: 1; }
  .day-strip { grid-template-columns: repeat(7, minmax(66px, 1fr)); overflow-x: auto; }
  .day-strip button { min-width: 74px; flex-direction: column; }
  .agenda-row { grid-template-columns: 52px minmax(0, 1fr) auto; gap: 0.65rem; }
  .agenda-resource { grid-column: 2; } .agenda-row > .app-icon { grid-column: 3; grid-row: 1 / 3; }
  .planning-status { grid-column: 3; grid-row: 1; }
  .resource-grid { grid-template-columns: 1fr; }
}
@media (max-width: 520px) { .planning-kpis { grid-template-columns: 1fr 1fr; } .planning-kpis > div:last-child { grid-column: 1 / -1; } .agenda-row { grid-template-columns: 45px minmax(0, 1fr); } .agenda-row > .planning-status, .agenda-row > .app-icon { display: none; } .resource-toolbar { align-items: stretch; flex-direction: column; }.density-switch button { flex: 1; }.planning-drawer { width: 100%; padding: 1.1rem 1rem calc(1.25rem + env(safe-area-inset-bottom)); }.drawer-facts { grid-template-columns: 1fr; }.reschedule-panel > div { grid-template-columns: 1fr; } }
</style>
