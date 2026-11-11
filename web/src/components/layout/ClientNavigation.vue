<script setup lang="ts">
import { RouterLink, useRouter } from "vue-router";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import AppIcon from "../ui/AppIcon.vue";
import { useAuthenticationStore } from "../../stores/authentication/store";
const auth = useAuthenticationStore();
const router = useRouter();
const navigation = ref<HTMLElement>();
function revealCurrent() {
  const nav = navigation.value;
  const link = nav?.querySelector<HTMLElement>(".is-current");
  if (!nav || !link) return;
  const bounds = nav.getBoundingClientRect();
  const item = link.getBoundingClientRect();
  if (item.right > bounds.right) nav.scrollLeft += item.right - bounds.right;
  else if (item.left < bounds.left) nav.scrollLeft -= bounds.left - item.left;
}
let observer: ResizeObserver | undefined;
onMounted(() => {
  observer = new ResizeObserver(revealCurrent);
  if (navigation.value) observer.observe(navigation.value);
  void document.fonts.ready.then(revealCurrent);
});
onBeforeUnmount(() => observer?.disconnect());
watch(() => router.currentRoute.value.path, revealCurrent, { flush: "post" });
async function logout() {
  await auth.logout();
  await router.push("/");
}
const links = [
  { to: "/espace-client", label: "Vue d’ensemble", icon: "grid" },
  { to: "/mes-reservations", label: "Mes réservations", icon: "ticket" },
  { to: "/mes-billets", label: "Mes billets", icon: "scan" },
  { to: "/mon-profil", label: "Mon profil", icon: "user" },
];
</script>
<template>
  <div class="client-navigation">
    <nav ref="navigation" aria-label="Mon espace voyageur">
      <RouterLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        exact-active-class="is-current"
        ><AppIcon :name="link.icon" :size="17" />{{ link.label }}</RouterLink
      >
    </nav>
    <button type="button" @click="logout">
      <AppIcon name="logout" :size="16" /><span>Déconnexion</span>
    </button>
  </div>
</template>
