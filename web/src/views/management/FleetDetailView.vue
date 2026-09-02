<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { vehiculeService, getDocumentUrl } from '../../services/vehicule/service'
import { chauffeurService } from '../../services/chauffeur/service'
import { marqueService } from '../../services/marque/service'
import { modeleService } from '../../services/modele/service'
import { cooperativeService } from '../../services/cooperative/service'
import { userService } from '../../services/user/service'
import type { DocumentType, Vehicule, VehiculeDocument } from '../../models/vehicule/model'
import type { Chauffeur } from '../../models/chauffeur/model'
import type { Marque } from '../../models/marque/model'
import type { Modele } from '../../models/modele/model'
import type { Cooperative } from '../../models/cooperative/model'
import type { User } from '../../models/user/model'
import { userError } from '../../utils/errors'

type FleetSection = 'vehicules' | 'chauffeurs' | 'marques' | 'modeles'
const route = useRoute()
const auth = useAuthenticationStore()
const section = computed<FleetSection>(() => ({
  'vehicule-detail': 'vehicules', 'chauffeur-detail': 'chauffeurs',
  'marque-detail': 'marques', 'modele-detail': 'modeles',
}[String(route.name || 'vehicule-detail')] || 'vehicules'))
const id = computed(() => Number(route.params.id))
const listPath = computed(() => `/${section.value}`)
const editPath = computed(() => `/${section.value}/${id.value}/edit`)
const title = computed(() => ({ vehicules: 'Détail du véhicule', chauffeurs: 'Détail du chauffeur', marques: 'Détail de la marque', modeles: 'Détail du modèle' }[section.value]))
const canManageDocuments = computed(() => ['ADMIN', 'RESPONSABLE_COOPERATIVE'].includes(auth.userRole.toUpperCase()))

const vehicule = ref<Vehicule | null>(null)
const chauffeur = ref<Chauffeur | null>(null)
const marque = ref<Marque | null>(null)
const modele = ref<Modele | null>(null)
const marqueModeles = ref<Modele[]>([])
const marques = ref<Marque[]>([])
const cooperatives = ref<Cooperative[]>([])
const users = ref<User[]>([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const documentSubmitting = ref(false)
const documentType = ref<DocumentType>('CARTE_GRISE')
const documentNumber = ref('')
const documentIssueDate = ref('')
const documentExpirationDate = ref('')
const documentIsValid = ref(true)
const documentFile = ref<File | null>(null)

function displayCooperative(value?: number) { return cooperatives.value.find(item => item.id === value)?.nom || `Coopérative #${value || ''}` }
function displayUser(value?: number) { const item = users.value.find(user => user.id === value); return item ? `${item.first_name} ${item.name}`.trim() : `Utilisateur #${value || ''}` }
function displayBrand(value?: number) { return marques.value.find(item => item.id === value)?.nom || `Marque #${value || ''}` }
function formatDate(value?: string | null) { return value ? new Date(value).toLocaleDateString('fr-FR') : '—' }
function documentStatus(document: VehiculeDocument) { if (document.is_expired) return 'Expiré'; if (!document.is_active) return 'Inactif'; if (!document.is_valid) return 'Invalide'; return 'Valide' }
function documentStatusClass(document: VehiculeDocument) { return document.is_expired || !document.is_active || !document.is_valid ? 'inactive' : 'active' }
function documentTypeLabel(type: DocumentType) { return ({ CARTE_GRISE: 'Carte grise', ASSURANCE: 'Assurance', VISITE_TECHNIQUE: 'Visite technique' }[type]) }
function onDocumentFileChange(event: Event) { documentFile.value = (event.target as HTMLInputElement).files?.[0] || null }
function resetDocumentForm() {
  documentNumber.value = ''; documentIssueDate.value = ''; documentExpirationDate.value = ''; documentIsValid.value = true; documentFile.value = null
  const input = document.getElementById('vehicle-document-file') as HTMLInputElement | null
  if (input) input.value = ''
}

async function addVehicleDocument() {
  if (!vehicule.value || !documentFile.value) { error.value = 'Sélectionnez un fichier à rattacher au document.'; return }
  if (documentIssueDate.value && documentExpirationDate.value && documentExpirationDate.value < documentIssueDate.value) { error.value = "La date d'expiration doit être postérieure ou égale à la date de délivrance."; return }
  documentSubmitting.value = true; error.value = ''; success.value = ''
  const data = new FormData()
  data.append('type_document', documentType.value)
  if (documentNumber.value) data.append('numero_document', documentNumber.value)
  if (documentIssueDate.value) data.append('date_delivrance', documentIssueDate.value)
  if (documentExpirationDate.value) data.append('date_expiration', documentExpirationDate.value)
  data.append('is_valid', String(documentIsValid.value)); data.append('file', documentFile.value)
  try {
    const created = await vehiculeService.uploadDocument(vehicule.value.id, data)
    vehicule.value.documents.push(created)
    vehicule.value.documents.sort((a, b) => (a.date_expiration || '9999').localeCompare(b.date_expiration || '9999'))
    resetDocumentForm(); success.value = 'Document ajouté avec succès.'
  } catch (errorValue: unknown) { error.value = userError(errorValue, "Impossible d'ajouter le document.", 'DOCUMENT_ADD_ERROR') }
  finally { documentSubmitting.value = false }
}
async function toggleVehicleDocument(document: VehiculeDocument) { try { Object.assign(document, await vehiculeService.toggleDocument(document.id)); success.value = 'Statut du document mis à jour.' } catch (errorValue: unknown) { error.value = userError(errorValue, 'Impossible de modifier le statut du document.', 'DOCUMENT_TOGGLE_ERROR') } }
async function removeVehicleDocument(document: VehiculeDocument) {
  if (!window.confirm('Supprimer définitivement ce document ?')) return
  try { await vehiculeService.deleteDocument(document.id); if (vehicule.value) vehicule.value.documents = vehicule.value.documents.filter(item => item.id !== document.id); success.value = 'Document supprimé.' }
  catch (errorValue: unknown) { error.value = userError(errorValue, 'Impossible de supprimer le document.', 'DOCUMENT_DELETE_ERROR') }
}

async function loadReferences() {
  const results = await Promise.allSettled([
    marqueService.listMarques({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
    cooperativeService.listCooperatives({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
    userService.list({ page: 1, page_size: 100, sort_by: 'name', sort_order: 'asc' }),
  ])
  if (results[0].status === 'fulfilled') marques.value = results[0].value.items
  if (results[1].status === 'fulfilled') cooperatives.value = results[1].value.items
  if (results[2].status === 'fulfilled') users.value = results[2].value.items
}
async function load() {
  try {
    await loadReferences()
    if (section.value === 'vehicules') { vehicule.value = await vehiculeService.getVehicule(id.value); modele.value = await modeleService.getModele(vehicule.value.id_modele) }
    else if (section.value === 'chauffeurs') chauffeur.value = await chauffeurService.getChauffeur(id.value)
    else if (section.value === 'marques') { marque.value = await marqueService.getMarque(id.value); marqueModeles.value = (await modeleService.listModeles({ page: 1, page_size: 100, id_marque: id.value, sort_by: 'nom', sort_order: 'asc' })).items }
    else modele.value = await modeleService.getModele(id.value)
  } catch (errorValue: unknown) { error.value = userError(errorValue, 'Impossible de charger les détails.', 'DETAIL_LOAD_ERROR') }
  finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>{{ title }}</template>
    <div class="page-intro"><div><p class="eyebrow">GESTION DE LA FLOTTE</p><h2>{{ title }}</h2><p>Consultez les informations détaillées de cet élément.</p></div><div class="form-actions"><RouterLink class="secondary-button" :to="listPath">Retour à la liste</RouterLink><RouterLink v-if="!loading && !error" class="primary-button compact-button" :to="editPath">Modifier</RouterLink></div></div>
    <p v-if="loading" class="status-msg">Chargement des détails en cours…</p>
    <p v-else-if="error && !vehicule" class="error-banner">{{ error }}</p>
    <p v-if="success" class="success-banner">{{ success }}</p><p v-if="error && vehicule" class="error-banner">{{ error }}</p>

    <template v-if="section === 'vehicules' && vehicule">
      <BaseCard><div class="card-heading"><div><h2>{{ vehicule.immatriculation }}</h2><p><span :class="['status-badge', vehicule.is_active ? 'active' : 'inactive']">{{ vehicule.is_active ? 'Actif' : 'Inactif' }}</span></p></div></div><div class="detail-grid"><div class="detail-item"><span class="detail-label">Modèle</span><strong>{{ modele?.nom || '—' }}</strong></div><div class="detail-item"><span class="detail-label">Marque</span><strong>{{ displayBrand(modele?.id_marque) }}</strong></div><div class="detail-item"><span class="detail-label">Propriétaire</span><strong>{{ displayCooperative(vehicule.id_cooperative) }}</strong></div><div class="detail-item"><span class="detail-label">Nombre de places</span><strong>{{ vehicule.nombre_places }}</strong></div><div class="detail-item"><span class="detail-label">Puissance</span><strong>{{ vehicule.chevaux ? `${vehicule.chevaux} CV` : '—' }}</strong></div><div class="detail-item"><span class="detail-label">Disponibilité</span><strong>{{ vehicule.disponibilite ? 'Disponible' : 'Indisponible' }}</strong></div><div class="detail-item"><span class="detail-label">État</span><strong>{{ vehicule.etat }}</strong></div><div class="detail-item"><span class="detail-label">Créé le</span><strong>{{ formatDate(vehicule.created_at) }}</strong></div><div class="detail-item detail-wide"><span class="detail-label">Description</span><strong>{{ vehicule.description || 'Aucune description.' }}</strong></div></div></BaseCard>
      <BaseCard>
        <div class="card-heading"><div><h2>Documents du véhicule</h2><p>Ajoutez plusieurs documents et consultez leur validité.</p></div></div>
        <form v-if="canManageDocuments" class="management-form document-form" @submit.prevent="addVehicleDocument">
          <div class="field-group"><label for="document-type">Type <span>*</span></label><select id="document-type" v-model="documentType"><option value="CARTE_GRISE">Carte grise</option><option value="ASSURANCE">Assurance</option><option value="VISITE_TECHNIQUE">Visite technique</option></select></div>
          <div class="field-group"><label for="document-number">Numéro</label><input id="document-number" v-model="documentNumber" placeholder="CG-001" /></div>
          <div class="field-group"><label for="document-issue">Date de délivrance</label><input id="document-issue" v-model="documentIssueDate" type="date" /></div>
          <div class="field-group"><label for="document-expiration">Date d'expiration</label><input id="document-expiration" v-model="documentExpirationDate" type="date" /></div>
          <div class="field-group field-wide"><label for="vehicle-document-file">Fichier <span>*</span></label><input id="vehicle-document-file" type="file" accept=".pdf,.png,.jpg,.jpeg,.gif,.webp,.doc,.docx,.xls,.xlsx" @change="onDocumentFileChange" /><span class="field-hint">PDF, image, Word ou Excel — 10 Mo maximum.</span></div>
          <label class="check-field field-wide"><input v-model="documentIsValid" type="checkbox" /> Document déclaré valide</label>
          <div class="form-actions"><button class="primary-button compact-button" type="submit" :disabled="documentSubmitting">{{ documentSubmitting ? 'Ajout…' : 'Ajouter le document' }}</button></div>
        </form>
        <div v-if="vehicule.documents.length" class="detail-list document-list">
          <div class="document-list-head"><span>Type</span><span>N° / dates</span><span>Statut</span><span>Actions</span></div>
          <div v-for="document in vehicule.documents" :key="document.id" class="detail-list-row document-row"><strong>{{ documentTypeLabel(document.type_document) }}</strong><span>N° {{ document.numero_document || '—' }}<br />Délivré le {{ formatDate(document.date_delivrance) }}<br />Expire le {{ formatDate(document.date_expiration) }}</span><span :class="['status-badge', documentStatusClass(document)]">{{ documentStatus(document) }}</span><span class="document-actions"><a v-if="document.fichier_path" class="table-action table-link" :href="getDocumentUrl(document.fichier_path)" target="_blank" rel="noopener">Ouvrir</a><button v-if="canManageDocuments" class="table-action" type="button" @click="toggleVehicleDocument(document)">{{ document.is_active ? 'Désactiver' : 'Activer' }}</button><button v-if="canManageDocuments" class="table-action danger-action" type="button" @click="removeVehicleDocument(document)">Supprimer</button></span></div>
        </div>
        <div v-else class="empty-state">Aucun document enregistré.</div>
      </BaseCard>
    </template>

    <BaseCard v-else-if="section === 'chauffeurs' && chauffeur"><div class="card-heading"><div><h2>{{ displayUser(chauffeur.id_user) }}</h2><p><span :class="['status-badge', chauffeur.is_active ? 'active' : 'inactive']">{{ chauffeur.is_active ? 'Actif' : 'Inactif' }}</span></p></div></div><div class="detail-grid"><div class="detail-item"><span class="detail-label">Utilisateur</span><strong>{{ displayUser(chauffeur.id_user) }}</strong></div><div class="detail-item"><span class="detail-label">Coopérative</span><strong>{{ displayCooperative(chauffeur.id_cooperative) }}</strong></div><div class="detail-item"><span class="detail-label">Numéro de permis</span><strong>{{ chauffeur.numero_permis }}</strong></div><div class="detail-item"><span class="detail-label">Catégorie</span><strong>{{ chauffeur.categorie_permis }}</strong></div><div class="detail-item"><span class="detail-label">Expiration du permis</span><strong>{{ formatDate(chauffeur.date_expiration_permis) }}</strong></div><div class="detail-item"><span class="detail-label">Disponibilité</span><strong>{{ chauffeur.disponibilite ? 'Disponible' : 'Indisponible' }}</strong></div></div></BaseCard>
    <BaseCard v-else-if="section === 'marques' && marque"><div class="card-heading"><div><h2>{{ marque.nom }}</h2><p><span :class="['status-badge', marque.is_active ? 'active' : 'inactive']">{{ marque.is_active ? 'Active' : 'Inactive' }}</span></p></div></div><div class="detail-grid"><div class="detail-item"><span class="detail-label">Nom</span><strong>{{ marque.nom }}</strong></div><div class="detail-item"><span class="detail-label">Créée le</span><strong>{{ formatDate(marque.created_at) }}</strong></div><div class="detail-item detail-wide"><span class="detail-label">Description</span><strong>{{ marque.description || 'Aucune description.' }}</strong></div></div><div class="detail-subsection"><h3>Modèles de cette marque</h3><div v-if="marqueModeles.length" class="detail-list"><div v-for="item in marqueModeles" :key="item.id" class="detail-list-row"><strong>{{ item.nom }}</strong><span>{{ item.description || 'Aucune description.' }}</span></div></div><div v-else class="empty-state">Aucun modèle rattaché.</div></div></BaseCard>
    <BaseCard v-else-if="section === 'modeles' && modele"><div class="card-heading"><div><h2>{{ modele.nom }}</h2><p><span :class="['status-badge', modele.is_active ? 'active' : 'inactive']">{{ modele.is_active ? 'Actif' : 'Inactif' }}</span></p></div></div><div class="detail-grid"><div class="detail-item"><span class="detail-label">Nom du modèle</span><strong>{{ modele.nom }}</strong></div><div class="detail-item"><span class="detail-label">Marque</span><strong>{{ displayBrand(modele.id_marque) }}</strong></div><div class="detail-item detail-wide"><span class="detail-label">Description</span><strong>{{ modele.description || 'Aucune description.' }}</strong></div><div class="detail-item"><span class="detail-label">Créé le</span><strong>{{ formatDate(modele.created_at) }}</strong></div></div></BaseCard>
  </AppLayout>
</template>
