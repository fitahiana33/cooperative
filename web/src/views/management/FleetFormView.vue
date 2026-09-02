<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { vehiculeService, getDocumentUrl } from '../../services/vehicule/service'
import { chauffeurService } from '../../services/chauffeur/service'
import { marqueService } from '../../services/marque/service'
import { modeleService } from '../../services/modele/service'
import { cooperativeService } from '../../services/cooperative/service'
import { userService } from '../../services/user/service'
import type { DocumentType, Vehicule, VehiculeDocument, VehiculeEtat } from '../../models/vehicule/model'
import type { Chauffeur } from '../../models/chauffeur/model'
import type { Marque } from '../../models/marque/model'
import type { Modele } from '../../models/modele/model'
import type { Cooperative } from '../../models/cooperative/model'
import type { User } from '../../models/user/model'
import { userError } from '../../utils/errors'

type FleetSection = 'vehicules' | 'chauffeurs' | 'marques' | 'modeles'
type DocumentDraft = { key: number; type_document: DocumentType; numero_document: string; date_delivrance: string; date_expiration: string; file: File | null; is_valid: boolean }
const route = useRoute()
const router = useRouter()
const section = computed<FleetSection>(() => ({
  'vehicule-create': 'vehicules', 'vehicule-edit': 'vehicules',
  'chauffeur-create': 'chauffeurs', 'chauffeur-edit': 'chauffeurs',
  'marque-create': 'marques', 'marque-edit': 'marques',
  'modele-create': 'modeles', 'modele-edit': 'modeles',
}[String(route.name || 'vehicule-create')] || 'vehicules'))
const id = computed(() => route.params.id ? Number(route.params.id) : null)
const editing = computed(() => Boolean(id.value))
const title = computed(() => `${editing.value ? 'Modifier' : 'Ajouter'} ${{ vehicules: 'un véhicule', chauffeurs: 'un chauffeur', marques: 'une marque', modeles: 'un modèle' }[section.value]}`)
const listPath = computed(() => `/${section.value}`)

const vehiculeForm = reactive({ id_modele: 0, id_cooperative: 0, immatriculation: '', chevaux: null as number | null, nombre_places: 14, disponibilite: true, etat: 'BON_ETAT' as VehiculeEtat, description: '', is_active: true })
const chauffeurForm = reactive({ id_user: 0, id_cooperative: 0, numero_permis: '', categorie_permis: '', date_expiration_permis: '', disponibilite: true, is_active: true })
const marqueForm = reactive({ nom: '', description: '', is_active: true })
const modeleForm = reactive({ id_marque: 0, nom: '', description: '', is_active: true })
const documentDrafts = ref<DocumentDraft[]>([])
const existingDocuments = ref<VehiculeDocument[]>([])
let documentKey = 0

const marques = ref<Marque[]>([])
const modeles = ref<Modele[]>([])
const cooperatives = ref<Cooperative[]>([])
const users = ref<User[]>([])
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const selectedVehicleModel = computed(() => modeles.value.find(item => item.id === vehiculeForm.id_modele))
const selectedVehicleBrand = computed(() => marques.value.find(item => item.id === selectedVehicleModel.value?.id_marque))

function newDocumentDraft(): DocumentDraft { return { key: ++documentKey, type_document: 'CARTE_GRISE', numero_document: '', date_delivrance: '', date_expiration: '', file: null, is_valid: true } }
function addDocumentDraft() { documentDrafts.value.push(newDocumentDraft()) }
function removeDocumentDraft(key: number) { documentDrafts.value = documentDrafts.value.filter(item => item.key !== key) }
function onDraftFileChange(draft: DocumentDraft, event: Event) { draft.file = (event.target as HTMLInputElement).files?.[0] || null }
function documentTypeLabel(type: DocumentType) { return ({ CARTE_GRISE: 'Carte grise', ASSURANCE: 'Assurance', VISITE_TECHNIQUE: 'Visite technique' }[type]) }
function formatDocumentDate(value?: string | null) { return value ? new Date(value).toLocaleDateString('fr-FR') : '—' }
function showError(errorValue: unknown, fallback: string) { error.value = userError(errorValue, fallback, 'FLEET_FORM_ERROR') }

async function loadReferences() {
  const results = await Promise.allSettled([
    marqueService.listMarques({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
    modeleService.listModeles({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
    cooperativeService.listCooperatives({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
    userService.list({ page: 1, page_size: 100, sort_by: 'name', sort_order: 'asc' }),
  ])
  if (results[0].status === 'fulfilled') marques.value = results[0].value.items
  if (results[1].status === 'fulfilled') modeles.value = results[1].value.items
  if (results[2].status === 'fulfilled') cooperatives.value = results[2].value.items
  if (results[3].status === 'fulfilled') users.value = results[3].value.items

  const requiredIndexes = section.value === 'vehicules'
    ? [1, 2]
    : section.value === 'chauffeurs'
      ? [2, 3]
      : section.value === 'modeles'
        ? [0]
        : []
  const failedReference = requiredIndexes
    .map(index => results[index])
    .find(result => result.status === 'rejected')
  if (failedReference?.status === 'rejected') throw failedReference.reason
}

async function loadItem() {
  if (!id.value) return
  if (section.value === 'vehicules') {
    const item: Vehicule = await vehiculeService.getVehicule(id.value)
    Object.assign(vehiculeForm, item)
    existingDocuments.value = item.documents || []
  }
  if (section.value === 'chauffeurs') Object.assign(chauffeurForm, await chauffeurService.getChauffeur(id.value))
  if (section.value === 'marques') Object.assign(marqueForm, await marqueService.getMarque(id.value))
  if (section.value === 'modeles') Object.assign(modeleForm, await modeleService.getModele(id.value))
}

function validateDocumentDrafts() {
  const configured = documentDrafts.value.filter(item => item.file || item.numero_document || item.date_delivrance || item.date_expiration)
  for (const draft of configured) {
    if (!draft.file) { error.value = 'Chaque document renseigné doit avoir un fichier.'; return false }
    if (draft.date_delivrance && draft.date_expiration && draft.date_expiration < draft.date_delivrance) { error.value = "La date d'expiration doit être postérieure ou égale à la date de délivrance."; return false }
  }
  return true
}

async function uploadDrafts(vehicule: Vehicule) {
  for (const draft of documentDrafts.value.filter(item => item.file)) {
    const data = new FormData()
    data.append('type_document', draft.type_document)
    if (draft.numero_document) data.append('numero_document', draft.numero_document)
    if (draft.date_delivrance) data.append('date_delivrance', draft.date_delivrance)
    if (draft.date_expiration) data.append('date_expiration', draft.date_expiration)
    data.append('is_valid', String(draft.is_valid))
    data.append('file', draft.file as File)
    await vehiculeService.uploadDocument(vehicule.id, data)
  }
}

async function submitVehicule() {
  if (!validateDocumentDrafts()) throw new Error(error.value)
  const payload = { id_modele: vehiculeForm.id_modele, id_cooperative: vehiculeForm.id_cooperative, immatriculation: vehiculeForm.immatriculation, chevaux: vehiculeForm.chevaux || undefined, nombre_places: vehiculeForm.nombre_places, disponibilite: vehiculeForm.disponibilite, etat: vehiculeForm.etat, description: vehiculeForm.description || undefined, ...(editing.value ? { is_active: vehiculeForm.is_active } : {}) }
  const saved = id.value ? await vehiculeService.updateVehicule(id.value, payload) : await vehiculeService.createVehicule(payload)
  await uploadDrafts(saved)
}
async function submitChauffeur() { const payload = { id_user: chauffeurForm.id_user, id_cooperative: chauffeurForm.id_cooperative, numero_permis: chauffeurForm.numero_permis, categorie_permis: chauffeurForm.categorie_permis, date_expiration_permis: chauffeurForm.date_expiration_permis, disponibilite: chauffeurForm.disponibilite, ...(editing.value ? { is_active: chauffeurForm.is_active } : {}) }; if (id.value) await chauffeurService.updateChauffeur(id.value, payload); else await chauffeurService.createChauffeur(payload) }
async function submitMarque() { const payload = { nom: marqueForm.nom, description: marqueForm.description || undefined, ...(editing.value ? { is_active: marqueForm.is_active } : {}) }; if (id.value) await marqueService.updateMarque(id.value, payload); else await marqueService.createMarque(payload) }
async function submitModele() { const payload = { id_marque: modeleForm.id_marque, nom: modeleForm.nom, description: modeleForm.description || undefined, ...(editing.value ? { is_active: modeleForm.is_active } : {}) }; if (id.value) await modeleService.updateModele(id.value, payload); else await modeleService.createModele(payload) }

function validateReferenceSelections() {
  if (section.value === 'vehicules' && (!vehiculeForm.id_modele || !vehiculeForm.id_cooperative)) {
    throw new Error('Sélectionnez un modèle et une coopérative avant de continuer.')
  }
  if (section.value === 'chauffeurs' && (!chauffeurForm.id_user || !chauffeurForm.id_cooperative)) {
    throw new Error('Sélectionnez un utilisateur et une coopérative avant de continuer.')
  }
  if (section.value === 'modeles' && !modeleForm.id_marque) {
    throw new Error('Sélectionnez une marque avant de continuer.')
  }
}

async function submit() {
  if (submitting.value) return
  submitting.value = true; error.value = ''
  try {
    validateReferenceSelections()
    if (section.value === 'vehicules') await submitVehicule()
    if (section.value === 'chauffeurs') await submitChauffeur()
    if (section.value === 'marques') await submitMarque()
    if (section.value === 'modeles') await submitModele()
    await router.push({ path: listPath.value, query: { success: editing.value ? 'Élément modifié avec succès.' : 'Élément créé avec succès.' } })
  } catch (e: any) { showError(e, e instanceof Error ? e.message : 'Enregistrement impossible.') }
  finally { submitting.value = false }
}

onMounted(async () => { try { await loadReferences(); await loadItem(); if (section.value === 'vehicules') addDocumentDraft() } catch (e: any) { showError(e, 'Impossible de charger les données du formulaire.') } finally { loading.value = false } })
</script>

<template>
  <AppLayout>
    <template #title>{{ title }}</template>
    <div class="page-intro"><div><p class="eyebrow">GESTION DE LA FLOTTE</p><h2>{{ title }}</h2><p>Renseignez les informations puis enregistrez.</p></div><RouterLink class="secondary-button" :to="listPath">Retour à la liste</RouterLink></div>
    <BaseCard><p v-if="loading" class="status-msg">Chargement des données en cours…</p><p v-else-if="error && !documentDrafts.length" class="error-banner">{{ error }}</p><form v-else class="management-form form-page" @submit.prevent="submit">
      <template v-if="section === 'vehicules'">
        <div class="field-group"><label for="vehicle-registration">Immatriculation <span>*</span></label><input id="vehicle-registration" v-model="vehiculeForm.immatriculation" required placeholder="Ex. 1234 TAA" /></div>
        <div class="field-group"><label for="vehicle-model">Modèle <span>*</span></label><select id="vehicle-model" v-model.number="vehiculeForm.id_modele" required><option :value="0" disabled>Choisir un modèle</option><option v-for="item in modeles" :key="item.id" :value="item.id">{{ item.nom }}</option></select></div>
        <div class="field-group"><label for="vehicle-brand">Marque</label><input id="vehicle-brand" :value="selectedVehicleBrand?.nom || 'Sélectionnez d’abord un modèle'" class="readonly-field" readonly /></div>
        <div class="field-group"><label for="vehicle-cooperative">Coopérative <span>*</span></label><select id="vehicle-cooperative" v-model.number="vehiculeForm.id_cooperative" required><option :value="0" disabled>Choisir une coopérative</option><option v-for="item in cooperatives" :key="item.id" :value="item.id">{{ item.nom }}</option></select></div>
        <div class="field-group"><label for="vehicle-seats">Nombre de places <span>*</span></label><input id="vehicle-seats" v-model.number="vehiculeForm.nombre_places" type="number" min="1" required /></div>
        <div class="field-group"><label for="vehicle-horsepower">Puissance (CV)</label><input id="vehicle-horsepower" v-model.number="vehiculeForm.chevaux" type="number" min="1" placeholder="Optionnel" /></div>
        <div class="field-group"><label for="vehicle-state">État</label><select id="vehicle-state" v-model="vehiculeForm.etat"><option value="BON_ETAT">Bon état</option><option value="MOYEN">Moyen</option><option value="A_REPARER">À réparer</option><option value="HORS_SERVICE">Hors service</option></select></div>
        <label class="check-field"><input v-model="vehiculeForm.disponibilite" type="checkbox" /> Disponible</label><label v-if="editing" class="check-field"><input v-model="vehiculeForm.is_active" type="checkbox" /> Actif</label>
        <div class="field-group field-wide"><label for="vehicle-description">Description</label><textarea id="vehicle-description" v-model="vehiculeForm.description" placeholder="Informations complémentaires"></textarea></div>
        <div class="detail-subsection field-wide vehicle-documents-form"><div class="card-heading"><div><h3>Documents du véhicule</h3><p>Ajoutez un ou plusieurs fichiers lors de l'enregistrement.</p></div><button class="secondary-button compact-button" type="button" @click="addDocumentDraft">+ Ajouter un document</button></div>
          <div v-for="draft in documentDrafts" :key="draft.key" class="document-draft"><div class="field-group"><label>Type</label><select v-model="draft.type_document"><option value="CARTE_GRISE">Carte grise</option><option value="ASSURANCE">Assurance</option><option value="VISITE_TECHNIQUE">Visite technique</option></select></div><div class="field-group"><label>Numéro</label><input v-model="draft.numero_document" placeholder="CG-001" /></div><div class="field-group"><label>Délivrance</label><input v-model="draft.date_delivrance" type="date" /></div><div class="field-group"><label>Expiration</label><input v-model="draft.date_expiration" type="date" /></div><div class="field-group field-wide"><label>Fichier <span>*</span></label><input type="file" accept=".pdf,.png,.jpg,.jpeg,.gif,.webp,.doc,.docx,.xls,.xlsx" @change="onDraftFileChange(draft, $event)" /><span class="field-hint">PDF, image, Word ou Excel — 10 Mo maximum.</span></div><label class="check-field"><input v-model="draft.is_valid" type="checkbox" /> Document valide</label><button v-if="documentDrafts.length > 1" class="table-action danger-action" type="button" @click="removeDocumentDraft(draft.key)">Retirer</button></div>
        </div>
        <div v-if="editing && existingDocuments.length" class="detail-subsection field-wide"><h3>Documents déjà rattachés</h3><div class="detail-list"><div v-for="document in existingDocuments" :key="document.id" class="detail-list-row"><strong>{{ documentTypeLabel(document.type_document) }}</strong><span>N° {{ document.numero_document || '—' }} · Expire le {{ formatDocumentDate(document.date_expiration) }}</span><a v-if="document.fichier_path" class="table-action table-link" :href="getDocumentUrl(document.fichier_path)" target="_blank" rel="noopener">Ouvrir</a></div></div><span class="field-hint">Pour modifier ou supprimer un document existant, utilisez la fiche détail du véhicule.</span></div>
      </template>
      <template v-else-if="section === 'chauffeurs'"><div class="field-group"><label for="driver-user">Utilisateur <span>*</span></label><select id="driver-user" v-model.number="chauffeurForm.id_user" :disabled="editing" required><option :value="0" disabled>Choisir un utilisateur</option><option v-for="item in users" :key="item.id" :value="item.id">{{ item.first_name }} {{ item.name }} — #{{ item.id }}</option></select></div><div class="field-group"><label for="driver-cooperative">Coopérative <span>*</span></label><select id="driver-cooperative" v-model.number="chauffeurForm.id_cooperative" required><option :value="0" disabled>Choisir une coopérative</option><option v-for="item in cooperatives" :key="item.id" :value="item.id">{{ item.nom }}</option></select></div><div class="field-group"><label for="driver-license">Numéro de permis <span>*</span></label><input id="driver-license" v-model="chauffeurForm.numero_permis" required /></div><div class="field-group"><label for="driver-category">Catégorie <span>*</span></label><input id="driver-category" v-model="chauffeurForm.categorie_permis" required placeholder="Ex. D" /></div><div class="field-group"><label for="driver-expiration">Expiration du permis <span>*</span></label><input id="driver-expiration" v-model="chauffeurForm.date_expiration_permis" type="date" required /></div><label class="check-field"><input v-model="chauffeurForm.disponibilite" type="checkbox" /> Disponible</label><label v-if="editing" class="check-field"><input v-model="chauffeurForm.is_active" type="checkbox" /> Actif</label></template>
      <template v-else-if="section === 'marques'"><div class="field-group"><label for="brand-name">Nom <span>*</span></label><input id="brand-name" v-model="marqueForm.nom" required placeholder="Ex. Toyota" /></div><div class="field-group field-wide"><label for="brand-description">Description</label><textarea id="brand-description" v-model="marqueForm.description" placeholder="Informations complémentaires"></textarea></div><label v-if="editing" class="check-field"><input v-model="marqueForm.is_active" type="checkbox" /> Active</label></template>
      <template v-else><div class="field-group"><label for="model-brand">Marque <span>*</span></label><select id="model-brand" v-model.number="modeleForm.id_marque" required><option :value="0" disabled>Choisir une marque</option><option v-for="item in marques" :key="item.id" :value="item.id">{{ item.nom }}</option></select></div><div class="field-group"><label for="model-name">Nom du modèle <span>*</span></label><input id="model-name" v-model="modeleForm.nom" required placeholder="Ex. Hiace" /></div><div class="field-group field-wide"><label for="model-description">Description</label><textarea id="model-description" v-model="modeleForm.description" placeholder="Informations complémentaires"></textarea></div><label v-if="editing" class="check-field"><input v-model="modeleForm.is_active" type="checkbox" /> Actif</label></template>
      <div class="form-actions"><button class="primary-button compact-button" type="submit" :disabled="submitting">{{ submitting ? 'Enregistrement…' : 'Enregistrer' }}</button><RouterLink class="secondary-button" :to="listPath">Annuler</RouterLink></div>
    </form></BaseCard>
  </AppLayout>
</template>
