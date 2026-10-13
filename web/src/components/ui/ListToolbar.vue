<script setup lang="ts">
import { onBeforeUnmount } from 'vue'

withDefaults(defineProps<{ placeholder?: string; sortLabel?: string; loading?: boolean; showSort?: boolean }>(), { loading: false, showSort: true })
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
  <div class="list-toolbar" :aria-busy="loading">
    <input v-model="model" :placeholder="placeholder || 'Rechercher…'" :disabled="loading" aria-label="Rechercher dans la liste" @input="scheduleSearch" @keyup.enter="emit('search')" />
    <button class="secondary-button" type="button" :disabled="loading" @click="emit('search')">{{ loading ? 'Recherche…' : 'Rechercher' }}</button>
    <button v-if="showSort" class="secondary-button" type="button" :disabled="loading" @click="emit('sort')">{{ loading ? 'Traitement…' : (sortLabel || 'Trier') }}</button>
  </div>
</template>
