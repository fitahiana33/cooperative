<script setup lang="ts">
import ReservationActions from "../../components/ui/ReservationActions.vue";
import PaginationControls from "../../components/ui/PaginationControls.vue";
import ClientNavigation from "../../components/layout/ClientNavigation.vue";
import PublicLayout from "../../components/layout/PublicLayout.vue";
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { reservationService } from "../../services/reservation/service";
import type {
  Reservation,
  ReservationStatus,
} from "../../models/reservation/model";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { userError } from "../../utils/errors";

const auth = useAuthenticationStore();
const items = ref<Reservation[]>([]);
const loading = ref(true);
const error = ref("");
const search = ref("");
const status = ref("");
const sortOrder = ref("desc");
const page = ref(1);
const pages = ref(1);
const total = ref(0);

const statusLabels: Record<ReservationStatus, string> = {
  EN_ATTENTE: "Paiement en attente",
  CONFIRMEE: "Confirmée",
  PAYEE: "Paiement confirmé",
  ANNULEE: "Annulée",
  EXPIREE: "Expirée",
  EMBARQUEE: "Embarquée",
  TERMINEE: "Terminée",
};

function statusClass(status: ReservationStatus) {
  return status.toLowerCase().replace("_", "-");
}
function formatDate(value?: string) {
  return value
    ? new Intl.DateTimeFormat("fr-FR", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
      }).format(new Date(`${value}T00:00:00`))
    : "Date à confirmer";
}
function routeLabel(item: Reservation) {
  const route = item.depart?.itineraire;
  return `${route?.destination_depart?.nom || "Départ"} → ${route?.destination_arrivee?.nom || "Destination"}`;
}
function seatLabel(item: Reservation) {
  return (
    item.places
      .map((place) => place.depart_place?.numero_place || "—")
      .join(", ") || "—"
  );
}
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const result = await reservationService.list({
      page: page.value,
      page_size: 12,
      search: search.value.trim() || undefined,
      statut: status.value || undefined,
      sort_by: "date_depart",
      sort_order: sortOrder.value,
    });
    items.value = result.items || [];
    total.value = result.total || 0;
    pages.value = Math.max(1, Math.ceil(total.value / 12));
  } catch (value: unknown) {
    error.value = userError(
      value,
      "Impossible de charger votre activité.",
      "CLIENT_RESERVATIONS_ERROR",
    );
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>

<template>
  <PublicLayout class="client-activity-page"
    ><ClientNavigation />

    <section class="client-activity-hero">
      <p>ESPACE PASSAGER</p>
      <h1>Mes réservations</h1>
      <span>Retrouvez vos voyages, leur statut et les places réservées.</span>
    </section>
    <section class="client-activity-content">
      <div class="client-activity-heading">
        <div>
          <p class="client-activity-kicker">HISTORIQUE PERSONNEL</p>
          <h2>
            {{ loading ? "…" : total }} réservation{{ total > 1 ? "s" : "" }}
          </h2>
        </div>
        <RouterLink class="client-activity-primary" to="/recherche"
          >Rechercher un voyage →</RouterLink
        >
      </div>
      <form
        class="client-history-filters"
        @submit.prevent="
          page = 1;
          load();
        "
      >
        <label
          >Référence<input
            v-model="search"
            type="search"
            placeholder="Rechercher une réservation" /></label
        ><label
          >Statut<select
            v-model="status"
            @change="
              page = 1;
              load();
            "
          >
            <option value="">Tous les statuts</option>
            <option value="EN_ATTENTE">En attente</option>
            <option value="CONFIRMEE">Confirmée</option>
            <option value="PAYEE">Paiement confirmé</option>
            <option value="ANNULEE">Annulée</option>
            <option value="EXPIREE">Expirée</option>
            <option value="EMBARQUEE">Embarquée</option>
            <option value="TERMINEE">Terminée</option>
          </select></label
        ><label
          >Ordre chronologique<select
            v-model="sortOrder"
            @change="
              page = 1;
              load();
            "
          >
            <option value="desc">Plus récents d’abord</option>
            <option value="asc">Plus anciens d’abord</option>
          </select></label
        ><button
          class="client-ticket-primary"
          type="submit"
          :disabled="loading"
        >
          Rechercher
        </button>
      </form>
      <p v-if="loading" class="client-activity-state">
        Chargement de vos réservations…
      </p>
      <p v-else-if="error" class="client-activity-error" role="alert">
        {{ error }} <button type="button" @click="load">Réessayer</button>
      </p>
      <div v-else-if="items.length" class="client-reservation-list">
        <article
          v-for="item in items"
          :key="item.id"
          class="client-reservation-card"
        >
          <div class="client-reservation-top">
            <span class="client-status" :class="statusClass(item.statut)">{{
              statusLabels[item.statut] || item.statut
            }}</span
            ><strong>{{ item.numero_reservation }}</strong>
          </div>
          <h3>{{ routeLabel(item) }}</h3>
          <p class="client-reservation-date">
            {{ formatDate(item.depart?.date_depart) }} · départ à
            {{ item.depart?.heure_depart?.slice(0, 5) || "—" }}
          </p>
          <div class="client-reservation-meta">
            <span
              ><small>Places</small><b>{{ seatLabel(item) }}</b></span
            ><span
              ><small>Total</small
              ><b
                >{{ Number(item.montant_total).toLocaleString("fr-FR") }} Ar</b
              ></span
            ><span
              ><small>Coopérative</small
              ><b>{{ item.depart?.cooperative?.nom || "—" }}</b></span
            >
          </div>
          <p v-if="item.statut === 'EN_ATTENTE'" class="client-payment-note">
            La réservation sera valide après le paiement de l’avance minimale.
          </p>
          <p
            v-else-if="item.statut === 'PAYEE'"
            class="client-payment-note success"
          >
            Paiement confirmé :
            {{ Number(item.montant_paye).toLocaleString("fr-FR") }} Ar réglés,
            {{ Number(item.montant_restant).toLocaleString("fr-FR") }} Ar
            restants. Vos billets sont disponibles dans « Mes billets ».
          </p>
          <ReservationActions :reservation="item" @updated="load" />
        </article>
      </div>
      <div v-else class="client-activity-empty">
        <strong>Aucune réservation pour ces critères.</strong
        ><span>Consultez le programme et choisissez votre prochain voyage.</span
        ><RouterLink class="client-activity-primary" to="/recherche"
          >Voir les départs</RouterLink
        >
      </div>
      <PaginationControls
        v-if="!error"
        :page="page"
        :pages="pages"
        :total="total"
        :loading="loading"
        @change="
          (next) => {
            page = next;
            load();
          }
        "
      />
    </section>
  </PublicLayout>
</template>
