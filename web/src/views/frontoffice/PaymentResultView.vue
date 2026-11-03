<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { reservationService } from '../../services/reservation/service'
import type { Reservation } from '../../models/reservation/model'

const route = useRoute()
const reference = String(route.query.reference || '')
const paymentAccess = (() => {
  if (!reference) return null
  try {
    const stored = localStorage.getItem(`reservation-payment:${reference}`)
    return stored ? JSON.parse(stored) as { reservationNumber?: string; token?: string } : null
  } catch (value) {
    console.error('[PAYMENT_ACCESS_ERROR]', value)
    return null
  }
})()
const reservationNumber = paymentAccess?.reservationNumber || reference
const token = paymentAccess?.token
  || (reservationNumber ? localStorage.getItem(`reservation-access:${reservationNumber}`) : '')
  || (reference ? sessionStorage.getItem(`reservation-access:${reference}`) : '')
  || ''
const reservation = ref<Reservation | null>(null)
const loading = ref(true)
const waiting = ref(true)
const error = ref('')
const copied = ref(false)
const copyError = ref('')
let timer: ReturnType<typeof setInterval> | undefined

async function refresh() {
  if (!reference || !token) { error.value = 'Le code d’accès de cette réservation n’est plus disponible dans ce navigateur.'; loading.value = false; waiting.value = false; return }
  try {
    reservation.value = await reservationService.publicGet(reservationNumber, token)
    waiting.value = reservation.value.statut === 'EN_ATTENTE'
    if (!waiting.value && timer) { clearInterval(timer); timer = undefined }
  } catch (value) {
    console.error('[PAYMENT_RESULT_ERROR]', value)
    error.value = 'Le statut du paiement ne peut pas encore être vérifié.'
  } finally { loading.value = false }
}
async function copyAccessCode() {
  copyError.value = ''
  try {
    await navigator.clipboard.writeText(token)
    copied.value = true
  } catch (value) {
    console.error('[PAYMENT_ACCESS_COPY_ERROR]', value)
    copyError.value = 'Copie impossible. Sélectionnez le code pour le copier manuellement.'
  }
}
onMounted(async () => { await refresh(); if (waiting.value) timer = setInterval(refresh, 3000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <main class="payment-result-page"><header><RouterLink class="result-brand" to="/"><span>C</span><strong>Coopérative</strong></RouterLink></header><section class="payment-result-card"><div class="result-icon" :class="{ success: reservation?.statut === 'PAYEE', failure: reservation?.statut === 'ANNULEE' || reservation?.statut === 'EXPIREE' }">{{ reservation?.statut === 'PAYEE' ? '✓' : '…' }}</div><p class="result-kicker">PAIEMENT MOBILE MONEY</p><h1>{{ reservation?.statut === 'PAYEE' ? 'Paiement confirmé' : reservation?.statut === 'ANNULEE' || reservation?.statut === 'EXPIREE' ? 'Réservation non confirmée' : 'Vérification du paiement' }}</h1><p v-if="loading">Nous récupérons le résultat de votre paiement…</p><p v-else-if="error" class="result-error" role="alert">{{ error }}</p><p v-else-if="waiting">Papi a reçu votre demande. Cette page se met à jour automatiquement.</p><p v-else-if="reservation?.statut === 'PAYEE'">L’avance de la réservation <strong>{{ reservation.numero_reservation }}</strong> est confirmée. Consultez la coopérative pour le solde éventuel.</p><p v-else>La réservation {{ reservation?.numero_reservation || reference }} n’est pas confirmée. Vous pouvez contacter la gare.</p><div v-if="reservation" class="result-details"><span>Réservation<strong>{{ reservation.numero_reservation }}</strong></span><span>Total<strong>{{ Number(reservation.montant_total).toLocaleString('fr-FR') }} Ar</strong></span><span>État<strong>{{ reservation.statut }}</strong></span></div><section v-if="reservation && token" class="result-access"><h2>Conservez votre accès</h2><p>Ce code permet de retrouver cette réservation sans compte. Gardez-le privé.</p><label>Code d’accès<input :value="token" readonly aria-label="Code d’accès à la réservation"></label><button class="copy-access" type="button" @click="copyAccessCode">{{ copied ? 'Code copié' : 'Copier le code' }}</button><p v-if="copyError" class="result-error" role="alert">{{ copyError }}</p></section><div class="result-actions"><RouterLink class="result-button primary" :to="{ name: 'public-reservation-lookup', query: { reference } }">Retrouver ma réservation</RouterLink><RouterLink class="result-button secondary" to="/">Retour à l’accueil</RouterLink></div></section></main>
</template>

<style scoped>
.payment-result-page { min-height: 100vh; color: #173b59; background: #f4f7fb; font-family: Inter, system-ui, sans-serif; }.payment-result-page header { padding: 1rem max(1rem, calc((100vw - 1180px) / 2)); border-bottom: 1px solid #e1e9ef; background: white; }.result-brand { display: inline-flex; align-items: center; gap: .6rem; color: #123452; text-decoration: none; }.result-brand span { display: grid; place-items: center; width: 2.2rem; height: 2.2rem; border-radius: .55rem; color: white; background: #ef8d2f; }.payment-result-card { display: grid; justify-items: center; max-width: 620px; margin: 7rem auto; padding: 2.5rem 1.5rem; border: 1px solid #e1e9ef; border-radius: .8rem; background: white; box-shadow: 0 15px 35px #18324b0d; text-align: center; }.result-icon { display: grid; place-items: center; width: 3.5rem; height: 3.5rem; margin-bottom: 1rem; border-radius: 50%; color: #d86521; background: #fff0e4; font-size: 1.5rem; font-weight: 900; }.result-icon.success { color: #2c7b57; background: #eaf8ef; }.result-icon.failure { color: #a43f36; background: #fff0ed; }.result-kicker { margin: 0 0 .5rem; color: #e9782a; font-size: .7rem; font-weight: 900; letter-spacing: .14em; }.payment-result-card h1 { margin: 0; color: #123452; font: 800 clamp(1.8rem, 4vw, 2.8rem) Manrope, sans-serif; letter-spacing: -.05em; }.payment-result-card > p:not(.result-kicker) { max-width: 480px; color: #718596; line-height: 1.6; }.result-error { color: #a43f36 !important; }.result-details { display: flex; flex-wrap: wrap; justify-content: center; gap: 1.2rem; width: 100%; margin: 1rem 0; padding: 1rem 0; border-top: 1px solid #edf1f4; border-bottom: 1px solid #edf1f4; }.result-details span, .result-details strong { display: grid; gap: .25rem; color: #8293a0; font-size: .7rem; }.result-details strong { color: #18324b; font-size: .82rem; }.result-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: .7rem; margin-top: 1rem; }.result-button { min-height: 42px; padding: .7rem 1rem; border-radius: .4rem; font-size: .78rem; font-weight: 800; text-decoration: none; }.result-button.primary { color: white; background: #ef7828; }.result-button.secondary { border: 1px solid #efb17d; color: #e9782a; background: white; }
.result-access { display: grid; gap: .55rem; width: 100%; padding: 1rem; border: 1px solid #e8edf0; border-radius: .5rem; background: #f8fafb; text-align: left; }.result-access h2 { margin: 0; color: #123452; font-size: 1rem; }.result-access p { margin: 0; color: #718596; font-size: .78rem; line-height: 1.5; }.result-access label { display: grid; gap: .35rem; color: #536d81; font-size: .75rem; font-weight: 800; }.result-access input { min-height: 42px; padding: 0 .7rem; border: 1px solid #d9e3e9; border-radius: .35rem; color: #18324b; background: white; font: .8rem ui-monospace, monospace; }.copy-access { min-height: 42px; border: 0; border-radius: .35rem; color: white; background: #164d74; font-size: .8rem; font-weight: 800; cursor: pointer; }
@media (max-width: 600px) { .payment-result-card { margin: 3rem 1rem; padding: 2rem 1rem; } }
</style>
