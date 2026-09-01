<script setup lang="ts">
defineProps<{ placeholder?: string; sortLabel?: string }>()
const emit = defineEmits<{ search: []; sort: [] }>()
const model = defineModel<string>({ default: '' })
</script>
<template>
  <div class="list-toolbar">
    <input v-model="model" :placeholder="placeholder || 'Rechercher…'" @keyup.enter="emit('search')" />
    <button class="secondary-button" @click="emit('search')">Rechercher</button>
    <button class="secondary-button" @click="emit('sort')">{{ sortLabel || 'Trier' }}</button>
  </div>
</template>
