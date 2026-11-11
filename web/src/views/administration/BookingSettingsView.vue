<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import AppLayout from "../../components/layout/AppLayout.vue";
import { api } from "../../services/api";
import { userError } from "../../utils/errors";
import { formatMoney } from "../../utils/money";
type Configuration = {
  deposit_percentage: number;
  minimum_deposit_amount: number;
  booking_close_minutes: number;
  updated_at: string | null;
};
const configuration = ref<Configuration | null>(null);
const percentage = ref(25);
const bookingCloseMinutes = ref(10);
const busy = ref(false);
const error = ref("");
const success = ref("");
const example = computed(() =>
  Math.min(
    50000,
    Math.max(
      configuration.value?.minimum_deposit_amount || 0,
      Math.ceil((50000 * percentage.value) / 100),
    ),
  ),
);
async function load() {
  busy.value = true;
  try {
    configuration.value = (
      await api.get<Configuration>("/system/booking-settings")
    ).data;
    percentage.value = configuration.value.deposit_percentage;
    bookingCloseMinutes.value = configuration.value.booking_close_minutes;
  } catch (e) {
    error.value = userError(
      e,
      "Impossible de charger ou enregistrer ces données.",
      "BOOKING_SETTINGS_ERROR",
    );
  } finally {
    busy.value = false;
  }
}
async function save() {
  error.value = "";
  success.value = "";
  if (
    !Number.isFinite(percentage.value) ||
    percentage.value <= 0 ||
    percentage.value > 100
  ) {
    error.value =
      "Renseignez un pourcentage supérieur à 0 et inférieur ou égal à 100.";
    return;
  }
  if (
    !Number.isInteger(bookingCloseMinutes.value) ||
    bookingCloseMinutes.value < 0 ||
    bookingCloseMinutes.value > 180
  ) {
    error.value = "Le délai de fermeture doit être compris entre 0 et 180 minutes.";
    return;
  }
  busy.value = true;
  try {
    configuration.value = (
      await api.put<Configuration>("/system/booking-settings", {
        deposit_percentage: percentage.value,
        booking_close_minutes: bookingCloseMinutes.value,
      })
    ).data;
    success.value =
      "Le pourcentage est enregistré pour les nouvelles réservations.";
  } catch (e) {
    error.value = userError(
      e,
      "Impossible de charger ou enregistrer ces données.",
      "BOOKING_SETTINGS_ERROR",
    );
  } finally {
    busy.value = false;
  }
}
onMounted(load);
</script>
<template>
  <AppLayout>
    <template #title>Paramètres de réservation</template>
    <div class="page-header">
      <div>
        <h2>Paramètres de réservation</h2>
        <p>
          Les conditions d’acompte appliquées sur le web, au guichet et sur
          mobile.
        </p>
      </div>
    </div>
    <p v-if="error" class="error-banner" role="alert">
      {{ error }} <button v-if="!configuration" @click="load">Réessayer</button>
    </p>
    <p v-if="success" class="success-banner" role="status">{{ success }}</p>
    <form
      v-if="configuration"
      class="deposit-settings card"
      @submit.prevent="save"
    >
      <h2>Acompte à la réservation</h2>
      <p>
        Ce montant minimum confirme la réservation après validation du paiement.
        Le solde reste à régler selon les conditions de voyage.
      </p>
      <label for="deposit-percentage">Pourcentage d’acompte minimum (%)</label>
      <input
        id="deposit-percentage"
        v-model.number="percentage"
        type="number"
        min="0.01"
        max="100"
        step="0.01"
        required
        :disabled="busy"
        aria-describedby="deposit-example"
      />
      <p id="deposit-example">
        Pour un voyage de 50 000 Ar :
        <strong>{{ formatMoney(example, "MGA") }}</strong> d’acompte minimum.
      </p>
      <p>
        Le plancher technique est de
        {{ formatMoney(configuration.minimum_deposit_amount, "MGA") }}, dans la
        limite du montant du voyage. L’acompte est arrondi à l’ariary supérieur.
      </p>
      <p class="info-banner">
        Les réservations existantes conservent leurs conditions enregistrées. Le
        nouveau pourcentage s’applique uniquement aux nouvelles réservations. Au
        guichet, le montant restant est encaissé intégralement.
      </p>
      <hr />
      <h2>Fermeture des réservations</h2>
      <p>
        Ce délai protège l’embarquement : aucune nouvelle place ni paiement en
        ligne ne peut être initié après l’heure calculée.
      </p>
      <label for="booking-close-minutes">Fermer avant le départ (minutes)</label>
      <input
        id="booking-close-minutes"
        v-model.number="bookingCloseMinutes"
        type="number"
        min="0"
        max="180"
        step="1"
        required
        :disabled="busy"
      />
      <p class="info-banner">
        Exemple : 10 signifie qu’une réservation reste possible jusqu’à 10
        minutes avant l’horaire prévu. Un départ dépassé passe automatiquement
        en retardé tant qu’il n’a pas été pointé comme parti.
      </p>
      <button class="primary-button" :disabled="busy">
        {{ busy ? "Enregistrement…" : "Enregistrer les conditions" }}
      </button>
      <small v-if="configuration.updated_at"
        >Dernière modification :
        {{ new Date(configuration.updated_at).toLocaleString("fr-FR") }}</small
      >
    </form>
    <p v-else-if="busy" role="status">Chargement des paramètres…</p>
  </AppLayout>
</template>
<style scoped>
.deposit-settings {
  max-width: 760px;
  padding: 28px;
  display: grid;
  gap: 18px;
}
.deposit-settings h2,
.deposit-settings p {
  margin: 0;
}
.deposit-settings p {
  line-height: 1.65;
}
.deposit-settings input {
  width: min(100%, 220px);
  padding: 12px;
  border: 1px solid var(--border, #cdd7d1);
  border-radius: 8px;
}
.deposit-settings button {
  justify-self: start;
}
</style>
