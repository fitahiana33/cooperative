<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import UserAvatar from "../ui/UserAvatar.vue";
import AppIcon from "../ui/AppIcon.vue";
import { useAuthenticationStore } from "../../stores/authentication/store";
const auth = useAuthenticationStore();
const route = useRoute();
const router = useRouter();
const open = ref(false);
const isPassenger = computed(() => {
  const roles = [
    auth.user?.role,
    ...(auth.user?.roles || []).map((role) => role.libelle),
  ].map((role) => role?.toLowerCase());
  return (
    roles.some((role) => role === "passenger" || role === "passager") &&
    !roles.some((role) =>
      [
        "admin",
        "responsable_gare",
        "agent_gare",
        "responsable_cooperative",
        "chauffeur",
      ].includes(role || ""),
    )
  );
});
const space = computed(() =>
  isPassenger.value ? "/espace-client" : "/backoffice",
);
watch(
  () => route.fullPath,
  () => {
    open.value = false;
  },
);
async function logout() {
  await auth.logout();
  await router.push("/");
}
</script>
<template>
  <header class="public-header" @keydown.esc="open = false">
    <div class="public-header-inner">
      <RouterLink to="/" class="public-brand" aria-label="Coopérative, accueil"
        ><span class="public-brand-symbol"
          ><AppIcon name="route" :size="25" /></span
        ><strong
          >Coopérative<small>VOTRE VOYAGE À MADAGASCAR</small></strong
        ></RouterLink
      >
      <nav class="public-desktop-nav" aria-label="Navigation principale">
        <RouterLink to="/recherche">Trouver un voyage</RouterLink
        ><RouterLink to="/ma-reservation">Ma réservation</RouterLink
        ><RouterLink to="/conditions-voyage">Guide du voyage</RouterLink>
      </nav>
      <RouterLink
        class="public-account"
        :to="auth.isAuthenticated ? space : '/login'"
        ><UserAvatar v-if="auth.user" :user="auth.user" :size="30" /><AppIcon
          v-else
          name="user"
          :size="17"
        /><span>{{
          auth.isAuthenticated ? "Mon espace" : "Se connecter"
        }}</span></RouterLink
      >
      <button
        class="public-menu-button"
        type="button"
        aria-controls="public-mobile-menu"
        :aria-expanded="open"
        :aria-label="open ? 'Fermer le menu' : 'Ouvrir le menu'"
        @click="open = !open"
      >
        <AppIcon :name="open ? 'close' : 'menu'" />
      </button>
    </div>
    <nav
      v-if="open"
      id="public-mobile-menu"
      class="public-mobile-menu"
      aria-label="Navigation mobile"
      @click="open = false"
    >
      <RouterLink to="/recherche"
        >Trouver un voyage<AppIcon name="arrow" :size="18" /></RouterLink
      ><RouterLink to="/ma-reservation"
        >Ma réservation<AppIcon name="arrow" :size="18" /></RouterLink
      ><RouterLink to="/conditions-voyage"
        >Guide du voyage<AppIcon name="arrow" :size="18" /></RouterLink
      ><RouterLink
        v-if="auth.isAuthenticated"
        :to="isPassenger ? '/mon-profil' : '/profil'"
        >Mon profil<AppIcon name="user" :size="18" /></RouterLink
      ><RouterLink v-if="!auth.isAuthenticated" to="/register"
        >Créer un compte<AppIcon name="arrow" :size="18" /></RouterLink
      ><button v-else type="button" @click="logout">
        Se déconnecter<AppIcon name="logout" :size="18" />
      </button>
    </nav>
  </header>
</template>
