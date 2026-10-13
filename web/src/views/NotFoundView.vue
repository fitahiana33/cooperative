<script setup lang="ts">
import { RouterLink } from 'vue-router'
import BaseCard from '../components/ui/BaseCard.vue'
</script>

<template>
  <main class="not-found">
    <BaseCard class="status-page">
      <p class="eyebrow">ERREUR 404</p>
      <h1>Page introuvable</h1>
      <p>L’adresse demandée n’existe pas ou a été déplacée.</p>
      <RouterLink class="primary-button" to="/">Retour à l’accueil</RouterLink>
    </BaseCard>
  </main>
</template>

<style scoped>
.not-found { display: grid; min-height: 100vh; place-items: center; padding: 1rem; }
.status-page { display: grid; gap: 0.75rem; max-width: 520px; padding: 1.5rem; }
.status-page .primary-button { justify-self: start; }
</style>
