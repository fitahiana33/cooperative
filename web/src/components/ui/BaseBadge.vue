<script setup lang="ts">withDefaults(defineProps<{ tone?: 'neutral' | 'success' | 'warning' | 'danger' }>(), { tone: 'neutral' })</script>
<template><span class="base-badge" :class="`badge-${tone}`"><slot /></span></template>
