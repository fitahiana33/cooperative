<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import type { Caisse } from '../../models/finance/model'
import type { Reservation, ReservationStatus } from '../../models/reservation/model'
import { financeService } from '../../services/finance/service'
import { reservationService } from '../../services/reservation/service'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { userError } from '../../utils/errors'

const route = useRoute()
const auth = useAuthenticationStore()
const item = ref<Reservation | null>(null)
const caisses = ref<Caisse[]>([])
const cancelCaisseId = ref<number | null>(null)
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const success = ref('')
const labels: Record<ReservationStatus, string> = {
  EN_ATTENTE: 'En attente', CONFIRMEE: 'Confirmée', PAYEE: 'Payée', ANNULEE: 'Annulée',
  EXPIREE: 'Expirée', EMBARQUEE: 'Embarquée', TERMINEE: 'Terminée',
}
function statusExplanation(status: ReservationStatus) {
  return {
    EN_ATTENTE: 'Votre place est retenue temporairement. Réglez au guichet avant la date d’expiration indiquée.',
    CONFIRMEE: 'La réservation est confirmée et les billets associés sont disponibles dans votre espace.',
    PAYEE: 'Le paiement est confirmé. Vos billets sont disponibles avec leur QR Code.',
    ANNULEE: 'Cette réservation est annulée et les places ont été libérées.',
    EXPIREE: 'Le délai de règlement est dépassé et les places ont été libérées.',
    EMBARQUEE: 'L’embarquement a été enregistré pour cette réservation.',
    TERMINEE: 'Le voyage associé à cette réservation est terminé.',
  }[status]
}

const canUpdate = () => auth.hasPermission('RESERVATION_UPDATE')
const canCancel = () => auth.hasPermission('RESERVATION_CANCEL')
const canProcessRefund = () => auth.hasPermission('PAIEMENT_REFUND')

function showError(value: unknown, fallback: string) { error.value = userError(value, fallback, 'RESERVATION_DETAIL_ERROR'); success.value = '' }
async function loadRefundCaisses() {
  if (!canProcessRefund()) return
  const result = await financeService.caisses({ page: 1, page_size: 100 })
  caisses.value = (result.items || result).filter((caisse: Caisse) => caisse.statut === 'OUVERTE')
}
async function load() {
  try {
    item.value = await reservationService.get(Number(route.params.id))
    if (item.value.statut === 'PAYEE' && canProcessRefund()) await loadRefundCaisses()
  } catch (value: unknown) { showError(value, 'Impossible de charger la réservation.') } finally { loading.value = false }
}
async function change(action: 'confirm' | 'cancel') {
  if (!item.value || busy.value) return
  if (action === 'cancel') {
    const refundNow = item.value.statut === 'PAYEE' && canProcessRefund() && Boolean(cancelCaisseId.value)
    const refundNote = item.value.statut !== 'PAYEE' ? '' : refundNow ? ' Le montant sera remboursé depuis la caisse sélectionnée.' : ' Le remboursement sera à effectuer par un agent de caisse.'
    if (!window.confirm(`Annuler la réservation ${item.value.numero_reservation} ? Les places seront libérées.${refundNote}`)) return
  }
  busy.value = true; error.value = ''
  try {
    item.value = action === 'confirm' ? await reservationService.confirm(item.value.id) : await reservationService.cancel(item.value.id, cancelCaisseId.value || undefined)
    const pendingRefund = action === 'cancel' && !cancelCaisseId.value && item.value.statut === 'ANNULEE'
    success.value = action === 'confirm' ? 'Réservation confirmée et billets générés.' : pendingRefund ? 'Réservation annulée. Le remboursement est en attente au guichet.' : 'Réservation annulée.'
  } catch (value: unknown) { showError(value, 'Opération impossible.') } finally { busy.value = false }
}
onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>Détail réservation</template>
    <div class="page-intro"><div><p class="eyebrow">VENTES & PLACES</p><h2>Détail de la réservation</h2><p>Réservation {{ item?.numero_reservation || `#${route.params.id}` }}</p></div><RouterLink class="secondary-button" to="/reservations">Retour à la liste</RouterLink></div>
    <p v-if="loading" class="status-msg">Chargement…</p><p v-else-if="error" class="error-banner">{{ error }}</p>
    <template v-if="item"><p v-if="success" class="success-banner">{{ success }}</p><BaseCard>
      <div class="card-heading"><div><h2>{{ item.numero_reservation }}</h2><span class="status-badge active">{{ labels[item.statut] || item.statut }}</span></div></div>
      <p class="reservation-status-explanation" :class="`status-${item.statut.toLowerCase()}`">{{ statusExplanation(item.statut) }}</p>
      <div class="detail-grid"><div class="detail-item"><span class="detail-label">Départ</span><strong>#{{ item.id_depart }}</strong></div><div class="detail-item"><span class="detail-label">Date</span><strong>{{ item.depart?.date_depart }} {{ item.depart?.heure_depart?.slice(0, 5) }}</strong></div><div class="detail-item"><span class="detail-label">Montant total</span><strong>{{ item.montant_total }}</strong></div><div class="detail-item"><span class="detail-label">Expiration</span><strong>{{ item.date_expiration ? new Date(item.date_expiration).toLocaleString('fr-FR') : '—' }}</strong></div></div>
      <h3 class="section-title">Places et billets</h3><div class="table-scroll"><table class="data-table"><thead><tr><th>Place</th><th>Passager</th><th>Téléphone</th><th>Billet</th><th>Statut</th></tr></thead><tbody><tr v-for="place in item.places" :key="place.id"><td>{{ place.depart_place?.numero_place || place.id_depart_place }}</td><td>{{ place.nom_passager }}</td><td>{{ place.telephone_passager || '—' }}</td><td>{{ place.billet?.numero_billet || 'Billet non généré' }}</td><td>{{ place.billet?.statut || item.statut }}</td></tr></tbody></table></div>
      <div v-if="item.statut === 'PAYEE' && canProcessRefund()" class="form-grid cancellation-cash"><label class="form-field"><span>Caisse de remboursement *</span><select v-model="cancelCaisseId"><option :value="null">Choisir une caisse ouverte</option><option v-for="caisse in caisses" :key="caisse.id" :value="caisse.id">Gare #{{ caisse.id_gare }} · solde {{ caisse.solde }}</option></select></label></div>
      <p v-if="item.statut === 'PAYEE' && !canProcessRefund()" class="status-msg">Le remboursement doit être traité par un agent habilité à utiliser une caisse.</p>
      <div class="form-actions"><button v-if="canUpdate() && item.statut === 'EN_ATTENTE'" class="primary-button" :disabled="busy" @click="change('confirm')">Confirmer</button><button v-if="canCancel() && !['ANNULEE', 'TERMINEE', 'EMBARQUEE'].includes(item.statut) && true" class="secondary-button danger-action" :disabled="busy" @click="change('cancel')">Annuler</button></div>
    </BaseCard></template>
  </AppLayout>
</template>

<style scoped>.cancellation-cash { max-width: 420px; margin-top: 1rem; }.reservation-status-explanation { margin: 1rem 0; padding: .9rem 1rem; border-left: 3px solid #ef7828; color: #536d81; background: #fff8f1; font-size: .82rem; line-height: 1.5; }.reservation-status-explanation.status-annulee, .reservation-status-explanation.status-expiree { border-left-color: #a43f36; background: #fff0ed; }.reservation-status-explanation.status-confirmee, .reservation-status-explanation.status-payee { border-left-color: #2c7b57; background: #edf9f1; }</style>
