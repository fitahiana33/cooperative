<script setup lang="ts">
import { ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  page: number
  pages: number
  total: number
  loading?: boolean
  disabled?: boolean
  itemLabel?: string
}>(), {
  loading: false,
  disabled: false,
  itemLabel: 'résultat(s)',
})

const emit = defineEmits<{ change: [page: number] }>()
const pageInput = ref(String(props.page))

watch(() => props.page, (value) => {
  pageInput.value = String(value)
})

function goTo(page: number) {
  emit('change', page)
}

function handlePageSelect(event: Event) {
  pageInput.value = (event.target as HTMLInputElement).value
}

function commitPage() {
  const candidate = Number.parseInt(pageInput.value, 10)
  const next = Number.isFinite(candidate)
    ? Math.min(Math.max(candidate, 1), props.pages)
    : props.page
  pageInput.value = String(next)
  if (next !== props.page) goTo(next)
}
</script>

<template>
  <nav v-if="pages > 1 || total > 0" class="pagination" aria-label="Pagination">
    <button
      class="secondary-button"
      type="button"
      :disabled="loading || disabled || page <= 1"
      @click="goTo(page - 1)"
    >
      Précédent
    </button>
    <div class="pagination-summary" aria-live="polite">
      <span>Page</span>
      <input
        class="pagination-input"
        type="number"
        inputmode="numeric"
        min="1"
        :max="pages"
        :value="pageInput"
        :disabled="loading || disabled"
        :aria-label="`Numéro de page sur ${pages}`"
        @input="handlePageSelect"
        @change="commitPage"
        @blur="commitPage"
        @keydown.enter.prevent="commitPage"
      />
      <span>/ {{ pages }} · {{ total }} {{ itemLabel }}</span>
    </div>
    <button
      class="secondary-button"
      type="button"
      :disabled="loading || disabled || page >= pages"
      @click="goTo(page + 1)"
    >
      Suivant
    </button>
  </nav>
</template>
