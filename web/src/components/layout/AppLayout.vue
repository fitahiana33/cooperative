<script setup lang="ts">
import { computed, watchEffect } from "vue";
import { RouterLink, useRoute } from "vue-router";
import AppIcon from "../ui/AppIcon.vue";
import { navigation } from "./navigation";
import { useSidebarStore } from "./sidebarStore";
import AppSidebar from "./AppSidebar.vue";
import AppHeader from "./AppHeader.vue";

const route = useRoute();
const sidebar = useSidebarStore();
const titles: Record<string, string> = {
  home: "Tableau de bord",
  profile: "Mon profil",
  forbidden: "Accès refusé",
  users: "Utilisateurs",
  "user-create": "Ajouter un utilisateur",
  "user-edit": "Modifier un utilisateur",
  gares: "Gares",
  "gare-create": "Ajouter une gare",
  "gare-edit": "Modifier une gare",
  cooperatives: "Coopératives",
  "cooperative-create": "Ajouter une coopérative",
  "cooperative-edit": "Modifier une coopérative",
  roles: "Rôles & permissions",
  vehicules: "Véhicules",
  "vehicule-create": "Ajouter un véhicule",
  "vehicule-edit": "Modifier un véhicule",
  "vehicule-detail": "Détail du véhicule",
  chauffeurs: "Chauffeurs",
  "chauffeur-create": "Ajouter un chauffeur",
  "chauffeur-edit": "Modifier un chauffeur",
  "chauffeur-detail": "Détail du chauffeur",
  marques: "Marques",
  "marque-create": "Ajouter une marque",
  "marque-edit": "Modifier une marque",
  "marque-detail": "Détail de la marque",
  modeles: "Modèles",
  "modele-create": "Ajouter un modèle",
  "modele-edit": "Modifier un modèle",
  "modele-detail": "Détail du modèle",
};

const section = computed(() =>
  navigation
    .flatMap((group) => group.items)
    .find(
      (item) =>
        route.path === item.to ||
        (item.to !== "/backoffice" && route.path.startsWith(item.to + "/")),
    ),
);
const pageTitle = computed(
  () =>
    titles[String(route.name)] ||
    (String(route.name).endsWith("-create")
      ? "Ajouter"
      : String(route.name).endsWith("-edit")
        ? "Modifier"
        : String(route.name).endsWith("-detail")
          ? "Détails"
          : section.value?.label) ||
    "Espace de gestion",
);
watchEffect(() => {
  document.title = `${pageTitle.value} | Coopérative`;
});
</script>
<template>
  <div class="dashboard-shell">
    <a class="skip-link" href="#workspace-content">Aller au contenu</a
    ><AppSidebar />
    <div class="dashboard-main" :inert="sidebar.mobileOpen || undefined">
      <AppHeader><slot name="title">Vue d’ensemble</slot></AppHeader>
      <main id="workspace-content" class="dashboard-content" tabindex="-1">
        <nav
          v-if="route.name !== 'home'"
          class="workspace-breadcrumb"
          aria-label="Fil d’Ariane"
        >
          <RouterLink to="/backoffice"
            ><AppIcon name="grid" :size="14" /><span class="sr-only"
              >Tableau de bord</span
            ></RouterLink
          ><AppIcon name="chevron" :size="12" /><RouterLink
            v-if="section && section.to !== route.path"
            :to="section.to"
            >{{ section.label }}</RouterLink
          ><AppIcon
            v-if="section && section.to !== route.path"
            name="chevron"
            :size="12"
          /><span aria-current="page">{{ pageTitle }}</span>
        </nav>
        <slot />
        <footer class="workspace-footer">
          <span>Coopérative · Espace de gestion</span
          ><span>Gares, voyages et coopératives</span>
        </footer>
      </main>
    </div>
  </div>
</template>
