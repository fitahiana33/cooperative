<script setup lang="ts">
import { allPages } from "../../services/pagination";
import SearchSelect from "../../components/ui/SearchSelect.vue";
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import type { Depart, DepartStatus } from "../../models/depart/model";
import type { Chauffeur } from "../../models/chauffeur/model";
import { departService } from "../../services/depart/service";
import { chauffeurService } from "../../services/chauffeur/service";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { userError } from "../../utils/errors";

const auth = useAuthenticationStore();
const items = ref<Depart[]>([]);
const loading = ref(true);
const refreshing = ref(false);
const error = ref("");
const actionError = ref("");
const success = ref("");
const busyId = ref<number | null>(null);
const chauffeurs = ref<Chauffeur[]>([]);
const historyItems = ref<Depart[]>([]);
const historyLoading = ref(false);
const historyError = ref("");
const historyLoaded = ref(false);
const selectedChauffeur = ref("");
const historyFrom = ref("");
const historyTo = ref("");

const isDriver = computed(() => {
  const roles = [
    auth.user?.role,
    ...(auth.user?.roles || []).map((role) => role.libelle),
  ]
    .filter(Boolean)
    .map((role) => String(role).toLowerCase());
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
const statusClass = (status: DepartStatus) =>
  ({
    PROGRAMME: "planned",
    EMBARQUEMENT: "boarding",
    RETARDE: "late",
    PARTI: "departed",
    TERMINE: "arrived",
    ANNULE: "cancelled",
  })[status];
const routeName = (item: Depart) =>
  `${item.itineraire?.destination_depart?.nom || `#${item.id_itineraire}`} → ${item.itineraire?.destination_arrivee?.nom || "Destination"}`;
const formatDate = (value: string) =>
  new Date(`${value}T00:00:00`).toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
const formatTime = (value?: string | null) =>
  value
    ? new Date(value).toLocaleString("fr-FR", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Non pointé";
const canLeave = (item: Depart) =>
  ["PROGRAMME", "EMBARQUEMENT", "RETARDE"].includes(item.statut);
const canArrive = (item: Depart) => item.statut === "PARTI";
const chauffeurLabel = (chauffeur: Chauffeur) =>
  `${chauffeur.user?.first_name || ""} ${chauffeur.user?.name || ""}`.trim() ||
  `Chauffeur #${chauffeur.id}`;
const historyDriverName = (item: Depart) => {
  const chauffeur = chauffeurs.value.find(
    (value) => value.id === item.id_chauffeur,
  );
  return chauffeur
    ? chauffeurLabel(chauffeur)
    : item.chauffeur?.numero_permis || `Chauffeur #${item.id_chauffeur}`;
};

async function loadChauffeurs() {
  if (isDriver.value) return;
  try {
    const result = await allPages((params) => chauffeurService.listChauffeurs(params), {
      page: 1,
      page_size: 100,
      sort_by: "created_at",
      sort_order: "asc",
    });
    chauffeurs.value = result.items || [];
  } catch {
    // L'historique reste consultable par identifiant même si la liste des chauffeurs est indisponible.
    chauffeurs.value = [];
  }
}

async function load(showLoader = true) {
  if (showLoader) loading.value = true;
  else refreshing.value = true;
  error.value = "";
  try {
    const result = isDriver.value
      ? await allPages((params) => departService.listMine(params), {
          page: 1,
          page_size: 100,
          sort_by: "date_depart",
          sort_order: "asc",
        })
      : await allPages((params) => departService.list(params), {
          page: 1,
          page_size: 100,
          sort_by: "date_depart",
          sort_order: "asc",
          date_from: new Date().toISOString().slice(0, 10),
        });
    items.value = result.items || [];
  } catch (value: unknown) {
    error.value = userError(
      value,
      "Impossible de charger le suivi des pointages.",
      "DRIVER_POINTAGE_WEB_ERROR",
    );
  } finally {
    loading.value = false;
    refreshing.value = false;
  }
}

async function loadHistory() {
  historyLoading.value = true;
  historyError.value = "";
  try {
    const params = {
      page: 1,
      page_size: 100,
      date_from: historyFrom.value || undefined,
      date_to: historyTo.value || undefined,
      sort_by: "date_depart",
      sort_order: "desc",
    };
    const result = isDriver.value
      ? await departService.listMine(params)
      : await departService.list({
          ...params,
          id_chauffeur: selectedChauffeur.value
            ? Number(selectedChauffeur.value)
            : undefined,
        });
    historyItems.value = (result.items || []).filter(
      (item: Depart) => item.date_heure_depart || item.date_heure_arrivee,
    );
    historyLoaded.value = true;
  } catch (value: unknown) {
    historyError.value = userError(
      value,
      "Impossible de charger l’historique des pointages.",
      "DRIVER_POINTAGE_HISTORY_ERROR",
    );
  } finally {
    historyLoading.value = false;
  }
}

async function point(item: Depart, type: "DEPART" | "ARRIVEE") {
  if (busyId.value) return;
  const label = type === "DEPART" ? "le départ" : "l’arrivée";
  if (!window.confirm(`Confirmer ${label} pour ${routeName(item)} ?`)) return;
  busyId.value = item.id;
  actionError.value = "";
  success.value = "";
  try {
    const updated = await departService.pointage(item.id, type);
    Object.assign(item, updated);
    success.value =
      type === "DEPART"
        ? "Départ pointé. Le statut est maintenant « Parti »."
        : "Arrivée pointée. Le trajet est maintenant terminé.";
    if (historyLoaded.value) await loadHistory();
  } catch (value: unknown) {
    actionError.value = userError(
      value,
      "Le pointage n’a pas été enregistré. Vérifiez que ce départ vous est bien affecté.",
      "DRIVER_POINTAGE_ACTION_ERROR",
    );
  } finally {
    busyId.value = null;
  }
}

onMounted(async () => {
  await load();
  await loadChauffeurs();
  await loadHistory();
});
</script>

<template>
  <AppLayout>
    <template #title>Pointage chauffeur</template>
    <section class="page-intro">
      <div>
        <p class="eyebrow">SUIVI OPÉRATIONNEL</p>
        <h2>Pointage chauffeur</h2>
        <p>
          {{
            isDriver
              ? "Pointez vos départs et arrivées depuis le web, comme dans l’application mobile."
              : "Suivez en temps réel les départs pointés par les chauffeurs."
          }}
        </p>
      </div>
      <button
        class="secondary-button"
        type="button"
        :disabled="loading || refreshing"
        @click="load(false)"
      >
        {{ refreshing ? "Actualisation…" : "Actualiser" }}
      </button>
    </section>
    <p v-if="loading" class="status-msg">Chargement des départs…</p>
    <p v-else-if="error" class="error-banner" role="alert">
      {{ error }} <button type="button" @click="load()">Réessayer</button>
    </p>
    <template v-else>
      <p v-if="success" class="success-banner" role="status">{{ success }}</p>
      <p v-if="actionError" class="error-banner" role="alert">
        {{ actionError }}
      </p>
      <BaseCard v-if="!items.length"
        ><div class="empty-state">
          <strong>Aucun départ à suivre.</strong
          ><span
            >Les départs affectés apparaîtront ici avec leur état de
            pointage.</span
          >
        </div></BaseCard
      >
      <section v-else class="pointage-list" aria-label="Départs à pointer">
        <BaseCard v-for="item in items" :key="item.id" class="pointage-card"
          ><div class="pointage-head">
            <div>
              <p class="pointage-kicker">
                {{ formatDate(item.date_depart) }} · départ prévu à
                {{ item.heure_depart.slice(0, 5) }}
              </p>
              <h3>{{ routeName(item) }}</h3>
              <p class="pointage-context">
                {{
                  item.vehicule?.immatriculation ||
                  `Véhicule #${item.id_vehicule}`
                }}
                ·
                {{
                  item.cooperative?.nom || `Coopérative #${item.id_cooperative}`
                }}
                · {{ item.places_reservees }}/{{ item.nombre_places }} place(s)
                réservée(s)
              </p>
            </div>
            <span :class="['pointage-status', statusClass(item.statut)]">{{
              statusLabels[item.statut]
            }}</span>
          </div>
          <div class="pointage-times">
            <div>
              <small>Départ réel</small
              ><strong>{{ formatTime(item.date_heure_depart) }}</strong>
            </div>
            <div>
              <small>Arrivée réelle</small
              ><strong>{{ formatTime(item.date_heure_arrivee) }}</strong>
            </div>
            <div>
              <small>Chauffeur</small
              ><strong>{{
                item.chauffeur?.numero_permis || `#${item.id_chauffeur}`
              }}</strong>
            </div>
          </div>
          <div class="pointage-actions">
            <button
              v-if="isDriver && canLeave(item)"
              class="primary-button compact-button"
              type="button"
              :disabled="busyId === item.id"
              @click="point(item, 'DEPART')"
            >
              {{
                busyId === item.id ? "Enregistrement…" : "Pointer le départ"
              }}</button
            ><button
              v-if="isDriver && canArrive(item)"
              class="primary-button compact-button"
              type="button"
              :disabled="busyId === item.id"
              @click="point(item, 'ARRIVEE')"
            >
              Pointer l’arrivée</button
            ><span
              v-if="isDriver && item.statut === 'TERMINE'"
              class="pointage-complete"
              >Pointage terminé</span
            ><RouterLink
              class="secondary-button compact-button"
              :to="`/departs/${item.id}`"
              >Voir le détail</RouterLink
            >
          </div></BaseCard
        >
      </section>
      <BaseCard class="history-card">
        <div class="card-heading history-heading">
          <div>
            <p class="eyebrow">HISTORIQUE</p>
            <h2>Historique des pointages</h2>
            <p>
              {{
                isDriver
                  ? "Retrouvez vos départs et arrivées enregistrés."
                  : "Consultez les pointages de chaque chauffeur et vérifiez les heures réellement enregistrées."
              }}
            </p>
          </div>
          <button
            class="secondary-button"
            type="button"
            :disabled="historyLoading"
            @click="loadHistory"
          >
            {{ historyLoading ? "Chargement…" : "Rechercher" }}
          </button>
        </div>
        <form class="history-filters" @submit.prevent="loadHistory">
          <label v-if="!isDriver" class="form-field"
            ><span>Chauffeur</span
            ><SearchSelect
              aria-label="Tous les chauffeurs"
              v-model="selectedChauffeur"
              :options="
                chauffeurs.map((chauffeur) => ({
                  value: String(chauffeur.id),
                  label: `${chauffeurLabel(chauffeur)} · permis ${chauffeur.numero_permis}`,
                }))
              "
              placeholder="Tous les chauffeurs"
          /></label>
          <label class="form-field"
            ><span>Du</span><input v-model="historyFrom" type="date"
          /></label>
          <label class="form-field"
            ><span>Au</span><input v-model="historyTo" type="date"
          /></label>
        </form>
        <p v-if="historyError" class="error-banner" role="alert">
          {{ historyError }}
          <button type="button" @click="loadHistory">Réessayer</button>
        </p>
        <p v-else-if="historyLoading" class="status-msg">
          Chargement de l’historique…
        </p>
        <div
          v-else-if="historyLoaded && !historyItems.length"
          class="empty-state"
        >
          <strong>Aucun pointage trouvé.</strong
          ><span>Modifiez les dates ou sélectionnez un autre chauffeur.</span>
        </div>
        <div v-else-if="historyItems.length" class="history-table-wrap">
          <table class="history-table">
            <thead>
              <tr>
                <th>Chauffeur</th>
                <th>Trajet et départ prévu</th>
                <th>Départ réel</th>
                <th>Arrivée réelle</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in historyItems" :key="`history-${item.id}`">
                <td>
                  <strong>{{ historyDriverName(item) }}</strong
                  ><small
                    >Permis
                    {{
                      item.chauffeur?.numero_permis || `#${item.id_chauffeur}`
                    }}</small
                  >
                </td>
                <td>
                  <strong>{{ routeName(item) }}</strong
                  ><small
                    >{{ formatDate(item.date_depart) }} ·
                    {{ item.heure_depart.slice(0, 5) }}</small
                  >
                </td>
                <td>{{ formatTime(item.date_heure_depart) }}</td>
                <td>{{ formatTime(item.date_heure_arrivee) }}</td>
                <td>
                  <span
                    :class="['pointage-status', statusClass(item.statut)]"
                    >{{ statusLabels[item.statut] }}</span
                  >
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </BaseCard>
    </template>
  </AppLayout>
</template>

<style scoped>
.pointage-list {
  display: grid;
  gap: 1rem;
}
.pointage-card {
  display: grid;
  gap: 1rem;
}
.pointage-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
}
.pointage-kicker {
  margin: 0 0 0.35rem;
  color: var(--brand);
  font-size: 0.75rem;
  font-weight: 800;
}
.pointage-head h3 {
  margin: 0;
  color: var(--ink-strong);
  font:
    800 1.25rem Manrope,
    sans-serif;
}
.pointage-context {
  margin: 0.45rem 0 0;
  color: #718596;
  font-size: 0.875rem;
}
.pointage-status {
  padding: 0.4rem 0.65rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 900;
  white-space: nowrap;
}
.pointage-status.planned {
  color: #496174;
  background: #edf2f6;
}
.pointage-status.boarding {
  color: #9a5a00;
  background: #fff2d8;
}
.pointage-status.late {
  color: #a44338;
  background: #fff0ed;
}
.pointage-status.departed {
  color: #7b4b9b;
  background: #f5edfb;
}
.pointage-status.arrived {
  color: #16704d;
  background: #e8f8ef;
}
.pointage-status.cancelled {
  color: #a13f36;
  background: #fff0ed;
}
.pointage-times {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  padding: 1rem 0;
  border-top: 1px solid #edf1f4;
  border-bottom: 1px solid #edf1f4;
}
.pointage-times div {
  display: grid;
  gap: 0.25rem;
}
.pointage-times small {
  color: #8a9aa7;
  font-size: 0.75rem;
}
.pointage-times strong {
  color: var(--ink);
  font-size: 0.875rem;
}
.pointage-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.pointage-complete {
  margin-right: auto;
  color: #237252;
  font-size: 0.8125rem;
  font-weight: 800;
}
.pointage-actions button {
  cursor: pointer;
}
.history-card {
  margin-top: 1.25rem;
}
.history-heading {
  align-items: start;
}
.history-heading h2 {
  margin: 0.2rem 0 0.35rem;
}
.history-heading p:last-child {
  margin: 0;
  color: #718596;
}
.history-filters {
  display: grid;
  grid-template-columns: minmax(220px, 1.5fr) repeat(2, minmax(150px, 1fr));
  gap: 1rem;
  margin: 1.25rem 0;
}
.history-filters .form-field {
  display: grid;
  gap: 0.4rem;
}
.history-filters span {
  color: var(--ink-muted);
  font-size: 0.8rem;
  font-weight: 800;
}
.history-filters input,
.history-filters select {
  min-height: 2.7rem;
  padding: 0.55rem 0.7rem;
  border: 1px solid #dbe4ea;
  border-radius: 0.55rem;
  background: #fff;
  color: var(--ink);
}
.history-table-wrap {
  overflow-x: auto;
}
.history-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}
.history-table th,
.history-table td {
  padding: 0.85rem 0.75rem;
  border-top: 1px solid #edf1f4;
  text-align: left;
  vertical-align: middle;
  color: var(--ink-muted);
  font-size: 0.84rem;
}
.history-table th {
  color: #718596;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.history-table td strong,
.history-table td small {
  display: block;
}
.history-table td strong {
  color: var(--ink);
}
.history-table td small {
  margin-top: 0.25rem;
  color: #8a9aa7;
}
.history-table .pointage-status {
  display: inline-block;
}
@media (max-width: 650px) {
  .pointage-head {
    align-items: start;
    flex-direction: column;
  }
  .pointage-times {
    grid-template-columns: 1fr 1fr;
  }
  .pointage-actions {
    justify-content: stretch;
  }
  .pointage-actions button,
  .pointage-actions a {
    flex: 1;
  }
  .pointage-complete {
    width: 100%;
    margin: 0;
  }
  .history-filters {
    grid-template-columns: 1fr;
  }
  .history-heading {
    display: grid;
    gap: 0.75rem;
  }
  .history-heading button {
    width: 100%;
  }
}
@media (max-width: 420px) {
  .pointage-times {
    grid-template-columns: 1fr;
  }
  .pointage-actions {
    display: grid;
  }
  .pointage-actions button,
  .pointage-actions a {
    width: 100%;
  }
}
</style>
