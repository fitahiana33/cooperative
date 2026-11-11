<script setup lang="ts">
import PaginationControls from "../../components/ui/PaginationControls.vue";
import ClientNavigation from "../../components/layout/ClientNavigation.vue";
import PublicLayout from "../../components/layout/PublicLayout.vue";
import { onMounted, onBeforeUnmount, ref } from "vue";
import { RouterLink } from "vue-router";
import { api } from "../../services/api";
import { billetService } from "../../services/billet/service";
import type { Billet } from "../../models/billet/model";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { userError } from "../../utils/errors";

const auth = useAuthenticationStore();
const items = ref<Billet[]>([]);
const loading = ref(true);
const error = ref("");
const search = ref("");
const status = ref("");
const sortOrder = ref("desc");
const page = ref(1);
const pages = ref(1);
const total = ref(0);
const qrSources = ref<Record<number, string>>({});
const qrLoading = ref<Record<number, boolean>>({});
const qrErrors = ref<Record<number, string>>({});
const ticketLabels: Record<string, string> = {
  VALIDE: "Valide",
  UTILISE: "Utilisé",
  ANNULE: "Annulé",
};
async function loadQr(id: number) {
  if (qrLoading.value[id] || qrSources.value[id]) return;
  qrLoading.value[id] = true;
  qrErrors.value[id] = "";
  try {
    const response = await api.get<Blob>(`/billets/${id}/qr.png`, {
      responseType: "blob",
    });
    qrSources.value[id] = URL.createObjectURL(response.data);
  } catch {
    qrErrors.value[id] =
      "Le QR Code est indisponible. Réessayez ou présentez la référence du billet à la gare.";
  } finally {
    qrLoading.value[id] = false;
  }
}
onBeforeUnmount(() =>
  Object.values(qrSources.value).forEach((url) => URL.revokeObjectURL(url)),
);
function statusClass(status: string) {
  return status.toLowerCase();
}
function formatDate(value?: string) {
  return value
    ? new Intl.DateTimeFormat("fr-FR", {
        day: "2-digit",
        month: "long",
        year: "numeric",
      }).format(new Date(`${value}T00:00:00`))
    : "Date à confirmer";
}
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const result = await billetService.list({
      page: page.value,
      page_size: 12,
      search: search.value.trim() || undefined,
      statut: status.value || undefined,
      sort_by: "date_emission",
      sort_order: sortOrder.value,
    });
    items.value = result.items || [];
    total.value = result.total || 0;
    pages.value = Math.max(1, Math.ceil(total.value / 12));
  } catch (value: unknown) {
    error.value = userError(
      value,
      "Impossible de charger vos billets.",
      "CLIENT_TICKETS_ERROR",
    );
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>

<template>
  <PublicLayout class="client-ticket-page"
    ><ClientNavigation />
    <section class="client-ticket-hero">
      <p>ESPACE PASSAGER</p>
      <h1>Mes billets</h1>
      <span>Vos billets confirmés et leurs informations d’embarquement.</span>
    </section>
    <section class="client-ticket-content">
      <div class="client-ticket-heading">
        <div>
          <p>VOYAGES CONFIRMÉS</p>
          <h2>{{ loading ? "…" : total }} billet{{ total > 1 ? "s" : "" }}</h2>
        </div>
        <RouterLink class="client-ticket-primary" to="/recherche"
          >Réserver un voyage →</RouterLink
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
            placeholder="Rechercher une billet" /></label
        ><label
          >Statut<select
            v-model="status"
            @change="
              page = 1;
              load();
            "
          >
            <option value="">Tous les statuts</option>
            <option value="VALIDE">Valide</option>
            <option value="UTILISE">Utilisé</option>
            <option value="ANNULE">Annulé</option>
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
      <p v-if="loading" class="client-ticket-state">
        Chargement de vos billets…
      </p>
      <p v-else-if="error" class="client-ticket-error" role="alert">
        {{ error }} <button type="button" @click="load">Réessayer</button>
      </p>
      <div v-else-if="items.length" class="client-ticket-grid">
        <article
          v-for="item in items"
          :key="item.id"
          class="client-ticket-card"
        >
          <div class="client-ticket-card-top">
            <span
              class="client-ticket-status"
              :class="statusClass(item.statut)"
              >{{ ticketLabels[item.statut] || item.statut }}</span
            ><strong>{{ item.numero_billet }}</strong>
          </div>
          <h3>
            {{ item.destination_depart || "Départ" }} →
            {{ item.destination_arrivee || "Destination" }}
          </h3>
          <p>
            {{ formatDate(item.date_depart) }} · départ à
            {{ item.heure_depart?.slice(0, 5) || "—" }}
          </p>
          <div class="client-ticket-details">
            <span
              ><small>Place</small><b>{{ item.numero_place || "—" }}</b></span
            ><span
              ><small>Réservation</small
              ><b>{{ item.numero_reservation || "—" }}</b></span
            ><span
              ><small>Coopérative</small
              ><b>{{ item.nom_cooperative || "—" }}</b></span
            >
          </div>
          <div v-if="item.statut !== 'ANNULE'" class="client-ticket-qr">
            <template v-if="qrSources[item.id]"
              ><img
                :src="qrSources[item.id]"
                :alt="`QR Code du billet ${item.numero_billet}`"
                width="160"
                height="160"
              /><small>Présentez ce QR Code au contrôle d’embarquement.</small
              ><a
                class="client-outline"
                :href="qrSources[item.id]"
                :download="`${item.numero_billet}.png`"
                >Enregistrer le QR Code</a
              ></template
            ><button
              v-else
              class="client-outline"
              type="button"
              :disabled="qrLoading[item.id]"
              @click="loadQr(item.id)"
            >
              {{ qrLoading[item.id] ? "Chargement…" : "Afficher mon QR Code" }}
            </button>
            <p
              v-if="qrErrors[item.id]"
              class="client-ticket-error"
              role="alert"
            >
              {{ qrErrors[item.id] }}
            </p>
          </div>
        </article>
      </div>
      <div v-else class="client-ticket-empty">
        <strong>Aucun billet pour ces critères.</strong
        ><span
          >Un billet apparaît après confirmation de l’avance de votre
          réservation.</span
        ><RouterLink class="client-ticket-primary" to="/mes-reservations"
          >Voir mes réservations</RouterLink
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
      /></section
  ></PublicLayout>
</template>
