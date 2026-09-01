<script setup lang="ts">import { ref } from 'vue'; const open = ref(false)</script>
<template><div class="dropdown"><button class="dropdown-trigger" @click="open = !open"><slot name="trigger" /><span class="chevron">⌄</span></button><div v-if="open" class="dropdown-menu"><slot /></div></div></template>
