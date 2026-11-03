<script setup lang="ts">
import { useRouter } from 'vue-router'
import Dropdown from '../ui/Dropdown.vue'
import { useSidebarStore } from './sidebarStore'
import { useAuthenticationStore } from '../../stores/authentication/store'
const sidebar = useSidebarStore(); const auth = useAuthenticationStore(); const appRouter = useRouter()
const router = { push(location: any) { if (location?.name === 'user-detail' && auth.user?.role?.toLowerCase() === 'passenger') return appRouter.push({ name: 'client-profile' }); return appRouter.push(location) } }
async function logout() { await auth.logout(); await router.push({ name: 'frontoffice' }) }
function openProfile() { void router.push(auth.user?.role?.toLowerCase() === 'passenger' ? { name: 'client-profile' } : { name: 'user-detail', params: { id: auth.user?.id } }) }
</script>
<template><header class="app-header"><button class="hamburger" aria-label="Ouvrir le menu" @click="sidebar.openMobile">☰</button><div class="header-heading"><span class="eyebrow">ESPACE ADMINISTRATION</span><h1><slot>Vue d’ensemble</slot></h1></div><div v-if="auth.user" class="header-actions"><button class="notification-button" aria-label="Notifications" title="Notifications" @click="router.push({ name: 'notifications' })">♢<i /></button><span class="header-divider" /><Dropdown><template #trigger><span class="user-initials">{{ auth.user.first_name?.charAt(0) || auth.user.name.charAt(0) }}</span><span class="header-user-copy"><strong>{{ auth.user.first_name }} {{ auth.user.name }}</strong><small>{{ auth.user.role.toUpperCase() }}</small></span></template><button class="dropdown-option" @click="router.push({ name: 'user-detail', params: { id: auth.user.id } })">Mon profil</button><button class="dropdown-option" @click="logout">Se déconnecter</button></Dropdown></div></header></template>
