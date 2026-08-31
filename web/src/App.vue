<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header class="topbar"><h1>Coopérative</h1><nav><RouterLink to="/">Tableau de bord</RouterLink><RouterLink to="/users">Utilisateurs</RouterLink></nav></header>
  <main class="container"><RouterView /></main>
</template>

