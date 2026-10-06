<script setup lang="ts">
import { onBeforeUnmount } from 'vue'

withDefaults(defineProps<{ placeholder?: string; sortLabel?: string; loading?: boolean }>(), { loading: false })
const emit = defineEmits<{ search: []; sort: [] }>()
const model = defineModel<string>({ default: '' })
let searchTimer: ReturnType<typeof setTimeout> | undefined

function scheduleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => emit('search'), 300)
}

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})
</script>
<template>
  <div class="list-toolbar">
    <input v-model="model" :placeholder="placeholder || 'Rechercher…'" @input="scheduleSearch" @keyup.enter="emit('search')" />
    <button class="secondary-button" type="button" :disabled="loading" @click="emit('search')">Rechercher</button>
    <button class="secondary-button" type="button" :disabled="loading" @click="emit('sort')">{{ sortLabel || 'Trier' }}</button>
  </div>
</template>
