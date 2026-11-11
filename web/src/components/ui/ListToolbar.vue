<script setup lang="ts">
import { onBeforeUnmount, watch } from "vue";
import AppIcon from "./AppIcon.vue";

const props = withDefaults(
  defineProps<{
    placeholder?: string;
    sortLabel?: string;
    loading?: boolean;
    showSort?: boolean;
  }>(),
  { loading: false, showSort: true },
);
const emit = defineEmits<{ search: []; sort: [] }>();
const model = defineModel<string>({ default: "" });
let searchTimer: ReturnType<typeof setTimeout> | undefined;
let pendingSearch = false;
function performSearch() {
  if (searchTimer) clearTimeout(searchTimer);
  if (props.loading) {
    pendingSearch = true;
    return;
  }
  pendingSearch = false;
  emit("search");
}
watch(
  () => props.loading,
  (loading) => {
    if (!loading && pendingSearch) performSearch();
  },
);

function scheduleSearch() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(performSearch, 300);
}

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer);
});
</script>
<template>
  <div class="list-toolbar" :aria-busy="loading">
    <label class="toolbar-search"
      ><AppIcon name="search" :size="18" /><input
        v-model="model"
        type="search"
        :placeholder="placeholder || 'Rechercher…'"
        aria-label="Rechercher dans la liste"
        @input="scheduleSearch"
        @keyup.enter="performSearch"
    /></label>
    <button
      class="secondary-button"
      type="button"
      :disabled="loading"
      @click="performSearch"
    >
      {{ loading ? "Recherche…" : "Rechercher" }}
    </button>
    <button
      v-if="showSort"
      class="secondary-button"
      type="button"
      :disabled="loading"
      @click="emit('sort')"
    >
      {{ loading ? "Traitement…" : sortLabel || "Trier" }}
    </button>
  </div>
</template>
