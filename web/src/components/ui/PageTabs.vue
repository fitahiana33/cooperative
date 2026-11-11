<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
export interface PageTab {
  id: string;
  label: string;
  count?: number;
}

const props = defineProps<{
  tabs: PageTab[];
  modelValue: string;
  ariaLabel?: string;
  panelPrefix?: string;
}>();
const navigation = ref<HTMLElement>();
watch(
  () => props.modelValue,
  async () => {
    await nextTick();
    const nav = navigation.value;
    const selected = nav?.querySelector<HTMLElement>('[aria-selected="true"]');
    if (!nav || !selected) return;
    const item = selected.getBoundingClientRect();
    const bounds = nav.getBoundingClientRect();
    if (item.left < bounds.left) nav.scrollLeft -= bounds.left - item.left;
    else if (item.right > bounds.right)
      nav.scrollLeft += item.right - bounds.right;
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();
function moveFocus(event: KeyboardEvent) {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  const buttons = Array.from(
    (event.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>(
      '[role="tab"]',
    ),
  );
  const index = buttons.indexOf(event.target as HTMLButtonElement);
  if (index < 0 || !buttons.length) return;
  const next =
    event.key === "Home"
      ? 0
      : event.key === "End"
        ? buttons.length - 1
        : (index + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) %
          buttons.length;
  event.preventDefault();
  buttons[next]?.click();
  buttons[next]?.focus();
}
</script>

<template>
  <nav
    ref="navigation"
    class="page-tabs"
    role="tablist"
    :aria-label="ariaLabel || 'Sections de la page'"
    @keydown="moveFocus"
  >
    <button
      v-for="tab in tabs"
      :key="tab.id"
      class="page-tab"
      :class="{ active: modelValue === tab.id }"
      type="button"
      role="tab"
      :id="panelPrefix ? `${panelPrefix}-tab-${tab.id}` : undefined"
      :aria-controls="
        panelPrefix ? `${panelPrefix}-panel-${tab.id}` : undefined
      "
      :aria-selected="modelValue === tab.id"
      :tabindex="modelValue === tab.id ? 0 : -1"
      @click="emit('update:modelValue', tab.id)"
    >
      {{ tab.label
      }}<span v-if="tab.count !== undefined" class="page-tab-count">{{
        tab.count
      }}</span>
    </button>
  </nav>
</template>
