<script setup lang="ts">
import { onMounted, watch } from "vue";

type Density = "compact" | "comfortable";
const props = defineProps<{ storageKey: string; columns?: Array<{ id: string; label: string; locked?: boolean }> }>();
const density = defineModel<Density>("density", { default: "comfortable" });
const visibleColumns = defineModel<string[]>("visibleColumns", { default: () => [] });

onMounted(() => {
  const defaults = (props.columns || []).map((column) => column.id);
  try {
    const saved = JSON.parse(localStorage.getItem(`cooperative:table:${props.storageKey}`) || "null");
    density.value = saved?.density === "compact" ? "compact" : "comfortable";
    visibleColumns.value = Array.isArray(saved?.columns)
      ? defaults.filter((column) => saved.columns.includes(column) || props.columns?.find((item) => item.id === column)?.locked)
      : defaults;
  } catch { visibleColumns.value = defaults; }
});
watch([density, visibleColumns], () => {
  try { localStorage.setItem(`cooperative:table:${props.storageKey}`, JSON.stringify({ density: density.value, columns: visibleColumns.value })); } catch { /* optional preference */ }
}, { deep: true, flush: "sync" });

function toggle(id: string) {
  visibleColumns.value = visibleColumns.value.includes(id)
    ? visibleColumns.value.filter((column) => column !== id)
    : [...visibleColumns.value, id];
}
</script>

<template>
  <div class="table-view-controls">
    <div class="density-switch" role="group" aria-label="Densité du tableau">
      <button type="button" :class="{ active: density === 'comfortable' }" @click="density = 'comfortable'">Confort</button>
      <button type="button" :class="{ active: density === 'compact' }" @click="density = 'compact'">Compact</button>
    </div>
    <details v-if="columns?.length" class="column-picker">
      <summary>Colonnes</summary>
      <div>
        <label v-for="column in columns" :key="column.id">
          <input type="checkbox" :checked="visibleColumns.includes(column.id)" :disabled="column.locked" @change="toggle(column.id)" />
          {{ column.label }}
        </label>
      </div>
    </details>
  </div>
</template>

<style scoped>
.table-view-controls { display: flex; align-items: center; justify-content: flex-end; gap: .55rem; margin: .75rem 0; }
.density-switch { display: inline-flex; padding: 3px; border: 1px solid var(--line); border-radius: 8px; background: #f7f9f7; }
.density-switch button { min-height: 30px; padding: .25rem .55rem; border-radius: 6px; color: var(--ink-muted); background: transparent; font-size: 11px; }
.density-switch button.active { color: var(--brand-dark); background: #fff; box-shadow: 0 1px 3px #17372b14; font-weight: 700; }
.column-picker { position: relative; }.column-picker summary { min-height: 38px; display: flex; align-items: center; padding: .4rem .7rem; border: 1px solid var(--line); border-radius: 8px; color: var(--ink); background: #fff; cursor: pointer; font-size: 11px; font-weight: 700; }
.column-picker > div { position: absolute; z-index: 15; top: calc(100% + 5px); right: 0; display: grid; gap: .35rem; min-width: 190px; padding: .7rem; border: 1px solid var(--line); border-radius: 9px; background: #fff; box-shadow: 0 10px 30px #17372b18; }
.column-picker label { display: flex; align-items: center; gap: .55rem; min-height: 32px; font-size: 11px; }.column-picker input { width: auto; }
@media (max-width: 600px) { .table-view-controls { justify-content: space-between; } }
</style>
