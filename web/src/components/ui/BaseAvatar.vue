<script setup lang="ts">defineProps<{ label?: string; size?: 'small' | 'medium' }>()</script>
<template><span class="base-avatar" :class="`avatar-${size || 'medium'}`">{{ label || 'A' }}</span></template>
