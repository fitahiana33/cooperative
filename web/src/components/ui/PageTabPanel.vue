<script setup lang="ts">
defineProps<{ prefix: string; name: string; active: boolean }>();
</script>

<template>
  <section
    v-show="active"
    :id="`${prefix}-panel-${name}`"
    class="page-tab-panel"
    role="tabpanel"
    :aria-labelledby="`${prefix}-tab-${name}`"
    tabindex="0"
  >
    <slot />
  </section>
</template>
