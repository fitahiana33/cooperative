<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { destinationService } from '../../services/destination/service'
import { itineraireService } from '../../services/itineraire/service'
import { tarifService } from '../../services/tarif/service'
import { cooperativeService } from '../../services/cooperative/service'
import { userError } from '../../utils/errors'

const route = useRoute(); const router = useRouter(); const id = route.params.id ? Number(route.params.id) : null
const section = computed(() => String(route.name).startsWith('destination') ? 'destinations' : String(route.name).startsWith('itineraire') ? 'itineraires' : 'tarifs')
const editing = computed(() => Boolean(id)); const loading = ref(Boolean(id)); const submitting = ref(false); const error = ref('')
const destination = reactive({ nom: '', region: '', description: '' })
const itinerary = reactive({ id_destination_depart: 0, id_destination_arrivee: 0, distance_km: null as number | null, duree_estimee_minutes: null as number | null, description: '' })
const fare = reactive({ id_itineraire: 0, id_cooperative: null as number | null, prix: null as number | null, devise: 'MGA', date_debut: '', date_fin: '' })
const destinations = ref<any[]>([]); const itineraries = ref<any[]>([]); const cooperatives = ref<any[]>([])
const backPath = computed(() => `/${section.value}`); const heading = computed(() => editing.value ? 'Modifier' : 'Nouvelle')
function showError(value: unknown, fallback: string) { error.value = userError(value, fallback, 'ROUTES_FORM_ERROR') }
async function loadRefs() {
  const results = await Promise.allSettled([
    destinationService.list({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
    itineraireService.list({ page: 1, page_size: 100, sort_by: 'created_at', sort_order: 'desc' }),
    cooperativeService.listCooperatives({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
  ])
  if (results[0].status === 'fulfilled') destinations.value = results[0].value.items
  if (results[1].status === 'fulfilled') itineraries.value = results[1].value.items
  if (results[2].status === 'fulfilled') cooperatives.value = results[2].value.items
}
onMounted(async () => { await loadRefs(); if (!id) { loading.value = false; return }; try { const value = section.value === 'destinations' ? await destinationService.get(id) : section.value === 'itineraires' ? await itineraireService.get(id) : await tarifService.get(id); if (section.value === 'destinations') Object.assign(destination, value); else if (section.value === 'itineraires') Object.assign(itinerary, value); else Object.assign(fare, { ...value, date_debut: value.date_debut || '', date_fin: value.date_fin || '' }) } catch (value: unknown) { showError(value, 'Impossible de charger cet element.') } finally { loading.value = false } })
async function submit() {
  if (submitting.value) return; submitting.value = true; error.value = ''
  try {
    if (section.value === 'destinations') editing.value ? await destinationService.update(id!, destination) : await destinationService.create(destination)
    if (section.value === 'itineraires') editing.value ? await itineraireService.update(id!, itinerary) : await itineraireService.create(itinerary)
    if (section.value === 'tarifs') { const data = { ...fare, date_debut: fare.date_debut || undefined, date_fin: fare.date_fin || null }; editing.value ? await tarifService.update(id!, data) : await tarifService.create(data) }
    await router.push({ path: backPath.value, query: { success: `${section.value.slice(0, -1)} enregistre avec succes.` } })
  } catch (value: unknown) { showError(value, 'Enregistrement impossible.') } finally { submitting.value = false }
}
</script>

<template><AppLayout><template #title>{{ heading }} {{ section }}</template><div class="page-intro"><div><p class="eyebrow">RESEAU & TARIFICATION</p><h2>{{ heading }} {{ section }}</h2><p>Renseignez les informations puis enregistrez.</p></div><RouterLink class="secondary-button" :to="backPath">Retour a la liste</RouterLink></div><BaseCard><p v-if="loading" class="status-msg">Chargement...</p><p v-else-if="error" class="error-banner" role="alert">{{ error }}</p><form v-else class="management-form form-page" @submit.prevent="submit">
  <template v-if="section === 'destinations'"><div class="field-group"><label>Nom <span>*</span></label><input v-model="destination.nom" required maxlength="150" placeholder="Ex. Antananarivo" /></div><div class="field-group"><label>Region</label><input v-model="destination.region" maxlength="100" placeholder="Ex. Analamanga" /></div><div class="field-group field-wide"><label>Description</label><textarea v-model="destination.description" /></div></template>
  <template v-else-if="section === 'itineraires'"><div class="field-group"><label>Depart <span>*</span></label><select v-model.number="itinerary.id_destination_depart" required><option :value="0" disabled>Choisir une destination</option><option v-for="item in destinations" :key="item.id" :value="item.id">{{ item.nom }}</option></select></div><div class="field-group"><label>Arrivee <span>*</span></label><select v-model.number="itinerary.id_destination_arrivee" required><option :value="0" disabled>Choisir une destination</option><option v-for="item in destinations" :key="item.id" :value="item.id">{{ item.nom }}</option></select></div><div class="field-group"><label>Distance (km)</label><input v-model.number="itinerary.distance_km" type="number" min="0.01" step="0.01" /></div><div class="field-group"><label>Duree estimee (minutes)</label><input v-model.number="itinerary.duree_estimee_minutes" type="number" min="1" step="1" /></div><div class="field-group field-wide"><label>Description</label><textarea v-model="itinerary.description" /></div></template>
  <template v-else><div class="field-group"><label>Itineraire <span>*</span></label><select v-model.number="fare.id_itineraire" required :disabled="editing"><option :value="0" disabled>Choisir un itineraire</option><option v-for="item in itineraries" :key="item.id" :value="item.id">{{ item.destination_depart?.nom || item.id_destination_depart }} - {{ item.destination_arrivee?.nom || item.id_destination_arrivee }}</option></select></div><div class="field-group"><label>Portee cooperative</label><select v-model="fare.id_cooperative"><option :value="null">Tarif general</option><option v-for="item in cooperatives" :key="item.id" :value="item.id">{{ item.nom }}</option></select></div><div class="field-group"><label>Prix <span>*</span></label><input v-model.number="fare.prix" type="number" min="0.01" step="0.01" required /></div><div class="field-group"><label>Devise</label><input v-model="fare.devise" maxlength="10" required /></div><div class="field-group"><label>Date de debut</label><input v-model="fare.date_debut" type="date" /></div><div class="field-group"><label>Date de fin</label><input v-model="fare.date_fin" type="date" /></div></template>
  <div class="form-actions"><button class="primary-button compact-button" type="submit" :disabled="submitting">{{ submitting ? 'Enregistrement...' : 'Enregistrer' }}</button><RouterLink class="secondary-button" :to="backPath">Annuler</RouterLink></div></form></BaseCard></AppLayout></template>
