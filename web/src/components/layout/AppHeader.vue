<script setup lang="ts">
import { useRouter } from 'vue-router'
import Dropdown from '../ui/Dropdown.vue'
import { useSidebarStore } from './sidebarStore'
import { useAuthenticationStore } from '../../stores/authentication/store'
const sidebar = useSidebarStore(); const auth = useAuthenticationStore(); const router = useRouter()
async function logout() { await auth.logout(); await router.push({ name: 'login' }) }
</script>
<template><header class="app-header"><button class="hamburger" aria-label="Ouvrir le menu" @click="sidebar.openMobile">☰</button><div class="header-heading"><span class="eyebrow">ESPACE ADMINISTRATION</span><h1><slot>Vue d’ensemble</slot></h1></div><div v-if="auth.user" class="header-actions"><button class="notification-button" aria-label="Notifications">♢<i /></button><span class="header-divider" /><Dropdown><template #trigger><span class="user-initials">{{ auth.user.first_name?.charAt(0) || auth.user.name.charAt(0) }}</span><span class="header-user-copy"><strong>{{ auth.user.first_name }} {{ auth.user.name }}</strong><small>{{ auth.user.role.toUpperCase() }}</small></span></template><button class="dropdown-option">Paramètres</button><button class="dropdown-option" @click="logout">Se déconnecter</button></Dropdown></div></header></template>
