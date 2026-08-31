<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '../stores/userStore'
const store = useUserStore()
onMounted(() => store.fetchAll())
</script>
<template><section><p class="eyebrow">Administration</p><h2>Utilisateurs</h2><p v-if="store.loading">Chargement…</p><p v-else-if="store.error" class="error">{{ store.error }}</p><table v-else><thead><tr><th>Nom</th><th>Email</th><th>Statut</th></tr></thead><tbody><tr v-for="user in store.items" :key="user.id"><td>{{ user.full_name }}</td><td>{{ user.email }}</td><td>{{ user.is_active ? 'Actif' : 'Inactif' }}</td></tr></tbody></table></section></template>

