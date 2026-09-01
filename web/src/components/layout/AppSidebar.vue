<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useSidebarStore } from './sidebarStore'
import { useAuthenticationStore } from '../../stores/authentication/store'
const sidebar = useSidebarStore()
const auth = useAuthenticationStore()
</script>

<template>
  <div v-if="sidebar.mobileOpen" class="sidebar-backdrop" @click="sidebar.closeMobile" />
  <aside class="app-sidebar" :class="{ collapsed: sidebar.collapsed, 'mobile-open': sidebar.mobileOpen }">
    <div class="sidebar-brand"><span class="brand-symbol">C</span><span class="sidebar-name">Coopérative</span><button class="sidebar-toggle" aria-label="Réduire la barre latérale" @click="sidebar.toggle">{{ sidebar.collapsed ? '→' : '←' }}</button></div>
    <div class="sidebar-profile"><span class="profile-initial">{{ auth.user?.first_name?.charAt(0) || 'A' }}</span><div class="profile-copy"><strong>{{ auth.user?.first_name || 'Administrateur' }}</strong><small>Administrateur</small></div><span class="profile-chevron">⌄</span></div>
    <nav class="sidebar-nav"><span class="sidebar-section">MENU PRINCIPAL</span><RouterLink to="/" class="sidebar-link" title="Vue d’ensemble"><span>⌂</span><b>Vue d’ensemble</b></RouterLink><RouterLink to="/users" class="sidebar-link" title="Utilisateurs"><span>♙</span><b>Utilisateurs</b></RouterLink><span class="sidebar-section">GESTION</span><button v-for="item in ['Coopératives','Départs','Réservations']" :key="item" class="sidebar-link disabled" :title="item"><span>◫</span><b>{{ item }}</b><em>Bientôt</em></button></nav>
    <div class="sidebar-footer"><span class="sidebar-help">?</span><span class="sidebar-name">Centre d’aide</span></div>
  </aside>
</template>
