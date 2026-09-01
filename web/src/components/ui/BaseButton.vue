<script setup lang="ts">withDefaults(defineProps<{ variant?: 'primary' | 'ghost' | 'link'; disabled?: boolean }>(), { variant: 'primary' })</script>
<template><button class="base-button" :class="`button-${variant}`" :disabled="disabled"><slot /></button></template>
