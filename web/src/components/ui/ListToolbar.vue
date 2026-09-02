<script setup lang="ts">
withDefaults(defineProps<{ placeholder?: string; sortLabel?: string; loading?: boolean }>(), { loading: false })
const emit = defineEmits<{ search: []; sort: [] }>()
const model = defineModel<string>({ default: '' })
</script>
<template>
  <div class="list-toolbar">
    <input v-model="model" :placeholder="placeholder || 'Rechercher…'" @keyup.enter="emit('search')" />
    <button class="secondary-button" type="button" :disabled="loading" @click="emit('search')">Rechercher</button>
    <button class="secondary-button" type="button" :disabled="loading" @click="emit('sort')">{{ sortLabel || 'Trier' }}</button>
  </div>
</template>
