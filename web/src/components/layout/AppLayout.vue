<script setup lang="ts">import AppSidebar from './AppSidebar.vue'; import AppHeader from './AppHeader.vue'</script>
<template><div class="dashboard-shell"><AppSidebar /><div class="dashboard-main"><AppHeader><slot name="title">Vue d’ensemble</slot></AppHeader><main class="dashboard-content"><slot /></main></div></div></template>
