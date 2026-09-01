<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useSidebarStore } from './sidebarStore'
import { useAuthenticationStore } from '../../stores/authentication/store'
const sidebar = useSidebarStore(); const auth = useAuthenticationStore()
const userRole = computed(() => (auth.userRole || '').toLowerCase())
const canSeeUsers = computed(() => ['admin', 'responsable_gare', 'responsable_cooperative'].includes(userRole.value))
const canSeeGares = computed(() => ['admin', 'responsable_gare', 'agent_gare'].includes(userRole.value))
const canSeeCooperatives = computed(() => ['admin', 'responsable_cooperative'].includes(userRole.value))
const canSeeRoles = computed(() => userRole.value === 'admin')
</script>
<template><div v-if="sidebar.mobileOpen" class="sidebar-backdrop" @click="sidebar.closeMobile" /><aside class="app-sidebar" :class="{ collapsed: sidebar.collapsed, 'mobile-open': sidebar.mobileOpen }"><div class="sidebar-brand"><span class="brand-symbol">C</span><span class="sidebar-name">Coopérative</span><button class="sidebar-toggle" aria-label="Réduire la barre latérale" @click="sidebar.toggle">{{ sidebar.collapsed ? '→' : '←' }}</button></div><div v-if="auth.user" class="sidebar-profile"><span class="profile-initial">{{ auth.user.first_name?.charAt(0) || auth.user.name.charAt(0) }}</span><div class="profile-copy"><strong>{{ auth.user.first_name }} {{ auth.user.name }}</strong><small>{{ auth.user.role.toUpperCase() }}</small></div></div><nav class="sidebar-nav"><span class="sidebar-section">MENU PRINCIPAL</span><RouterLink to="/" class="sidebar-link"><span>⌂</span><b>Vue d’ensemble</b></RouterLink><RouterLink v-if="canSeeUsers" to="/users" class="sidebar-link"><span>♙</span><b>Utilisateurs</b></RouterLink><span v-if="canSeeGares || canSeeCooperatives || canSeeRoles" class="sidebar-section">GESTION</span><RouterLink v-if="canSeeGares" to="/gares" class="sidebar-link"><span>□</span><b>Gares</b></RouterLink><RouterLink v-if="canSeeCooperatives" to="/cooperatives" class="sidebar-link"><span>◉</span><b>Coopératives</b></RouterLink><RouterLink v-if="canSeeRoles" to="/roles" class="sidebar-link"><span>⚿</span><b>Rôles & permissions</b></RouterLink></nav><div class="sidebar-footer"><span class="sidebar-help">?</span><span class="sidebar-name">Centre d’aide</span></div></aside></template>
