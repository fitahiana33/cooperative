<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{ modelValue: string | number; max?: number; label?: string }>(),
  { max: 10, label: "Passagers" },
);
const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const value = computed(() =>
  Math.min(props.max, Math.max(1, Number(props.modelValue) || 1)),
);
function set(next: number) {
  emit("update:modelValue", String(Math.min(props.max, Math.max(1, next))));
}
</script>

<template>
  <div class="passenger-stepper" role="group" :aria-label="label">
    <button
      type="button"
      :disabled="value <= 1"
      :aria-label="`Retirer un passager (minimum 1)`"
      @click="set(value - 1)"
    >
      −
    </button>
    <output aria-live="polite">
      <strong>{{ value }}</strong>
      <small>{{ value === 1 ? "passager" : "passagers" }}</small>
    </output>
    <button
      type="button"
      :disabled="value >= max"
      :aria-label="`Ajouter un passager (maximum ${max})`"
      @click="set(value + 1)"
    >
      +
    </button>
  </div>
</template>

<style scoped>
.passenger-stepper { align-items: center; border: 1px solid var(--border, #ced9d2); border-radius: 10px; display: inline-flex; min-height: 48px; overflow: hidden; width: 100%; }
.passenger-stepper button { background: transparent; border: 0; color: var(--primary, #166653); cursor: pointer; font-size: 1.35rem; font-weight: 700; height: 46px; min-width: 46px; }
.passenger-stepper button:hover:not(:disabled) { background: #edf7f1; }
.passenger-stepper button:disabled { color: #9aa9a0; cursor: not-allowed; }
.passenger-stepper output { align-items: center; display: flex; flex: 1; flex-direction: column; line-height: 1.1; min-width: 0; text-align: center; }
.passenger-stepper output strong { font-size: 1rem; }
.passenger-stepper output small { color: var(--text-muted, #637267); font-size: .72rem; margin-top: 2px; }
</style>
