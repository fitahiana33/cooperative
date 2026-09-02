<script setup lang="ts">
import { computed, reactive } from 'vue'
import { RouterLink } from 'vue-router'
import { useSidebarStore } from './sidebarStore'
import { useAuthenticationStore } from '../../stores/authentication/store'

type SidebarSection = 'principal' | 'administration' | 'stations' | 'fleet'

const sidebar = useSidebarStore()
const auth = useAuthenticationStore()

const userRole = computed(() => (auth.userRole || '').toLowerCase())
const canSeeUsers = computed(() => ['admin', 'responsable_gare', 'responsable_cooperative'].includes(userRole.value))
const canSeeGares = computed(() => ['admin', 'responsable_gare', 'agent_gare'].includes(userRole.value))
const canSeeCooperatives = computed(() => ['admin', 'responsable_cooperative'].includes(userRole.value))
const canSeeRoles = computed(() => userRole.value === 'admin')
const canSeeVehicles = computed(() => ['admin', 'responsable_cooperative', 'chauffeur'].includes(userRole.value))
const canSeeChauffeurs = computed(() => ['admin', 'responsable_cooperative'].includes(userRole.value))
const canSeeFleetCatalog = computed(() => ['admin', 'responsable_cooperative'].includes(userRole.value))

const openSections = reactive<Record<SidebarSection, boolean>>({
  principal: true,
  administration: true,
  stations: true,
  fleet: true,
})

function toggleSection(section: SidebarSection) {
  openSections[section] = !openSections[section]
}

function isSectionOpen(section: SidebarSection) {
  return openSections[section]
}
</script>

<template>
  <div v-if="sidebar.mobileOpen" class="sidebar-backdrop" @click="sidebar.closeMobile" />
  <aside class="app-sidebar" :class="{ collapsed: sidebar.collapsed, 'mobile-open': sidebar.mobileOpen }">
    <div class="sidebar-brand">
      <span class="brand-symbol">C</span>
      <span class="sidebar-name">Coopérative</span>
      <button class="sidebar-toggle" aria-label="Réduire la barre latérale" @click="sidebar.toggle">
        {{ sidebar.collapsed ? '→' : '←' }}
      </button>
    </div>

    <div v-if="auth.user" class="sidebar-profile">
      <span class="profile-initial">{{ auth.user.first_name?.charAt(0) || auth.user.name.charAt(0) }}</span>
      <div class="profile-copy">
        <strong>{{ auth.user.first_name }} {{ auth.user.name }}</strong>
        <small>{{ auth.user.role.toUpperCase() }}</small>
      </div>
    </div>

    <nav class="sidebar-nav">
      <div class="sidebar-group">
        <button class="sidebar-section" type="button" :aria-expanded="isSectionOpen('principal')" @click="toggleSection('principal')">
          <span>PRINCIPAL</span><b>{{ isSectionOpen('principal') ? '⌃' : '⌄' }}</b>
        </button>
        <div v-if="isSectionOpen('principal')" class="sidebar-submenu">
          <RouterLink to="/" class="sidebar-link" @click="sidebar.closeMobile"><span>⌂</span><b>Vue d’ensemble</b></RouterLink>
        </div>
      </div>

      <div v-if="canSeeUsers || canSeeRoles" class="sidebar-group">
        <button class="sidebar-section" type="button" :aria-expanded="isSectionOpen('administration')" @click="toggleSection('administration')">
          <span>ADMINISTRATION</span><b>{{ isSectionOpen('administration') ? '⌃' : '⌄' }}</b>
        </button>
        <div v-if="isSectionOpen('administration')" class="sidebar-submenu">
          <RouterLink v-if="canSeeUsers" to="/users" class="sidebar-link" @click="sidebar.closeMobile"><span>♙</span><b>Utilisateurs</b></RouterLink>
          <RouterLink v-if="canSeeRoles" to="/roles" class="sidebar-link" @click="sidebar.closeMobile"><span>⚿</span><b>Rôles & permissions</b></RouterLink>
        </div>
      </div>

      <div v-if="canSeeGares || canSeeCooperatives" class="sidebar-group">
        <button class="sidebar-section" type="button" :aria-expanded="isSectionOpen('stations')" @click="toggleSection('stations')">
          <span>GARES & COOPÉRATIVES</span><b>{{ isSectionOpen('stations') ? '⌃' : '⌄' }}</b>
        </button>
        <div v-if="isSectionOpen('stations')" class="sidebar-submenu">
          <RouterLink v-if="canSeeGares" to="/gares" class="sidebar-link" @click="sidebar.closeMobile"><span>□</span><b>Gares</b></RouterLink>
          <RouterLink v-if="canSeeCooperatives" to="/cooperatives" class="sidebar-link" @click="sidebar.closeMobile"><span>◉</span><b>Coopératives</b></RouterLink>
        </div>
      </div>

      <div v-if="canSeeVehicles || canSeeChauffeurs || canSeeFleetCatalog" class="sidebar-group">
        <button class="sidebar-section" type="button" :aria-expanded="isSectionOpen('fleet')" @click="toggleSection('fleet')">
          <span>FLOTTE</span><b>{{ isSectionOpen('fleet') ? '⌃' : '⌄' }}</b>
        </button>
        <div v-if="isSectionOpen('fleet')" class="sidebar-submenu">
          <RouterLink v-if="canSeeVehicles" to="/vehicules" class="sidebar-link" @click="sidebar.closeMobile"><span>🚐</span><b>Véhicules</b></RouterLink>
          <RouterLink v-if="canSeeChauffeurs" to="/chauffeurs" class="sidebar-link" @click="sidebar.closeMobile"><span>🪪</span><b>Chauffeurs</b></RouterLink>
          <RouterLink v-if="canSeeFleetCatalog" to="/marques" class="sidebar-link" @click="sidebar.closeMobile"><span>©</span><b>Marques</b></RouterLink>
          <RouterLink v-if="canSeeFleetCatalog" to="/modeles" class="sidebar-link" @click="sidebar.closeMobile"><span>▤</span><b>Modèles</b></RouterLink>
        </div>
      </div>
    </nav>

    <div class="sidebar-footer">
      <span class="sidebar-help">?</span>
      <span class="sidebar-name">Centre d’aide</span>
    </div>
  </aside>
</template>
