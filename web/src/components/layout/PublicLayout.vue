<script setup lang="ts">
import PublicHeader from "./PublicHeader.vue";
import PublicFooter from "./PublicFooter.vue";
import { watchEffect } from "vue";
import { useRoute } from "vue-router";
const route = useRoute();
defineProps<{ compactFooter?: boolean }>();
const titles: Record<string, string> = {
  "not-found": "Page introuvable",
  frontoffice: "Voyager à Madagascar",
  programme: "Programme des voyages",
  "search-results": "Trouver un voyage",
  "public-booking": "Réserver mon voyage",
  "payment-success": "Suivi du paiement",
  "payment-failure": "Suivi du paiement",
  "public-reservation-lookup": "Retrouver ma réservation",
  "client-space": "Mon espace voyageur",
  "client-reservations": "Mes réservations",
  "client-tickets": "Mes billets",
  "client-profile": "Mon profil",
  "travel-conditions": "Conditions de voyage",
  "cancellation-policy": "Annulation et modification",
  "privacy-policy": "Confidentialité",
};
watchEffect(() => {
  document.title = `${titles[String(route.name)] || "Voyages"} | Coopérative`;
});
</script>
<template>
  <div class="public-shell">
    <a class="skip-link" href="#public-content">Aller au contenu</a
    ><PublicHeader />
    <main id="public-content" tabindex="-1"><slot /></main>
    <PublicFooter :compact="compactFooter" />
  </div>
</template>
