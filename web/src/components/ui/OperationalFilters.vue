<script setup lang="ts">
import { ref } from "vue";
import AppIcon from "./AppIcon.vue";

const props = withDefaults(
  defineProps<{
    activeCount?: number;
    loading?: boolean;
    title?: string;
    description?: string;
    open?: boolean;
  }>(),
  {
    activeCount: 0,
    loading: false,
    title: "Filtres avancés",
    description: "Affinez la liste selon votre besoin opérationnel.",
    open: true,
  },
);

const emit = defineEmits<{ apply: []; reset: [] }>();
const expanded = ref(props.open);
</script>

<template>
  <section class="operational-filters" aria-label="Filtres avancés">
    <button
      class="operational-filters__toggle"
      type="button"
      :aria-expanded="expanded"
      @click="expanded = !expanded"
    >
      <span class="operational-filters__icon"><AppIcon name="filter" :size="17" /></span>
      <span>
        <strong>{{ title }}</strong>
        <small>{{ description }}</small>
      </span>
      <span v-if="activeCount" class="filter-count">{{ activeCount }} actif{{ activeCount > 1 ? "s" : "" }}</span>
      <AppIcon name="down" :size="16" :class="{ rotated: expanded }" />
    </button>
    <form v-show="expanded" class="operational-filters__body" @submit.prevent="emit('apply')">
      <div class="operational-filter-grid"><slot /></div>
      <div class="operational-filter-actions">
        <slot name="summary" />
        <button class="text-button" type="button" :disabled="loading || !activeCount" @click="emit('reset')">
          Réinitialiser
        </button>
        <button class="primary-button compact-button" type="submit" :disabled="loading">
          {{ loading ? "Application…" : "Appliquer les filtres" }}
        </button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.operational-filters {
  margin: 1rem 0 1.25rem;
  overflow: visible;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #f8faf8;
}
.operational-filters__toggle {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  min-height: 60px;
  padding: 0.75rem 1rem;
  color: var(--ink);
  text-align: left;
  background: transparent;
  border: 0;
}
.operational-filters__toggle > span:nth-child(2) { display: grid; gap: 0.1rem; }
.operational-filters__toggle strong { font-size: 0.9rem; }
.operational-filters__toggle small { color: var(--ink-muted); font-size: 0.75rem; font-weight: 400; }
.operational-filters__icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  color: var(--brand-dark);
  border-radius: 9px;
  background: var(--brand-soft);
}
.filter-count {
  padding: 0.25rem 0.55rem;
  color: var(--brand-dark);
  border-radius: 99px;
  background: #e5efe4;
  font-size: 0.72rem;
  font-weight: 800;
  white-space: nowrap;
}
.rotated { transform: rotate(180deg); }
.operational-filters__body { padding: 1rem; border-top: 1px solid var(--line); }
.operational-filter-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(150px, 1fr));
  gap: 0.85rem;
}
.operational-filter-grid :deep(.form-field) { display: grid; gap: 0.35rem; min-width: 0; }
.operational-filter-grid :deep(.form-field > span) { color: var(--ink-muted); font-size: 0.75rem; font-weight: 700; }
.operational-filter-grid :deep(input),
.operational-filter-grid :deep(select) { width: 100%; min-width: 0; min-height: 42px; }
.operational-filter-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.7rem;
  margin-top: 1rem;
  padding-top: 0.9rem;
  border-top: 1px solid var(--line);
}
.operational-filter-actions :deep(.filter-summary) { margin-right: auto; color: var(--ink-muted); font-size: 0.78rem; }
@media (max-width: 1100px) { .operational-filter-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) {
  .operational-filter-grid { grid-template-columns: 1fr; }
  .operational-filters__toggle { grid-template-columns: auto minmax(0, 1fr) auto; }
  .operational-filters__toggle > .filter-count { display: none; }
  .operational-filter-actions { display: grid; grid-template-columns: 1fr 1fr; }
  .operational-filter-actions :deep(.filter-summary) { grid-column: 1 / -1; }
}
</style>
