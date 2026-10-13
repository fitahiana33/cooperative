<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../components/layout/AppLayout.vue'
import BaseCard from '../components/ui/BaseCard.vue'

const route = useRoute()
const target = computed(() => String(route.query.from || ''))
</script>

<template>
  <AppLayout>
    <template #title>Accès refusé</template>
    <BaseCard class="status-page">
      <p class="eyebrow">ERREUR 403</p>
      <h2>Vous n’avez pas accès à cette page</h2>
      <p>
        Votre rôle ne permet pas d’ouvrir <code v-if="target">{{ target }}</code><span v-else>cette page</span>.
        Si vous pensez qu’il s’agit d’une erreur, demandez à un administrateur de vérifier vos permissions.
      </p>
      <RouterLink class="primary-button" to="/">Retour au tableau de bord</RouterLink>
    </BaseCard>
  </AppLayout>
</template>

<style scoped>
.status-page { display: grid; gap: 0.75rem; max-width: 640px; padding: 1.5rem; }
.status-page .primary-button { justify-self: start; }
</style>
