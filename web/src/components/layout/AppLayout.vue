<script setup lang="ts">
import { watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'

const route = useRoute()
const titles: Record<string, string> = {
  home: 'Tableau de bord', users: 'Utilisateurs', 'user-create': 'Ajouter un utilisateur', 'user-edit': 'Modifier un utilisateur',
  gares: 'Gares', 'gare-create': 'Ajouter une gare', 'gare-edit': 'Modifier une gare',
  cooperatives: 'Coopératives', 'cooperative-create': 'Ajouter une coopérative', 'cooperative-edit': 'Modifier une coopérative',
  roles: 'Rôles & permissions', vehicules: 'Véhicules', 'vehicule-create': 'Ajouter un véhicule', 'vehicule-edit': 'Modifier un véhicule', 'vehicule-detail': 'Détail du véhicule',
  chauffeurs: 'Chauffeurs', 'chauffeur-create': 'Ajouter un chauffeur', 'chauffeur-edit': 'Modifier un chauffeur', 'chauffeur-detail': 'Détail du chauffeur',
  marques: 'Marques', 'marque-create': 'Ajouter une marque', 'marque-edit': 'Modifier une marque', 'marque-detail': 'Détail de la marque',
  modeles: 'Modèles', 'modele-create': 'Ajouter un modèle', 'modele-edit': 'Modifier un modèle', 'modele-detail': 'Détail du modèle',
}

watchEffect(() => { document.title = `${titles[String(route.name)] || 'Coopérative'} | Gestion` })
</script>
<template><div class="dashboard-shell"><AppSidebar /><div class="dashboard-main"><AppHeader><slot name="title">Vue d’ensemble</slot></AppHeader><main class="dashboard-content"><slot /></main></div></div></template>
