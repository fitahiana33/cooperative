<script setup lang="ts">
defineProps<{ open: boolean; title: string; confirmLabel: string; busy?: boolean; danger?: boolean }>();
defineEmits<{ confirm: []; cancel: [] }>();
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="sensitive-overlay" role="presentation" @mousedown.self="$emit('cancel')">
      <section class="sensitive-dialog" role="alertdialog" aria-modal="true" :aria-label="title">
        <p class="eyebrow">ACTION SENSIBLE</p><h2>{{ title }}</h2>
        <div class="sensitive-content"><slot /></div>
        <div class="sensitive-actions">
          <button class="secondary-button" type="button" :disabled="busy" @click="$emit('cancel')">Revenir</button>
          <button :class="danger ? 'danger-button' : 'primary-button'" type="button" :disabled="busy" @click="$emit('confirm')">{{ busy ? "Traitement…" : confirmLabel }}</button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.sensitive-overlay { position: fixed; inset: 0; z-index: 100; display: grid; place-items: center; padding: 1rem; background: #10251fc2; backdrop-filter: blur(3px); }
.sensitive-dialog { width: min(500px, 100%); padding: 1.35rem; border-radius: 14px; background: #fff; box-shadow: 0 24px 70px #0004; }.sensitive-dialog h2 { margin: .25rem 0 .8rem; color: var(--ink-strong); font: 750 1.25rem var(--font-heading); }.sensitive-content { color: var(--ink); font-size: 13px; }.sensitive-actions { display: flex; justify-content: flex-end; gap: .65rem; margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid var(--line); }
.sensitive-actions button { min-height: 42px; padding: .6rem .9rem; border: 1px solid var(--line); border-radius: 8px; font: 700 12px var(--font-body); }.sensitive-actions .secondary-button { color: var(--ink); background: #fff; }.sensitive-actions .primary-button { color: #fff; border-color: var(--brand); background: var(--brand); }.sensitive-actions .danger-button { color: #a04435; border-color: #edcfc6; background: #fff0ed; }
@media (max-width: 520px) { .sensitive-overlay { align-items: end; padding: 0; }.sensitive-dialog { border-radius: 16px 16px 0 0; padding-bottom: calc(1.2rem + env(safe-area-inset-bottom)); }.sensitive-actions > * { flex: 1; } }
</style>
