<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { chauffeurService } from '../../services/chauffeur/service'
import { cooperativeService } from '../../services/cooperative/service'
import { departService } from '../../services/depart/service'
import { itineraireService } from '../../services/itineraire/service'
import { tarifService } from '../../services/tarif/service'
import { vehiculeService } from '../../services/vehicule/service'
import { userError } from '../../utils/errors'

const route = useRoute()
const router = useRouter()
const id = route.params.id ? Number(route.params.id) : null
const editing = computed(() => Boolean(id))
const loading = ref(Boolean(id))
const submitting = ref(false)
const error = ref('')

const form = reactive({
  id_itineraire: 0,
  id_cooperative: 0,
  id_vehicule: 0,
  id_chauffeur: 0,
  id_tarif: 0,
  date_depart: new Date().toISOString().slice(0, 10),
  heure_depart: '08:00',
  nombre_places: null as number | null,
})

const itineraires = ref<any[]>([])
const cooperatives = ref<any[]>([])
const vehicules = ref<any[]>([])
const chauffeurs = ref<any[]>([])
const tarifs = ref<any[]>([])
const backPath = '/departs'

function coversDate(start: string | null | undefined, end: string | null | undefined) {
  return Boolean(start) && start <= form.date_depart && (!end || end >= form.date_depart)
}

const selectedItinerary = computed(() => itineraires.value.find((item) => item.id === form.id_itineraire))
const selectedVehicle = computed(() => vehicules.value.find((item) => item.id === form.id_vehicule))
const selectedRouteAssociation = computed(() => selectedItinerary.value?.cooperatives?.find((item: any) => (
  item.id_cooperative === form.id_cooperative && item.is_active && coversDate(item.date_debut, item.date_fin)
)))
const filteredVehicules = computed(() => vehicules.value.filter((item) => (
  !form.id_cooperative || item.id_cooperative === form.id_cooperative
)))
const filteredChauffeurs = computed(() => chauffeurs.value.filter((item) => (
  (!form.id_cooperative || item.id_cooperative === form.id_cooperative)
  && item.date_expiration_permis >= form.date_depart
)))
const filteredTarifs = computed(() => tarifs.value.filter((item) => (
  item.is_active
  && item.id_itineraire === form.id_itineraire
  && (item.id_cooperative == null || item.id_cooperative === form.id_cooperative)
  && coversDate(item.date_debut, item.date_fin)
)))

function routeName(item: any) {
  return `${item.destination_depart?.nom || item.id_destination_depart} → ${item.destination_arrivee?.nom || item.id_destination_arrivee}`
}

async function loadReferences() {
  const results = await Promise.allSettled([
    itineraireService.list({ page: 1, page_size: 100, sort_by: 'created_at', sort_order: 'desc' }),
    cooperativeService.listCooperatives({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
    vehiculeService.listVehicules({ page: 1, page_size: 100, sort_by: 'immatriculation', sort_order: 'asc' }),
    chauffeurService.listChauffeurs({ page: 1, page_size: 100, sort_by: 'created_at', sort_order: 'desc' }),
    tarifService.list({ page: 1, page_size: 100, sort_by: 'date_debut', sort_order: 'desc' }),
  ])

  if (results[0].status === 'fulfilled') itineraires.value = results[0].value.items.filter((item: any) => item.is_active)
  if (results[1].status === 'fulfilled') cooperatives.value = results[1].value.items.filter((item: any) => item.is_active)
  if (results[2].status === 'fulfilled') vehicules.value = results[2].value.items.filter((item: any) => item.is_active && item.disponibilite)
  if (results[3].status === 'fulfilled') chauffeurs.value = results[3].value.items.filter((item: any) => item.is_active && item.disponibilite)
  if (results[4].status === 'fulfilled') tarifs.value = results[4].value.items
}

onMounted(async () => {
  await loadReferences()
  if (!id) {
    loading.value = false
    return
  }

  try {
    Object.assign(form, await departService.get(id))
    form.heure_depart = form.heure_depart.slice(0, 5)
  } catch (value: unknown) {
    error.value = userError(value, 'Impossible de charger ce départ.', 'DEPART_FORM_LOAD_ERROR')
  } finally {
    loading.value = false
  }
})

function cooperativeChanged() {
  form.id_vehicule = 0
  form.id_chauffeur = 0
  form.id_tarif = 0
  form.nombre_places = null
}

function itineraryChanged() {
  form.id_tarif = 0
}

function vehicleChanged() {
  if (selectedVehicle.value) form.nombre_places = selectedVehicle.value.nombre_places
}

async function submit() {
  if (submitting.value) return
  error.value = ''

  if (!selectedRouteAssociation.value) {
    error.value = 'La coopérative sélectionnée n’est pas autorisée sur cet itinéraire pour la date choisie. Associez-la d’abord à l’itinéraire.'
    return
  }
  if (!filteredVehicules.value.some((item) => item.id === form.id_vehicule)) {
    error.value = 'Le véhicule sélectionné doit être actif, disponible et appartenir à la coopérative choisie.'
    return
  }
  if (!filteredChauffeurs.value.some((item) => item.id === form.id_chauffeur)) {
    error.value = 'Le chauffeur sélectionné doit être actif, disponible et avoir un permis valide à la date du départ.'
    return
  }
  if (!filteredTarifs.value.some((item) => item.id === form.id_tarif)) {
    error.value = 'Aucun tarif actif ne couvre cet itinéraire, cette coopérative et la date choisie.'
    return
  }

  submitting.value = true
  try {
    const payload = { ...form, nombre_places: form.nombre_places || undefined }
    if (editing.value) await departService.update(id!, payload)
    else await departService.create(payload)
    await router.push({
      path: backPath,
      query: { success: editing.value ? 'Départ modifié avec succès.' : 'Départ programmé avec succès.' },
    })
  } catch (value: unknown) {
    error.value = userError(value, 'Impossible d’enregistrer le départ.', 'DEPART_FORM_ERROR')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppLayout>
    <template #title>{{ editing ? 'Modifier' : 'Programmer' }} un départ</template>

    <div class="page-intro">
      <div>
        <p class="eyebrow">PLANIFICATION</p>
        <h2>{{ editing ? 'Modifier' : 'Programmer' }} un départ</h2>
        <p>Associez un itinéraire autorisé, un tarif valide, un véhicule et un chauffeur affecté.</p>
      </div>
      <RouterLink class="secondary-button" :to="backPath">Retour à la liste</RouterLink>
    </div>

    <BaseCard>
      <p v-if="loading" class="status-msg">Chargement…</p>

      <template v-else>
        <p v-if="error" class="error-banner" role="alert">{{ error }}</p>

        <form class="management-form form-page" @submit.prevent="submit">
          <div class="field-group">
            <label>Itinéraire <span>*</span></label>
            <select v-model.number="form.id_itineraire" required @change="itineraryChanged">
              <option :value="0" disabled>Choisir un itinéraire</option>
              <option v-for="item in itineraires" :key="item.id" :value="item.id">{{ routeName(item) }}</option>
            </select>
          </div>

          <div class="field-group">
            <label>Coopérative <span>*</span></label>
            <select v-model.number="form.id_cooperative" required @change="cooperativeChanged">
              <option :value="0" disabled>Choisir une coopérative</option>
              <option v-for="item in cooperatives" :key="item.id" :value="item.id">{{ item.nom }}</option>
            </select>
          </div>

          <div class="field-group">
            <label>Véhicule <span>*</span></label>
            <select v-model.number="form.id_vehicule" required @change="vehicleChanged">
              <option :value="0" disabled>Choisir un véhicule</option>
              <option v-for="item in filteredVehicules" :key="item.id" :value="item.id">
                {{ item.immatriculation }} — {{ item.nombre_places }} places
              </option>
            </select>
          </div>

          <div class="field-group">
            <label>Chauffeur <span>*</span></label>
            <select v-model.number="form.id_chauffeur" required>
              <option :value="0" disabled>Choisir un chauffeur</option>
              <option v-for="item in filteredChauffeurs" :key="item.id" :value="item.id">
                {{ item.user?.first_name || '' }} {{ item.user?.name || '' }} — {{ item.numero_permis }}
              </option>
            </select>
          </div>

          <div class="field-group">
            <label>Tarif <span>*</span></label>
            <select v-model.number="form.id_tarif" required>
              <option :value="0" disabled>Choisir un tarif</option>
              <option v-for="item in filteredTarifs" :key="item.id" :value="item.id">
                {{ item.prix }} {{ item.devise }} — {{ item.id_cooperative ? 'Coopératif' : 'Général' }}
              </option>
            </select>
            <span v-if="form.id_itineraire && !filteredTarifs.length" class="field-hint">
              Aucun tarif actif ne couvre cet itinéraire, cette coopérative et cette date.
            </span>
          </div>

          <div class="field-group">
            <label>Date <span>*</span></label>
            <input v-model="form.date_depart" type="date" required />
          </div>

          <div class="field-group">
            <label>Heure <span>*</span></label>
            <input v-model="form.heure_depart" type="time" required />
          </div>

          <div class="field-group">
            <label>Nombre de places <span>*</span></label>
            <input v-model.number="form.nombre_places" type="number" min="1" :max="selectedVehicle?.nombre_places || undefined" required />
            <span v-if="selectedVehicle" class="field-hint">Capacité maximale : {{ selectedVehicle.nombre_places }} places.</span>
          </div>

          <div class="form-actions">
            <button class="primary-button compact-button" type="submit" :disabled="submitting">
              {{ submitting ? 'Enregistrement…' : 'Enregistrer' }}
            </button>
            <RouterLink class="secondary-button" :to="backPath">Annuler</RouterLink>
          </div>
        </form>
      </template>
    </BaseCard>
  </AppLayout>
</template>
