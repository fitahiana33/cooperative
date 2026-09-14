<script setup lang="ts">import BaseCard from './BaseCard.vue'; defineProps<{ label: string; value: string; detail: string; icon: string; tone: string }>()</script>
<template><BaseCard><div class="stat-card"><div class="stat-card-top"><span class="stat-icon" :class="tone">{{ icon }}</span><span class="stat-label">{{ label }}</span></div><strong class="stat-value">{{ value }}</strong><span class="stat-detail">{{ detail }}</span></div></BaseCard></template>

<style scoped>
.stat-card { min-width: 0; }
.stat-card-top { min-width: 0; }
.stat-label { min-width: 0; line-height: 1.3; }
.stat-value { white-space: nowrap; letter-spacing: 0; font-size: clamp(1.35rem, 2vw, 1.8rem); }
.stat-detail { display: block; min-height: 1.25rem; line-height: 1.35; }
@media (max-width: 1100px) and (min-width: 768px) { .stat-card-top { align-items: flex-start; } .stat-label { font-size: 0.75rem; } .stat-value { font-size: 1.35rem; } }
</style>
