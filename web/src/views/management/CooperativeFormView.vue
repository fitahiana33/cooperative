<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { managementService } from '../../services/management/service'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { userError } from '../../utils/errors'
import type { User } from '../../models/user/model'

const route = useRoute()
const router = useRouter()
const auth = useAuthenticationStore()
const id = route.params.id ? Number(route.params.id) : null
const editing = Boolean(id)
const loading = ref(editing)
const submitting = ref(false)
const error = ref('')
const users = ref<User[]>([])
const form = reactive({
  nom: '', sigle: '', numero_agrement: '', adresse: '', ville: '', telephone: '', email: '',
  description: '', responsable_id: null as number | null,
})

const canAssignResponsible = auth.userRole.toLowerCase() === 'admin'

onMounted(async () => {
  try {
    const requests: Promise<unknown>[] = []
    if (id) requests.push(managementService.getCooperative(id))
    if (canAssignResponsible) requests.push(managementService.listEligibleResponsables())
    const results = await Promise.all(requests)
    let index = 0
    if (id) Object.assign(form, results[index++])
    if (canAssignResponsible) users.value = results[index] as User[]
  } catch (errorValue: unknown) {
    error.value = userError(errorValue, 'Impossible de charger cette coopérative.', 'COOPERATIVE_FORM_LOAD_ERROR')
  } finally {
    loading.value = false
  }
})

async function submit() {
  if (submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const payload = { ...form }
    if (!canAssignResponsible) delete (payload as { responsable_id?: number | null }).responsable_id
    if (id) await managementService.updateCooperative(id, payload)
    else await managementService.createCooperative(payload)
    await router.push({ path: '/cooperatives', query: { success: id ? 'Coopérative modifiée avec succès.' : 'Coopérative créée avec succès.' } })
  } catch (errorValue: unknown) {
    error.value = userError(errorValue, 'Enregistrement impossible.', 'COOPERATIVE_FORM_SAVE_ERROR')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppLayout>
    <template #title>{{ editing ? 'Modifier la coopérative' : 'Nouvelle coopérative' }}</template>
    <div class="page-intro">
      <div><p class="eyebrow">GESTION DES COOPÉRATIVES</p><h2>{{ editing ? 'Modifier la coopérative' : 'Ajouter une coopérative' }}</h2><p>Renseignez les informations de la coopérative puis enregistrez.</p></div>
      <RouterLink class="secondary-button" to="/cooperatives">Retour à la liste</RouterLink>
    </div>
    <BaseCard>
      <p v-if="loading" class="status-msg">Chargement des données en cours…</p>
      <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
      <form v-else class="management-form form-page" @submit.prevent="submit">
        <div class="field-group"><label for="coop-nom">Nom de la coopérative <span>*</span></label><input id="coop-nom" v-model="form.nom" required placeholder="Nom officiel" /></div>
        <div class="field-group"><label for="coop-sigle">Sigle</label><input id="coop-sigle" v-model="form.sigle" placeholder="Ex. Cotisse" /></div>
        <div class="field-group"><label for="coop-agrement">Numéro d’agrément</label><input id="coop-agrement" v-model="form.numero_agrement" placeholder="Numéro d’agrément ou NIF" /></div>
        <div v-if="canAssignResponsible" class="field-group"><label for="coop-responsable">Responsable</label><select id="coop-responsable" v-model="form.responsable_id"><option :value="null">Non désigné</option><option v-for="user in users" :key="user.id" :value="user.id">{{ user.first_name || '' }} {{ user.name }} — {{ user.email }}</option></select></div>
        <div class="field-group"><label for="coop-adresse">Adresse</label><input id="coop-adresse" v-model="form.adresse" placeholder="Adresse du siège" /></div>
        <div class="field-group"><label for="coop-ville">Ville</label><input id="coop-ville" v-model="form.ville" placeholder="Ville" /></div>
        <div class="field-group"><label for="coop-telephone">Téléphone</label><input id="coop-telephone" v-model="form.telephone" placeholder="Téléphone de contact" /></div>
        <div class="field-group"><label for="coop-email">Adresse email</label><input id="coop-email" v-model="form.email" type="email" placeholder="contact@exemple.com" /></div>
        <div class="field-group field-wide"><label for="coop-description">Description</label><textarea id="coop-description" v-model="form.description" placeholder="Informations complémentaires"></textarea></div>
        <div class="form-actions"><button class="primary-button compact-button" type="submit" :disabled="submitting">{{ submitting ? 'Enregistrement…' : 'Enregistrer' }}</button><RouterLink class="secondary-button" to="/cooperatives">Annuler</RouterLink></div>
      </form>
    </BaseCard>
  </AppLayout>
</template>
