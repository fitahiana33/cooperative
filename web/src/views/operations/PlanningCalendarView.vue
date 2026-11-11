<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import { departService } from "../../services/depart/service";
import type { Depart } from "../../models/depart/model";
import { localIsoDate } from "../../utils/date";
import { userError } from "../../utils/errors";
import { useAuthenticationStore } from "../../stores/authentication/store";

const weekStart = ref(startOfWeek(new Date(`${localIsoDate()}T00:00:00`)));
const items = ref<Depart[]>([]);
const loading = ref(false);
const error = ref("");
const auth = useAuthenticationStore();
const isDriver = computed(() => auth.user?.role?.toLowerCase() === "chauffeur");

function startOfWeek(value: Date) {
  const day = value.getDay() || 7;
  const result = new Date(value);
  result.setDate(value.getDate() - day + 1);
  return result;
}
function iso(value: Date) {
  return value.toISOString().slice(0, 10);
}
function addDays(value: Date, amount: number) {
  const result = new Date(value);
  result.setDate(result.getDate() + amount);
  return result;
}
function label(value: Date) {
  return value.toLocaleDateString("fr-FR", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
  });
}
function routeName(item: Depart) {
  return `${item.itineraire?.destination_depart?.nom || `#${item.id_itineraire}`} → ${item.itineraire?.destination_arrivee?.nom || ""}`;
}
function statusLabel(item: Depart) {
  return (
    (
      {
        PROGRAMME: "Programmé",
        EMBARQUEMENT: "Embarquement",
        RETARDE: "Retardé",
        PARTI: "Parti",
        TERMINE: "Terminé",
        ANNULE: "Annulé",
      } as Record<string, string>
    )[item.statut] || item.statut
  );
}
const days = computed(() =>
  Array.from({ length: 7 }, (_, index) => addDays(weekStart.value, index)),
);
const byDay = computed(() =>
  Object.fromEntries(
    days.value.map((day) => [
      iso(day),
      items.value
        .filter((item) => item.date_depart === iso(day))
        .sort((a, b) => a.heure_depart.localeCompare(b.heure_depart)),
    ]),
  ),
);
const periodLabel = computed(
  () =>
    `${days.value[0].toLocaleDateString("fr-FR")} — ${days.value[6].toLocaleDateString("fr-FR")}`,
);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const params = {
      page: 1,
      page_size: 100,
      date_from: iso(days.value[0]),
      date_to: iso(days.value[6]),
      sort_by: "date_depart",
      sort_order: "asc",
    };
    const result = isDriver.value
      ? await departService.listMine(params)
      : await departService.list(params);
    items.value = result.items || [];
  } catch (value: unknown) {
    error.value = userError(
      value,
      "Impossible de charger le planning.",
      "PLANNING_ERROR",
    );
  } finally {
    loading.value = false;
  }
}
function moveWeek(amount: number) {
  weekStart.value = addDays(weekStart.value, amount * 7);
  void load();
}
onMounted(load);
</script>

<template>
  <AppLayout>
    <template #title>Calendrier du planning</template>
    <section class="page-intro">
      <div>
        <p class="eyebrow">PLANIFICATION</p>
        <h2>Calendrier des départs</h2>
        <p>
          {{ periodLabel }} · les conflits de véhicule et de chauffeur sont
          bloqués par le service et la base de données.
        </p>
      </div>
      <div class="form-actions">
        <button class="secondary-button" type="button" @click="moveWeek(-1)">
          ← Semaine précédente</button
        ><button class="secondary-button" type="button" @click="moveWeek(1)">
          Semaine suivante →
        </button>
      </div>
    </section>
    <p v-if="loading" class="status-msg">Chargement du planning…</p>
    <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
    <BaseCard v-else>
      <div class="calendar-grid">
        <section v-for="day in days" :key="iso(day)" class="calendar-day">
          <h3>{{ label(day) }}</h3>
          <div v-if="!byDay[iso(day)]?.length" class="empty-day">
            Aucun départ
          </div>
          <RouterLink
            v-for="item in byDay[iso(day)]"
            :key="item.id"
            class="calendar-item"
            :to="`/departs/${item.id}`"
          >
            <strong
              >{{ item.heure_depart.slice(0, 5) }} ·
              {{ routeName(item) }}</strong
            >
            <span
              >{{
                item.vehicule?.immatriculation ||
                `Véhicule #${item.id_vehicule}`
              }}
              · chauffeur
              {{
                item.chauffeur?.numero_permis || `#${item.id_chauffeur}`
              }}</span
            >
            <small
              >{{ statusLabel(item) }} · {{ item.places_reservees }}/{{
                item.nombre_places
              }}
              place(s)</small
            >
          </RouterLink>
        </section>
      </div>
    </BaseCard>
  </AppLayout>
</template>

<style scoped>
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(145px, 1fr));
  gap: 0.65rem;
  overflow-x: auto;
}
.calendar-day {
  min-height: 260px;
  padding: 0.7rem;
  border: 1px solid var(--line);
  border-radius: 0.8rem;
  background: var(--canvas);
}
.calendar-day h3 {
  margin: 0 0 0.7rem;
  color: var(--ink-strong);
  text-transform: capitalize;
  font-size: 0.9rem;
}
.calendar-item {
  display: grid;
  gap: 0.25rem;
  margin-bottom: 0.55rem;
  padding: 0.65rem;
  border: 1px solid var(--brand-soft);
  border-radius: 0.65rem;
  background: #fff;
  color: var(--ink);
  text-decoration: none;
}
.calendar-item:hover {
  border-color: var(--brand);
}
.calendar-item strong {
  color: var(--ink-strong);
  font-size: 0.8rem;
}
.calendar-item span,
.calendar-item small,
.empty-day {
  color: var(--ink-muted);
  font-size: 0.72rem;
}
.empty-day {
  padding: 0.4rem 0;
}
@media (max-width: 1050px) {
  .calendar-grid {
    grid-template-columns: repeat(7, 190px);
  }
}
</style>
