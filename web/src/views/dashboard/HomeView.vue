<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import AppIcon from "../../components/ui/AppIcon.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import StatCard from "../../components/ui/StatCard.vue";
import type { DashboardSummary } from "../../models/dashboard/model";
import { dashboardService } from "../../services/dashboard/service";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { userError } from "../../utils/errors";
const auth = useAuthenticationStore();
const data = ref<DashboardSummary | null>(null);
const loading = ref(false);
const error = ref("");
const lastUpdated = ref<Date | null>(null);
const canReadDashboard = computed(() => auth.hasPermission("DASHBOARD_READ"));
const moneyValue = computed(() => Number(data.value?.recettes_du_jour || 0));
const money = computed(() => {
  if (moneyValue.value < 1_000_000)
    return `${moneyValue.value.toLocaleString("fr-FR")} Ar`;
  return `${new Intl.NumberFormat("fr-FR", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(moneyValue.value)} Ar`;
});
const moneyFull = computed(() => `${moneyValue.value.toLocaleString("fr-FR")} Ar encaissés`);
const displayDate = computed(() =>
  data.value?.date
    ? new Intl.DateTimeFormat("fr-FR", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      }).format(new Date(data.value.date + "T00:00:00"))
    : "Aujourd’hui",
);
const stats = computed(() => [
  {
    label: "Départs du jour",
    value: String(data.value?.departs_du_jour ?? 0),
    detail: "Au programme aujourd’hui",
    icon: "◷",
    tone: "stat-blue",
  },
  {
    label: "Réservations",
    value: String(data.value?.reservations_du_jour ?? 0),
    detail: `${data.value?.passagers_du_jour ?? 0} passager(s) distinct(s)`,
    icon: "▤",
    tone: "stat-purple",
  },
  {
    label: "Places disponibles",
    value: String(data.value?.places_disponibles ?? 0),
    detail: "Disponibilité du jour",
    icon: "▦",
    tone: "stat-green",
  },
  {
    label: "Encaissements guichet",
    value: money.value,
    detail: moneyFull.value,
    icon: "◈",
    tone: "stat-green",
  },
  {
    label: "Départs retardés",
    value: String(data.value?.departs_retardes ?? 0),
    detail: `${data.value?.departs_annules ?? 0} départ(s) annulé(s)`,
    icon: "!",
    tone: "stat-orange",
  },
  {
    label: "Départs complets",
    value: String(data.value?.departs_complets ?? 0),
    detail: "Toutes les places réservées",
    icon: "✓",
    tone: "stat-blue",
  },
]);
const actions = computed(() =>
  [
    {
      label: "Créer une réservation",
      description: "Vendre et attribuer des places",
      to: "/reservations/new",
      icon: "ticket",
      permission: "RESERVATION_CREATE",
    },
    {
      label: "Planifier un départ",
      description: "Préparer les prochains voyages",
      to: "/departs/new",
      icon: "calendar",
      permission: "DEPART_CREATE",
    },
    {
      label: "Contrôler un billet",
      description: "Accéder à l’embarquement",
      to: "/embarquement",
      icon: "scan",
      permission: "EMBARQUEMENT_MANAGE",
    },
    {
      label: "Ouvrir la caisse",
      description: "Consulter les encaissements",
      to: "/finance",
      icon: "wallet",
      permission: "CAISSE_READ",
    },
    {
      label: "Mes pointages",
      description: "Départ et arrivée des voyages",
      to: "/pointage-chauffeur",
      icon: "check",
      permission: "DEPART_POINTAGE",
    },
  ].filter((action) => auth.hasPermission(action.permission)),
);
const workspace = computed(() => {
  const roles = [auth.user?.role, ...(auth.user?.roles || []).map((item) => item.libelle)]
    .filter(Boolean).map((item) => String(item).toLowerCase());
  if (roles.includes("chauffeur")) return {
    eyebrow: "POSTE CHAUFFEUR", title: "Vos trajets et pointages", description: "Commencez par le prochain trajet à confirmer, puis consultez votre historique.",
    links: [{ label: "Ouvrir mes pointages", to: "/pointage-chauffeur", permission: "DEPART_POINTAGE" }, { label: "Voir le planning", to: "/planning", permission: "DEPART_READ" }],
  };
  if (roles.some((role) => ["guichetier", "agent_gare", "agent de gare"].includes(role))) return {
    eyebrow: "POSTE GUICHET", title: "Ventes, encaissements et embarquement", description: "Traitez d’abord les ventes du jour, puis contrôlez les billets avant le départ.",
    links: [{ label: "Nouvelle réservation", to: "/reservations/new", permission: "RESERVATION_CREATE" }, { label: "Contrôler les billets", to: "/embarquement", permission: "EMBARQUEMENT_MANAGE" }, { label: "Accéder à la caisse", to: "/finance", permission: "CAISSE_READ" }],
  };
  if (roles.some((role) => role.includes("cooper")) || auth.hasPermission("VEHICULE_UPDATE")) return {
    eyebrow: "POSTE COOPÉRATIVE", title: "Vos ressources à préparer", description: "Vérifiez les véhicules, chauffeurs et départs avant la mise en vente.",
    links: [{ label: "Voir les départs", to: "/departs", permission: "DEPART_READ" }, { label: "Gérer les véhicules", to: "/vehicules", permission: "VEHICULE_READ" }, { label: "Gérer les chauffeurs", to: "/chauffeurs", permission: "CHAUFFEUR_READ" }],
  };
  return {
    eyebrow: "PILOTAGE", title: "Votre poste de supervision", description: "Suivez les exceptions du jour et accédez aux opérations prioritaires.",
    links: [{ label: "Ouvrir le planning", to: "/planning", permission: "DEPART_READ" }, { label: "Suivre les réservations", to: "/reservations", permission: "RESERVATION_READ" }, { label: "Consulter les statistiques", to: "/statistiques", permission: "STATISTIQUE_READ" }],
  };
});
const statusLabels: Record<string, string> = {
  PROGRAMME: "Programmé",
  EMBARQUEMENT: "Embarquement",
  RETARDE: "Retardé",
  PARTI: "Parti",
  ARRIVE: "Arrivé",
  ANNULE: "Annulé",
};
function routeName(item: DashboardSummary["departs_imminents"][number]) {
  return `${item.itineraire?.destination_depart?.nom || "Départ"} → ${item.itineraire?.destination_arrivee?.nom || "Destination"}`;
}
async function load() {
  if (!canReadDashboard.value || loading.value) return;
  loading.value = true;
  error.value = "";
  try {
    data.value = await dashboardService.summary();
    lastUpdated.value = new Date();
  } catch (value) {
    error.value = userError(
      value,
      "Le tableau de bord est momentanément indisponible.",
      "DASHBOARD_ERROR",
    );
  } finally {
    loading.value = false;
  }
}
let refreshTimer: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
  void load();
  if (canReadDashboard.value)
    refreshTimer = setInterval(() => {
      if (!document.hidden) void load();
    }, 30000);
});
onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>
<template>
  <AppLayout>
    <template #title>Vue d’ensemble</template>
    <section class="page-intro">
      <div>
        <p class="eyebrow">VOTRE ACTIVITÉ, EN UN COUP D’ŒIL</p>
        <h2>
          Bonjour {{ auth.user?.first_name || auth.user?.name
          }}<span class="greeting-dot">.</span>
        </h2>
        <p class="dashboard-date">{{ displayDate }}</p>
      </div>
      <div class="dashboard-actions">
        <button
          v-if="canReadDashboard"
          class="secondary-button"
          type="button"
          :disabled="loading"
          @click="load"
        >
          <AppIcon name="refresh" :size="15" />{{
            loading ? "Actualisation…" : "Actualiser"
          }}</button
        ><RouterLink
          v-if="auth.hasPermission('RESERVATION_CREATE')"
          class="primary-button"
          to="/reservations/new"
          ><AppIcon name="plus" :size="16" />Nouvelle réservation</RouterLink
        >
      </div>
    </section>
    <p v-if="error" class="error-banner" role="alert">
      {{ error }}
      <button class="text-button" type="button" @click="load">Réessayer</button>
    </p>
    <BaseCard v-if="auth.user" class="role-workspace-card">
      <div><p class="card-eyebrow">{{ workspace.eyebrow }}</p><h2>{{ workspace.title }}</h2><p>{{ workspace.description }}</p></div>
      <div class="role-workspace-actions"><RouterLink v-for="link in workspace.links.filter((item) => auth.hasPermission(item.permission))" :key="link.to" class="secondary-button compact-button" :to="link.to">{{ link.label }} <AppIcon name="arrow" :size="14" /></RouterLink></div>
    </BaseCard>
    <div
      v-if="canReadDashboard && !data && loading"
      class="dashboard-skeleton stats-grid"
      role="status"
      aria-label="Chargement du tableau de bord"
    >
      <div v-for="index in 6" :key="index" />
    </div>
    <template v-if="canReadDashboard && data">
      <section class="stats-grid" aria-label="Indicateurs du jour">
        <StatCard v-for="stat in stats" :key="stat.label" v-bind="stat" />
      </section>
      <div class="dashboard-update-note">
        <span class="live-marker" />Données du jour<small v-if="lastUpdated"
          >Dernière actualisation à
          {{
            lastUpdated.toLocaleTimeString("fr-FR", {
              hour: "2-digit",
              minute: "2-digit",
            })
          }}</small
        >
      </div>
      <BaseCard class="upcoming-card"
        ><div class="card-heading">
          <div>
            <p class="card-eyebrow">PLANNING OPÉRATIONNEL</p>
            <h2>Les prochains départs</h2>
            <p>Les voyages à préparer et à suivre.</p>
          </div>
          <RouterLink
            v-if="auth.hasPermission('DEPART_READ')"
            class="card-link"
            to="/departs"
            >Tous les départs <AppIcon name="arrow" :size="14"
          /></RouterLink>
        </div>
        <div class="table-scroll dashboard-departures">
          <table class="data-table">
            <caption class="sr-only">
              Les huit prochains départs du planning
            </caption>
            <thead>
              <tr>
                <th>Départ</th>
                <th>Itinéraire</th>
                <th>Véhicule</th>
                <th>Réservations</th>
                <th>Statut</th>
                <th><span class="sr-only">Consulter</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in data.departs_imminents" :key="item.id">
                <td>
                  <strong class="departure-hour">{{
                    item.heure_depart?.slice(0, 5)
                  }}</strong
                  ><small>{{ item.date_depart }}</small>
                </td>
                <td>
                  <strong>{{ routeName(item) }}</strong>
                </td>
                <td>{{ item.vehicule?.immatriculation || "Non renseigné" }}</td>
                <td>
                  <span class="occupancy-count"
                    ><strong>{{ item.places_reservees }}</strong> /
                    {{ item.nombre_places }} places</span
                  >
                </td>
                <td>
                  <span
                    class="status-badge"
                    :class="{
                      active:
                        item.statut === 'PROGRAMME' ||
                        item.statut === 'EMBARQUEMENT',
                      inactive: item.statut === 'ANNULE',
                      'badge-warning': item.statut === 'RETARDE',
                    }"
                    >{{ statusLabels[item.statut] || item.statut }}</span
                  >
                </td>
                <td>
                  <RouterLink
                    v-if="auth.hasPermission('DEPART_READ')"
                    class="departure-open"
                    :to="`/departs/${item.id}`"
                    :aria-label="`Consulter le départ ${routeName(item)} à ${item.heure_depart?.slice(0, 5)}`"
                    ><AppIcon name="arrow" :size="17"
                  /></RouterLink>
                </td>
              </tr>
              <tr v-if="!data.departs_imminents.length">
                <td colspan="6" class="empty-state">
                  Aucun départ à venir. Les prochains voyages apparaîtront ici.
                </td>
              </tr>
            </tbody>
          </table>
        </div></BaseCard
      >
    </template>
    <section class="dashboard-lower-grid">
      <BaseCard v-if="actions.length" class="quick-actions-card"
        ><div class="card-heading">
          <div>
            <p class="card-eyebrow">GAGNEZ DU TEMPS</p>
            <h2>Actions rapides</h2>
            <p>Vos opérations les plus courantes.</p>
          </div>
          <AppIcon name="route" :size="22" />
        </div>
        <div class="quick-action-grid">
          <RouterLink v-for="action in actions" :key="action.to" :to="action.to"
            ><span class="quick-action-icon"
              ><AppIcon :name="action.icon" :size="19" /></span
            ><span
              ><strong>{{ action.label }}</strong
              ><small>{{ action.description }}</small></span
            ><AppIcon name="chevron" :size="14"
          /></RouterLink></div
      ></BaseCard>
      <BaseCard v-if="data" class="resource-summary-card"
        ><div class="card-heading">
          <div>
            <p class="card-eyebrow">VOTRE RÉSEAU</p>
            <h2>Ressources actives</h2>
            <p>Les moyens de transport enregistrés.</p>
          </div>
          <AppIcon name="building" :size="22" />
        </div>
        <dl class="resource-summary">
          <div>
            <dt><AppIcon name="users" :size="17" />Coopératives</dt>
            <dd>{{ data.cooperatives_actives }}</dd>
          </div>
          <div>
            <dt><AppIcon name="bus" :size="17" />Véhicules</dt>
            <dd>{{ data.vehicules_actifs }}</dd>
          </div>
          <div>
            <dt><AppIcon name="user" :size="17" />Chauffeurs</dt>
            <dd>{{ data.chauffeurs_actifs }}</dd>
          </div>
        </dl></BaseCard
      >
    </section>
    <BaseCard v-if="!canReadDashboard && !actions.length" class="welcome-card"
      ><h2>Bienvenue dans votre espace</h2>
      <p>
        Utilisez le menu pour accéder aux modules autorisés pour votre rôle.
      </p></BaseCard
    >
  </AppLayout>
</template>
