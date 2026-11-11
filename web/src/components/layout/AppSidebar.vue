<script setup lang="ts">
import {
  computed,
  nextTick,
  onMounted,
  onBeforeUnmount,
  ref,
  watch,
} from "vue";
import { RouterLink, useRoute } from "vue-router";
import AppIcon from "../ui/AppIcon.vue";
import { navigation } from "./navigation";
import { useSidebarStore } from "./sidebarStore";
import { useAuthenticationStore } from "../../stores/authentication/store";
const auth = useAuthenticationStore();
const sidebar = useSidebarStore();
const route = useRoute();
const aside = ref<HTMLElement>();
const nav = ref<HTMLElement>();
const filter = ref("");
const groups = computed(() =>
  navigation
    .map((group) => ({
      ...group,
      items: group.items.filter(
        (item) =>
          (!item.permission || auth.hasPermission(item.permission)) &&
          (!item.admin || auth.userRole?.toLowerCase() === "admin") &&
          item.label
            .toLocaleLowerCase("fr")
            .includes(filter.value.toLocaleLowerCase("fr")),
      ),
    }))
    .filter((group) => group.items.length),
);
function active(to: string) {
  return to === "/backoffice"
    ? route.path === to
    : route.path === to || route.path.startsWith(to + "/");
}
function rememberScroll() {
  sidebar.rememberNavScroll(nav.value?.scrollTop || 0);
}
let previousFocus: HTMLElement | null = null;
watch(
  () => sidebar.mobileOpen,
  async (open) => {
    document.body.classList.toggle("navigation-open", open);
    if (open) {
      previousFocus = document.activeElement as HTMLElement;
      await nextTick();
      aside.value?.querySelector<HTMLElement>("button")?.focus();
    } else previousFocus?.focus();
  },
);
function keyboard(event: KeyboardEvent) {
  if (!sidebar.mobileOpen) return;
  if (event.key === "Escape") {
    event.preventDefault();
    sidebar.closeMobile();
  }
  if (event.key === "Tab") {
    const controls = Array.from(
      aside.value?.querySelectorAll<HTMLElement>("a, button, input") || [],
    ).filter((element) => element.offsetParent !== null);
    if (!controls?.length) return;
    const first = controls[0],
      last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
  }
}
watch(
  () => route.fullPath,
  async () => {
    sidebar.closeMobile();
    await nextTick();
    if (nav.value) nav.value.scrollTop = sidebar.navScrollTop;
  },
);
function resize() {
  if (window.innerWidth > 900 && sidebar.mobileOpen) sidebar.closeMobile();
}
onMounted(() => {
  document.addEventListener("keydown", keyboard);
  window.addEventListener("resize", resize);
  if (nav.value) nav.value.scrollTop = sidebar.navScrollTop;
});
onBeforeUnmount(() => {
  document.removeEventListener("keydown", keyboard);
  window.removeEventListener("resize", resize);
  document.body.classList.remove("navigation-open");
});
</script>
<template>
  <div
    v-if="sidebar.mobileOpen"
    class="sidebar-backdrop"
    aria-hidden="true"
    @click="sidebar.closeMobile"
  />
  <aside
    ref="aside"
    id="workspace-navigation"
    class="app-sidebar"
    :class="{ collapsed: sidebar.collapsed, 'mobile-open': sidebar.mobileOpen }"
    :role="sidebar.mobileOpen ? 'dialog' : undefined"
    :aria-modal="sidebar.mobileOpen ? true : undefined"
    aria-label="Navigation de l’application"
  >
    <div class="sidebar-brand">
      <RouterLink
        to="/backoffice"
        class="workspace-brand"
        aria-label="Coopérative, tableau de bord"
        ><span class="brand-symbol"><AppIcon name="route" :size="23" /></span
        ><span class="sidebar-name"
          >Coopérative<small>Espace de gestion</small></span
        ></RouterLink
      >
      <button
        class="sidebar-mobile-close"
        type="button"
        aria-label="Fermer le menu"
        @click="sidebar.closeMobile"
      >
        <AppIcon name="close" />
      </button>
    </div>
    <label class="sidebar-filter"
      ><AppIcon name="search" :size="17" /><input
        v-model="filter"
        type="search"
        placeholder="Trouver un module…"
        aria-label="Filtrer les modules"
    /></label>
    <nav ref="nav" class="sidebar-nav" @scroll.passive="rememberScroll">
      <div v-for="group in groups" :key="group.label" class="sidebar-group">
        <p class="sidebar-section">{{ group.label }}</p>
        <div class="sidebar-submenu">
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="sidebar-link"
            :class="{ 'is-current': active(item.to) }"
            :title="item.label"
            :aria-current="active(item.to) ? 'page' : undefined"
            @click="sidebar.closeMobile"
            ><AppIcon :name="item.icon" :size="19" /><b>{{ item.label }}</b
            ><span v-if="active(item.to)" class="nav-current-dot"
          /></RouterLink>
        </div>
      </div>
      <p v-if="!groups.length" class="sidebar-no-results">
        Aucun module trouvé.
      </p>
    </nav>
    <div class="sidebar-footer">
      <RouterLink to="/" title="Voir le site voyageur"
        ><AppIcon name="external" :size="18" /><span class="sidebar-name"
          >Site voyageur</span
        ></RouterLink
      ><button
        class="sidebar-toggle"
        type="button"
        :aria-label="
          sidebar.collapsed ? 'Développer le menu' : 'Réduire le menu'
        "
        :aria-expanded="!sidebar.collapsed"
        @click="sidebar.toggle"
      >
        <AppIcon :name="sidebar.collapsed ? 'chevron' : 'back'" :size="17" />
      </button>
    </div>
  </aside>
</template>
