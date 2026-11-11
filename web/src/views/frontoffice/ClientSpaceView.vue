<script setup lang="ts">
import ClientNavigation from "../../components/layout/ClientNavigation.vue";
import PublicLayout from "../../components/layout/PublicLayout.vue";
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { reservationService } from "../../services/reservation/service";
import { billetService } from "../../services/billet/service";
import type { Reservation } from "../../models/reservation/model";

const auth = useAuthenticationStore();
const reservationCount = ref<number | null>(null);
const billetCount = ref<number | null>(null);
const loading = ref(true);
const error = ref("");
async function load() {
  loading.value = true;
  error.value = "";
  const [reservations, billets] = await Promise.allSettled([
    reservationService.list({ page: 1, page_size: 1 }),
    billetService.list({ page: 1, page_size: 1 }),
  ]);
  if (reservations.status === "fulfilled")
    reservationCount.value = reservations.value.total || 0;
  if (billets.status === "fulfilled")
    billetCount.value = billets.value.total || 0;
  if (reservations.status === "rejected" || billets.status === "rejected")
    error.value =
      "Certains compteurs ne sont pas disponibles. Vous pouvez toujours ouvrir vos réservations et vos billets.";
  loading.value = false;
}
onMounted(load);
</script>

<template>
  <PublicLayout class="client-space-page"
    ><ClientNavigation />

    <section class="client-welcome">
      <p class="client-kicker">ESPACE PASSAGER</p>
      <h1>Bonjour {{ auth.user?.first_name || auth.user?.name }}.</h1>
      <p>
        Retrouvez vos réservations, vos billets et vos informations personnelles
        au même endroit.
      </p>
    </section>
    <section class="client-content">
      <p v-if="error" class="client-activity-error" role="alert">
        {{ error }} <button type="button" @click="load">Réessayer</button>
      </p>
      <div class="client-section-title">
        <div>
          <p class="client-kicker">MON ESPACE</p>
          <h2>Que souhaitez-vous faire ?</h2>
        </div>
        <RouterLink class="client-outline" to="/recherche"
          >Rechercher un voyage</RouterLink
        >
      </div>
      <div class="client-cards">
        <RouterLink
          class="client-card client-card-primary"
          to="/mes-reservations"
          ><span class="client-card-icon">01</span
          ><strong>Mes réservations</strong
          ><span
            >Suivez l’état de vos demandes et retrouvez les informations de
            chaque trajet.</span
          ><b
            >{{ loading ? "…" : (reservationCount ?? "—") }} réservation(s) →</b
          ></RouterLink
        ><RouterLink class="client-card" to="/mes-billets"
          ><span class="client-card-icon">02</span><strong>Mes billets</strong
          ><span
            >Accédez à vos billets disponibles et à vos QR Codes pour
            l’embarquement.</span
          ><b
            >{{ loading ? "…" : (billetCount ?? "—") }} billet(s) →</b
          ></RouterLink
        ><RouterLink class="client-card" to="/mon-profil"
          ><span class="client-card-icon">03</span><strong>Mon profil</strong
          ><span
            >Modifiez votre nom, votre téléphone, votre adresse et votre mot de
            passe.</span
          ><b>Gérer mon profil →</b></RouterLink
        >
      </div>
    </section>
    <section class="client-steps">
      <p class="client-kicker">COMMENT ÇA MARCHE ?</p>
      <h2>De la recherche au billet</h2>
      <div>
        <article>
          <b>1</b><strong>Choisissez votre départ</strong
          ><span
            >Comparez les horaires, les prix, les gares et les places
            disponibles.</span
          >
        </article>
        <article>
          <b>2</b><strong>Réservez vos places</strong
          ><span
            >Indiquez le nom de la personne qui réserve. Les autres noms sont
            facultatifs.</span
          >
        </article>
        <article>
          <b>3</b><strong>Payez l’avance</strong
          ><span
            >La réservation reste en attente jusqu’à la confirmation du paiement
            de l’avance.</span
          >
        </article>
        <article>
          <b>4</b><strong>Recevez votre billet</strong
          ><span
            >Après confirmation, le billet et son QR Code sont disponibles dans
            votre espace.</span
          >
        </article>
      </div>
    </section>
  </PublicLayout>
</template>
