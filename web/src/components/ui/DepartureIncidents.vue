<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../../services/api";
import { userError } from "../../utils/errors";
interface Incident { id: number; type: string; description: string; statut: string; resolution?: string; date: string; auteur: string }
const props = defineProps<{ departId: number; canManage: boolean }>();
const incidents = ref<Incident[]>([]);
const busy = ref(false);
const error = ref("");
const kind = ref("PANNE");
const description = ref("");
const resolving = ref<number | null>(null);
const resolution = ref("");
async function load() {
  try { incidents.value = (await api.get<Incident[]>(`/departs/${props.departId}/incidents`)).data; }
  catch (value) { error.value = userError(value, "Le journal des incidents est indisponible.", "INCIDENT_LOAD_ERROR"); }
}
async function submit() {
  if (busy.value) return;
  busy.value = true; error.value = "";
  try {
    incidents.value = (await api.post<Incident[]>(`/departs/${props.departId}/incidents`, { type: kind.value, description: description.value })).data;
    description.value = "";
  } catch (value) { error.value = userError(value, "L’incident n’a pas pu être enregistré.", "INCIDENT_REPORT_ERROR"); }
  finally { busy.value = false; }
}
async function resolve() {
  if (busy.value || !resolving.value) return;
  busy.value = true; error.value = "";
  try {
    incidents.value = (await api.post<Incident[]>(`/departs/${props.departId}/incidents/${resolving.value}/resolution`, { description: resolution.value })).data;
    resolving.value = null; resolution.value = "";
  } catch (value) { error.value = userError(value, "La résolution n’a pas pu être enregistrée.", "INCIDENT_RESOLVE_ERROR"); }
  finally { busy.value = false; }
}
onMounted(load);
</script>
<template>
  <section class="incident-journal">
    <h2>Journal des incidents</h2>
    <p>Tracez les difficultés du voyage et les mesures prises. Les changements de planning, annulations et remboursements conservent leurs contrôles métier.</p>
    <p v-if="error" role="alert">{{ error }} <button type="button" @click="load">Réessayer</button></p>
    <p v-if="!incidents.length && !error">Aucun incident signalé.</p>
    <article v-for="incident in incidents" :key="incident.id">
      <strong>{{ incident.type }} · {{ incident.statut === 'RESOLU' ? 'Résolu' : 'Ouvert' }}</strong>
      <p>{{ incident.description }}</p><small>{{ new Date(incident.date).toLocaleString('fr-FR') }} · {{ incident.auteur }}</small>
      <p v-if="incident.resolution">Mesures prises : {{ incident.resolution }}</p>
      <button v-if="canManage && incident.statut === 'OUVERT'" type="button" :disabled="busy" @click="resolving = incident.id">Consigner la résolution</button>
    </article>
    <form v-if="resolving" @submit.prevent="resolve"><label>Mesures prises<textarea v-model="resolution" minlength="10" maxlength="3000" required :disabled="busy" /></label><button type="submit" :disabled="busy">Clôturer l’incident</button><button type="button" @click="resolving = null">Fermer</button></form>
    <details v-if="canManage"><summary>Signaler un incident</summary>
      <form @submit.prevent="submit"><label>Type<select v-model="kind" :disabled="busy"><option value="PANNE">Panne</option><option value="RETARD">Retard</option><option value="REMPLACEMENT">Remplacement à organiser</option><option value="EMBARQUEMENT">Embarquement</option><option value="AUTRE">Autre</option></select></label><label>Description<textarea v-model="description" minlength="10" maxlength="3000" required :disabled="busy" /></label><button type="submit" :disabled="busy">Enregistrer l’incident</button></form>
    </details>
  </section>
</template>
<style scoped>
.incident-journal { border: 1px solid var(--line); border-radius: 12px; padding: 1.5rem; background: var(--surface); margin-top: 1.5rem; }
article { border-top: 1px solid var(--line); padding: 1rem 0; }
form, label { display: grid; gap: .5rem; } form { max-width: 640px; margin-top: 1rem; }
input, select, button, textarea { min-height: 44px; border: 1px solid var(--line); border-radius: 8px; padding: .6rem; background: var(--surface); color: var(--ink-strong); }
textarea { min-height: 90px; resize: vertical; } summary, button { cursor: pointer; } small { color: var(--ink-muted); }
</style>
