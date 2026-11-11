<script setup lang="ts">
import ReservationActions from "../../components/ui/ReservationActions.vue";
import PublicLayout from "../../components/layout/PublicLayout.vue";
import { onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { reservationService } from "../../services/reservation/service";
import type {
  Reservation,
  ReservationStatus,
} from "../../models/reservation/model";

const route = useRoute();
const number = ref("");
const token = ref("");
const reservation = ref<Reservation | null>(null);
const loading = ref(false);
const error = ref("");
const storageWarning = ref("");

const statusLabels: Record<ReservationStatus, string> = {
  EN_ATTENTE: "Paiement en attente",
  CONFIRMEE: "Confirmée",
  PAYEE: "Paiement confirmé",
  ANNULEE: "Annulée",
  EXPIREE: "Expirée",
  EMBARQUEE: "Embarquée",
  TERMINEE: "Terminée",
};

function statusLabel(status: ReservationStatus) {
  return statusLabels[status] || status;
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
  return `${item.depart?.itineraire?.destination_depart?.nom || "Départ"} → ${item.depart?.itineraire?.destination_arrivee?.nom || "Destination"}`;
}

function readPaymentReference(
  reference: string,
): { reservationNumber: string; token: string } | null {
  try {
    const stored = localStorage.getItem(`reservation-payment:${reference}`);
    if (stored) {
      const access = JSON.parse(stored) as {
        reservationNumber?: string;
        token?: string;
      };
      if (
        typeof access.reservationNumber === "string" &&
        typeof access.token === "string"
      ) {
        return {
          reservationNumber: access.reservationNumber,
          token: access.token,
        };
      }
    }
  } catch (value) {
    if (import.meta.env.DEV)
      console.error("[PUBLIC_RESERVATION_ACCESS_ERROR]", value);
  }
  return null;
}

async function lookup() {
  error.value = "";
  storageWarning.value = "";
  reservation.value = null;
  const cleanNumber = number.value.trim();
  const cleanToken = token.value.trim();
  if (!cleanNumber || cleanToken.length < 20) {
    error.value =
      "Saisissez le numéro de réservation et le code d’accès conservé après le paiement.";
    return;
  }

  loading.value = true;
  try {
    reservation.value = await reservationService.publicGet(
      cleanNumber,
      cleanToken,
    );
  } catch (value) {
    if (import.meta.env.DEV)
      console.error("[PUBLIC_RESERVATION_LOOKUP_ERROR]", value);
    error.value =
      "Réservation introuvable ou code d’accès invalide. Vérifiez les informations puis réessayez.";
    loading.value = false;
    return;
  }
  try {
    localStorage.setItem(`reservation-access:${cleanNumber}`, cleanToken);
  } catch (value) {
    if (import.meta.env.DEV)
      console.error("[PUBLIC_RESERVATION_STORAGE_ERROR]", value);
    storageWarning.value =
      "Réservation retrouvée, mais le code d’accès n’a pas pu être mémorisé dans ce navigateur.";
  }
  loading.value = false;
}

onMounted(() => {
  const reference = String(route.query.reference || "");
  if (!reference) return;

  const saved = readPaymentReference(reference);
  if (saved) {
    number.value = saved.reservationNumber;
    token.value = saved.token;
  } else {
    number.value = reference;
    try {
      token.value =
        localStorage.getItem(`reservation-access:${reference}`) || "";
    } catch (value) {
      if (import.meta.env.DEV)
        console.error("[PUBLIC_RESERVATION_STORAGE_READ_ERROR]", value);
      storageWarning.value =
        "Entrez manuellement le code d’accès conservé après le paiement.";
    }
  }
  if (token.value) void lookup();
});
</script>

<template>
  <PublicLayout class="public-lookup-page">
    <section class="public-lookup-hero">
      <p>ESPACE VOYAGEUR</p>
      <h1>Retrouvez votre réservation.</h1>
      <span
        >Consultez son statut et les informations du trajet, même sans
        compte.</span
      >
    </section>
    <section class="public-lookup-content">
      <form class="lookup-card" @submit.prevent="lookup" novalidate>
        <div>
          <p class="lookup-kicker">ACCÈS SÉCURISÉ</p>
          <h2>Consulter une réservation</h2>
          <p>
            Utilisez le numéro de réservation et le code d’accès de votre
            réservation. Après un paiement effectué dans ce navigateur, ces
            informations sont préremplies.
          </p>
        </div>
        <label
          >Référence de réservation
          <input
            v-model="number"
            autocomplete="off"
            placeholder="Ex. RES-2026-0001"
            required
          />
        </label>
        <label
          >Code d’accès
          <input
            v-model="token"
            type="password"
            autocomplete="off"
            placeholder="Votre code d’accès"
            required
          />
        </label>
        <p v-if="error" class="lookup-error" role="alert">{{ error }}</p>
        <p v-if="storageWarning" class="lookup-warning" role="status">
          {{ storageWarning }}
        </p>
        <button class="lookup-submit" type="submit" :disabled="loading">
          {{ loading ? "Vérification…" : "Consulter ma réservation" }}
        </button>
      </form>
      <article v-if="reservation" class="lookup-result">
        <div class="lookup-result-head">
          <div>
            <p class="lookup-kicker">
              RÉSERVATION {{ reservation.numero_reservation }}
            </p>
            <h2>{{ routeLabel(reservation) }}</h2>
          </div>
          <span
            class="lookup-status"
            :class="reservation.statut.toLowerCase().replace('_', '-')"
          >
            {{ statusLabel(reservation.statut) }}
          </span>
        </div>
        <dl>
          <div>
            <dt>Date et heure</dt>
            <dd>
              {{ formatDate(reservation.depart?.date_depart) }} ·
              {{ reservation.depart?.heure_depart?.slice(0, 5) || "—" }}
            </dd>
          </div>
          <div>
            <dt>Places</dt>
            <dd>{{ reservation.places.length }}</dd>
          </div>
          <div>
            <dt>Total</dt>
            <dd>
              {{ Number(reservation.montant_total).toLocaleString("fr-FR") }} Ar
            </dd>
          </div>
          <div>
            <dt>Déjà réglé</dt>
            <dd>
              {{ Number(reservation.montant_paye).toLocaleString("fr-FR") }} Ar
            </dd>
          </div>
          <div>
            <dt>Reste à régler</dt>
            <dd>
              {{
                Number(reservation.montant_restant).toLocaleString("fr-FR")
              }}
              Ar
            </dd>
          </div>
          <div v-if="Number(reservation.montant_a_rembourser) > 0">
            <dt>À rembourser</dt>
            <dd>
              {{
                Number(reservation.montant_a_rembourser).toLocaleString("fr-FR")
              }}
              Ar
            </dd>
          </div>
        </dl>
        <p class="lookup-explanation">
          {{
            reservation.statut === "EN_ATTENTE"
              ? "Le paiement de l’avance est en attente. La réservation sera confirmée après validation du paiement."
              : reservation.statut === "PAYEE"
                ? "Le paiement est confirmé. Le solde affiché ci-dessus est à régler selon les conditions de votre coopérative."
                : "Le statut affiché correspond à la dernière information reçue."
          }}
        </p>
        <ReservationActions :reservation="reservation" :access-token="token" @updated="reservation = $event" />
      </article>
    </section>
  </PublicLayout>
</template>
