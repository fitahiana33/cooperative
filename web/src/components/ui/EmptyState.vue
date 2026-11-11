<script setup lang="ts">
import AppIcon from "./AppIcon.vue";
defineProps<{ icon: string; title: string; description: string }>();
</script>
<template>
  <div class="empty-state">
    <div class="empty-state-icon"><AppIcon name="search" :size="24" /></div>
    <strong>{{ title }}</strong
    ><span>{{ description }}</span>
  </div>
</template>
