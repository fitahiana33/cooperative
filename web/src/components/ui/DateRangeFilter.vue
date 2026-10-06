<script setup lang="ts">
const props = withDefaults(defineProps<{ start?: string; end?: string; compact?: boolean }>(), { start: '', end: '', compact: true })
const emit = defineEmits<{ 'update:start': [value: string]; 'update:end': [value: string]; apply: []; clear: [] }>()
</script>

<template>
  <div class="date-range-filter" :class="{ compact }">
    <label>
      <span>Du</span>
      <input :value="props.start" type="date" aria-label="Date de début" @input="emit('update:start', ($event.target as HTMLInputElement).value)" />
    </label>
    <span class="date-range-separator" aria-hidden="true">→</span>
    <label>
      <span>Au</span>
      <input :value="props.end" type="date" :min="props.start || undefined" aria-label="Date de fin" @input="emit('update:end', ($event.target as HTMLInputElement).value)" />
    </label>
    <button class="secondary-button compact-button" type="button" @click="emit('apply')">Appliquer</button>
    <button v-if="props.start || props.end" class="text-button" type="button" @click="emit('clear')">Effacer</button>
  </div>
</template>

<style scoped>
.date-range-filter { display: flex; align-items: end; gap: .55rem; flex-wrap: wrap; margin-top: .75rem; }
.date-range-filter label { display: inline-flex; align-items: center; gap: .4rem; color: #64748b; font-size: .78rem; font-weight: 600; }
.date-range-filter input { width: 9.5rem; min-height: 2.35rem; padding: .4rem .55rem; border: 1px solid #dbe3ef; border-radius: 8px; background: #fff; color: #1e293b; }
.date-range-separator { padding-bottom: .55rem; color: #94a3b8; }
.text-button { border: 0; padding: .5rem .25rem; background: transparent; color: #2563eb; cursor: pointer; }
@media (max-width: 700px) { .date-range-filter { align-items: stretch; } .date-range-filter label { flex: 1 1 10rem; flex-direction: column; align-items: stretch; } .date-range-filter input { width: 100%; } .date-range-separator { display: none; } }
</style>
