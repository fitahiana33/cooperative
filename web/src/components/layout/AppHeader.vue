<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import Dropdown from "../ui/Dropdown.vue";
import UserAvatar from "../ui/UserAvatar.vue";
import AppIcon from "../ui/AppIcon.vue";
import NetworkStatus from "../ui/NetworkStatus.vue";
import { navigation, roleLabels } from "./navigation";
import { useSidebarStore } from "./sidebarStore";
import { useAuthenticationStore } from "../../stores/authentication/store";
const sidebar = useSidebarStore();
const auth = useAuthenticationStore();
const router = useRouter();
const route = useRoute();
const header = ref<HTMLElement>();
let headerObserver: ResizeObserver | undefined;
onMounted(() => {
  headerObserver = new ResizeObserver(() => {
    const element = header.value;
    element
      ?.closest<HTMLElement>(".dashboard-shell")
      ?.style.setProperty(
        "--section-tabs-top",
        `${element.getBoundingClientRect().height}px`,
      );
  });
  if (header.value) headerObserver.observe(header.value);
});
onBeforeUnmount(() => headerObserver?.disconnect());
const section = computed(
  () =>
    navigation.find((group) =>
      group.items.some(
        (item) =>
          route.path === item.to ||
          (item.to !== "/backoffice" && route.path.startsWith(item.to + "/")),
      ),
    )?.label || "Espace de gestion",
);
const role = computed(
  () => roleLabels[auth.user?.role?.toLowerCase() || ""] || auth.user?.role,
);
async function logout() {
  await auth.logout();
  await router.push({ name: "frontoffice" });
}
function openProfile() {
  void router.push({ name: "profile" });
}
</script>
<template>
  <header ref="header" class="app-header">
    <button
      class="hamburger"
      type="button"
      aria-label="Ouvrir le menu"
      aria-controls="workspace-navigation"
      :aria-expanded="sidebar.mobileOpen"
      @click="sidebar.openMobile"
    >
      <AppIcon name="menu" />
    </button>
    <div class="header-heading">
      <span class="eyebrow">{{ section }}</span>
      <h1><slot>Vue d’ensemble</slot></h1>
    </div>
    <div v-if="auth.user" class="header-actions">
      <NetworkStatus />
      <RouterLink to="/" class="header-public-link"
        ><AppIcon name="external" :size="16" /> Site voyageur</RouterLink
      >
      <RouterLink
        v-if="auth.hasPermission('NOTIFICATION_READ')"
        to="/notifications"
        class="notification-button"
        aria-label="Notifications"
        title="Notifications"
        ><AppIcon name="bell"
      /></RouterLink>
      <span class="header-divider" />
      <Dropdown
        ><template #trigger
          ><UserAvatar :user="auth.user" /><span class="header-user-copy"
            ><strong>{{ auth.user.first_name }} {{ auth.user.name }}</strong
            ><small>{{ role }}</small></span
          ></template
        ><button class="dropdown-option" @click="openProfile">
          <AppIcon name="user" :size="17" />Mon profil</button
        ><button class="dropdown-option logout-option" @click="logout">
          <AppIcon name="logout" :size="17" />Se déconnecter
        </button></Dropdown
      >
    </div>
  </header>
</template>
