<script setup lang="ts">
import { RouterLink } from "vue-router";
import AppIcon from "../ui/AppIcon.vue";
defineProps<{ compact?: boolean }>();
</script>
<template>
  <footer v-if="compact" class="public-footer-compact">
    <span>© {{ new Date().getFullYear() }} Coopérative</span>
    <nav aria-label="Informations pratiques">
      <RouterLink to="/conditions-voyage">Conditions de voyage</RouterLink
      ><RouterLink to="/confidentialite">Confidentialité</RouterLink>
    </nav>
  </footer>
  <footer v-else class="public-footer">
    <div class="public-footer-inner">
      <div>
        <RouterLink to="/" class="public-brand"
          ><span class="public-brand-symbol"
            ><AppIcon name="route" :size="25" /></span
          ><strong
            >Coopérative<small>LE VOYAGE NOUS RAPPROCHE</small></strong
          ></RouterLink
        >
        <p>
          Vos voyages en taxi-brousse,<br />de la recherche à l’embarquement.
        </p>
      </div>
      <nav aria-label="Voyager">
        <strong>Préparer mon voyage</strong
        ><RouterLink to="/recherche">Trouver un départ</RouterLink
        ><RouterLink to="/ma-reservation">Retrouver ma réservation</RouterLink
        ><RouterLink to="/espace-client">Mon espace</RouterLink>
      </nav>
      <nav aria-label="Informations pratiques">
        <strong>Informations pratiques</strong
        ><RouterLink to="/conditions-voyage">Conditions de voyage</RouterLink
        ><RouterLink to="/annulation">Annulation et modification</RouterLink
        ><RouterLink to="/confidentialite">Confidentialité</RouterLink>
      </nav>
    </div>
    <div class="public-footer-bottom">
      <span>© {{ new Date().getFullYear() }} Coopérative</span
      ><span>Pensé pour les voyageurs et les gares de Madagascar.</span>
    </div>
  </footer>
</template>
