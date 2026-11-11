<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);
const lastSuccess = ref<Date | null>(null);
const lastError = ref(false);
const clock = ref(Date.now());
let timer: ReturnType<typeof setInterval> | undefined;

const ageMinutes = computed(() => lastSuccess.value ? Math.floor((clock.value - lastSuccess.value.getTime()) / 60_000) : 0);
const label = computed(() => {
  if (!online.value) return "Hors connexion";
  if (lastError.value) return "Synchronisation à vérifier";
  if (!lastSuccess.value) return "Connexion active";
  if (ageMinutes.value < 1) return "Données à jour";
  return `Actualisées il y a ${ageMinutes.value} min`;
});
const tone = computed(() => !online.value || lastError.value ? "warning" : ageMinutes.value >= 2 ? "stale" : "online");

function onOnline() { online.value = true; }
function onOffline() { online.value = false; }
function onSuccess(event: Event) {
  const detail = (event as CustomEvent<{ at?: string }>).detail;
  lastSuccess.value = detail?.at ? new Date(detail.at) : new Date();
  lastError.value = false;
}
function onError() { lastError.value = true; }

onMounted(() => {
  window.addEventListener("online", onOnline);
  window.addEventListener("offline", onOffline);
  window.addEventListener("app:data-refreshed", onSuccess);
  window.addEventListener("app:data-error", onError);
  timer = setInterval(() => { clock.value = Date.now(); }, 30_000);
});
onBeforeUnmount(() => {
  window.removeEventListener("online", onOnline);
  window.removeEventListener("offline", onOffline);
  window.removeEventListener("app:data-refreshed", onSuccess);
  window.removeEventListener("app:data-error", onError);
  if (timer) clearInterval(timer);
});
</script>

<template>
  <span :class="['network-status', tone]" role="status" :title="label">
    <i aria-hidden="true" />
    <span>{{ label }}</span>
  </span>
</template>

<style scoped>
.network-status { display: inline-flex; align-items: center; gap: .45rem; color: var(--ink-muted); font-size: 11px; white-space: nowrap; }
.network-status i { width: 7px; height: 7px; border-radius: 50%; background: #42a06f; box-shadow: 0 0 0 3px #42a06f18; }
.network-status.stale i { background: #d39a2f; box-shadow: 0 0 0 3px #d39a2f18; }
.network-status.warning { color: #9a4638; }.network-status.warning i { background: #d65d4d; box-shadow: 0 0 0 3px #d65d4d18; }
@media (max-width: 1100px) { .network-status > span { display: none; } }
</style>
