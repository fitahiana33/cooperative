<script setup lang="ts">defineProps<{ icon: string; title: string; description: string }>()</script>
<template><div class="empty-state"><div class="empty-state-icon">{{ icon }}</div><strong>{{ title }}</strong><span>{{ description }}</span></div></template>
