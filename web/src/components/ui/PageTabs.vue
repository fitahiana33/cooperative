<script setup lang="ts">
export interface PageTab {
  id: string
  label: string
  count?: number
}

defineProps<{
  tabs: PageTab[]
  modelValue: string
  ariaLabel?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <nav class="page-tabs" role="tablist" :aria-label="ariaLabel || 'Sections de la page'">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      class="page-tab"
      :class="{ active: modelValue === tab.id }"
      type="button"
      role="tab"
      :aria-selected="modelValue === tab.id"
      :tabindex="modelValue === tab.id ? 0 : -1"
      @click="emit('update:modelValue', tab.id)"
    >
      {{ tab.label }}<span v-if="tab.count !== undefined" class="page-tab-count">{{ tab.count }}</span>
    </button>
  </nav>
</template>
