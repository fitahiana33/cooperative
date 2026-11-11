<script setup lang="ts">
import { RouterLink } from "vue-router";
import AppIcon from "../ui/AppIcon.vue";
</script>
<template>
  <main class="auth-shell">
    <aside class="auth-story" aria-label="Coopérative">
      <RouterLink to="/" class="auth-brand"
        ><AppIcon name="route" :size="28" /><span>Coopérative</span></RouterLink
      >
      <div class="auth-story-copy">
        <p>LES ROUTES NOUS RAPPROCHENT</p>
        <h2>
          Un voyage se prépare.<br />Une belle histoire<br /><em>commence.</em>
        </h2>
        <span
          >Retrouvez vos trajets, vos réservations et les personnes qui vous
          accompagnent, dans un seul espace.</span
        >
      </div>
      <img src="/images/highlands.svg" alt="" width="760" height="660" /><small
        >À vos côtés, sur les routes de Madagascar.</small
      >
    </aside>
    <section class="auth-panel">
      <RouterLink to="/" class="auth-back"
        ><AppIcon name="back" :size="16" />Retour aux voyages</RouterLink
      ><RouterLink to="/" class="auth-mobile-brand"
        ><AppIcon name="route" :size="24" />Coopérative</RouterLink
      >
      <div class="auth-card"><slot /></div>
      <p class="auth-policy">
        Vos informations sont utilisées pour gérer votre compte.<br /><RouterLink
          to="/confidentialite"
          >Consulter notre politique de confidentialité</RouterLink
        >
      </p>
    </section>
  </main>
</template>
