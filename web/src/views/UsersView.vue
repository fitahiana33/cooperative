<script setup lang="ts">
import { onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import BaseCard from '../components/ui/BaseCard.vue'
import ListToolbar from '../components/ui/ListToolbar.vue'
import { useUserStore } from '../stores/user/store'
const store = useUserStore()
onMounted(() => store.fetchAll())
</script>

<template>
  <AppLayout><template #title>Utilisateurs</template>
    <BaseCard>
      <div class="card-heading"><div><h1>Utilisateurs</h1><p>Comptes et accès à la plateforme.</p></div></div>
      <ListToolbar v-model="store.search" placeholder="Rechercher par nom ou email" sort-label="Trier par nom" @search="store.fetchAll(1)" @sort="store.setSort('name')" />
      <p v-if="store.loading" class="status-msg">Chargement des utilisateurs…</p>
      <p v-else-if="store.error" class="error-banner">{{ store.error }}</p>
      <p v-else-if="store.success" class="success-banner">{{ store.success }}</p>
      <table v-else class="data-table"><caption>Liste des utilisateurs</caption><thead><tr><th><button class="sort-button" @click="store.setSort('name')">Nom ↕</button></th><th><button class="sort-button" @click="store.setSort('email')">Email ↕</button></th><th><button class="sort-button" @click="store.setSort('is_active')">Statut ↕</button></th></tr></thead><tbody><tr v-for="user in store.items" :key="user.id"><td>{{ user.first_name }} {{ user.name }}</td><td>{{ user.email }}</td><td>{{ user.is_active ? 'Actif' : 'Inactif' }}</td></tr><tr v-if="!store.items.length"><td colspan="3">Aucun utilisateur trouvé.</td></tr></tbody></table>
      <div v-if="!store.loading && !store.error" class="pagination"><button class="table-action" :disabled="store.page <= 1" @click="store.fetchAll(store.page - 1)">Précédent</button><span>Page {{ store.page }} / {{ store.pages || 1 }} ({{ store.total }} utilisateurs)</span><button class="table-action" :disabled="store.page >= store.pages" @click="store.fetchAll(store.page + 1)">Suivant</button></div>
    </BaseCard>
  </AppLayout>
</template>
