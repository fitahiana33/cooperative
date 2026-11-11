<script setup lang="ts">
defineProps<{ progress: number; restored?: boolean; lastSaved?: Date | null; title?: string }>();
</script>

<template>
  <aside class="form-assistant" aria-label="Progression du formulaire">
    <div><strong>{{ title || "Progression" }}</strong><span>{{ Math.round(progress) }} %</span></div>
    <div class="form-progress" role="progressbar" :aria-valuenow="Math.round(progress)" aria-valuemin="0" aria-valuemax="100"><span :style="{ width: `${progress}%` }" /></div>
    <p v-if="restored">Brouillon restauré automatiquement.</p>
    <p v-else-if="lastSaved">Brouillon enregistré à {{ lastSaved.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) }}.</p>
    <p v-else>Les informations sont enregistrées localement pendant la saisie.</p>
  </aside>
</template>

<style scoped>
.form-assistant { margin: 0 0 1rem; padding: .85rem 1rem; border: 1px solid #dbe7dc; border-radius: 10px; background: #f7faf6; }
.form-assistant > div:first-child { display: flex; justify-content: space-between; gap: 1rem; color: var(--ink-strong); font-size: 12px; }.form-assistant p { margin: .45rem 0 0; color: var(--ink-muted); font-size: 11px; }
.form-progress { height: 6px; margin-top: .55rem; overflow: hidden; border-radius: 99px; background: #e5ece4; }.form-progress span { display: block; height: 100%; border-radius: inherit; background: var(--brand); transition: width .2s; }
</style>
