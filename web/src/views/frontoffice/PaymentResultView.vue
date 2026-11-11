<script setup lang="ts">
import PublicLayout from "../../components/layout/PublicLayout.vue";
import { computed, onMounted, onUnmounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { reservationService } from "../../services/reservation/service";
import type { Reservation } from "../../models/reservation/model";

const route = useRoute();
const reference = String(route.query.reference || "");
const paymentAccess = (() => {
  if (!reference) return null;
  try {
    const stored = localStorage.getItem(`reservation-payment:${reference}`);
    return stored
      ? (JSON.parse(stored) as { reservationNumber?: string; token?: string })
      : null;
  } catch (value) {
    if (import.meta.env.DEV) console.error("[PAYMENT_ACCESS_ERROR]", value);
    return null;
  }
})();
const reservationNumber = paymentAccess?.reservationNumber || reference;
const token = (() => {
  try {
    return (
      paymentAccess?.token ||
      (reservationNumber
        ? localStorage.getItem(`reservation-access:${reservationNumber}`)
        : "") ||
      (reference
        ? sessionStorage.getItem(`reservation-access:${reference}`)
        : "") ||
      ""
    );
  } catch {
    return "";
  }
})();
const reservation = ref<Reservation | null>(null);
const paymentConfirmed = computed(() =>
  ["PAYEE", "EMBARQUEE", "TERMINEE"].includes(reservation.value?.statut || ""),
);
const paymentRejected = computed(() => route.name === "payment-failure");
const loading = ref(true);
const waiting = ref(true);
const error = ref("");
const copied = ref(false);
const copyError = ref("");
let timer: ReturnType<typeof setInterval> | undefined;

async function refresh() {
  if (!reference || !token) {
    error.value =
      "Le code d’accès de cette réservation n’est plus disponible dans ce navigateur.";
    loading.value = false;
    waiting.value = false;
    return;
  }
  try {
    reservation.value = await reservationService.publicGet(
      reservationNumber,
      token,
    );
    error.value = "";
    waiting.value = reservation.value.statut === "EN_ATTENTE" && !paymentRejected.value;
    if (!waiting.value && timer) {
      clearInterval(timer);
      timer = undefined;
    }
  } catch (value) {
    if (import.meta.env.DEV) console.error("[PAYMENT_RESULT_ERROR]", value);
    error.value = "Le statut du paiement ne peut pas encore être vérifié.";
  } finally {
    loading.value = false;
  }
}
async function copyAccessCode() {
  copyError.value = "";
  try {
    await navigator.clipboard.writeText(token);
    copied.value = true;
  } catch (value) {
    if (import.meta.env.DEV)
      console.error("[PAYMENT_ACCESS_COPY_ERROR]", value);
    copyError.value =
      "Copie impossible. Sélectionnez le code pour le copier manuellement.";
  }
}
onMounted(async () => {
  await refresh();
  if (waiting.value) timer = setInterval(refresh, 3000);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<template>
  <PublicLayout class="payment-result-page"
    ><section class="payment-result-card">
      <div
        class="result-icon"
        :class="{
          success: paymentConfirmed,
          failure:
            paymentRejected || reservation?.statut === 'ANNULEE' ||
            reservation?.statut === 'EXPIREE',
        }"
      >
        {{ reservation?.statut === "PAYEE" ? "✓" : "…" }}
      </div>
      <p class="result-kicker">PAIEMENT MOBILE MONEY</p>
      <h1>
        {{
          paymentConfirmed
            ? "Paiement confirmé"
            : paymentRejected
              ? "Paiement non confirmé"
            : reservation?.statut === "ANNULEE" ||
                reservation?.statut === "EXPIREE"
              ? "Réservation non confirmée"
              : "Vérification du paiement"
        }}
      </h1>
      <p v-if="loading">Nous récupérons le résultat de votre paiement…</p>
      <p v-else-if="error" class="result-error" role="alert">{{ error }}</p>
      <p v-else-if="waiting">
        Papi a reçu votre demande. Cette page se met à jour automatiquement.
      </p>
      <p v-else-if="paymentRejected">
        Le prestataire n’a pas confirmé ce paiement. Votre réservation reste en
        attente : ouvrez son suivi pour relancer un paiement sans créer une
        seconde réservation.
      </p>
      <p v-else-if="paymentConfirmed && reservation">
        Le paiement de la réservation
        <strong>{{ reservation.numero_reservation }}</strong> est confirmée. Le
        solde restant à régler est affiché ci-dessous.
      </p>
      <p v-else>
        La réservation {{ reservation?.numero_reservation || reference }} n’est
        pas confirmée. Vous pouvez contacter la gare.
      </p>
      <div v-if="reservation" class="result-details">
        <span
          >Réservation<strong>{{
            reservation.numero_reservation
          }}</strong></span
        ><span
          >Total<strong
            >{{
              Number(reservation.montant_total).toLocaleString("fr-FR")
            }}
            Ar</strong
          ></span
        ><span
          >Déjà réglé<strong
            >{{
              Number(reservation.montant_paye).toLocaleString("fr-FR")
            }}
            Ar</strong
          ></span
        ><span
          >Reste à régler<strong
            >{{
              Number(reservation.montant_restant).toLocaleString("fr-FR")
            }}
            Ar</strong
          ></span
        >
      </div>
      <section v-if="reservation && token" class="result-access">
        <h2>Conservez votre accès</h2>
        <p>
          Ce code permet de retrouver cette réservation sans compte. Gardez-le
          privé.
        </p>
        <label
          >Code d’accès<input
            :value="token"
            readonly
            aria-label="Code d’accès à la réservation" /></label
        ><button class="copy-access" type="button" @click="copyAccessCode">
          {{ copied ? "Code copié" : "Copier le code" }}
        </button>
        <p v-if="copyError" class="result-error" role="alert">
          {{ copyError }}
        </p>
      </section>
      <div class="result-actions">
        <RouterLink
          class="result-button primary"
          :to="{ name: 'public-reservation-lookup', query: { reference } }"
          >Retrouver ma réservation</RouterLink
        ><RouterLink class="result-button secondary" to="/"
          >Retour à l’accueil</RouterLink
        >
      </div>
    </section></PublicLayout
  >
</template>
