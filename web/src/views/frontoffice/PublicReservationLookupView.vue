<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { reservationService } from '../../services/reservation/service'
import type { Reservation, ReservationStatus } from '../../models/reservation/model'

const route = useRoute()
const number = ref('')
const token = ref('')
const reservation = ref<Reservation | null>(null)
const loading = ref(false)
const error = ref('')
const storageWarning = ref('')

const statusLabels: Record<ReservationStatus, string> = {
  EN_ATTENTE: 'Paiement en attente',
  CONFIRMEE: 'Confirmée',
  PAYEE: 'Acompte payé',
  ANNULEE: 'Annulée',
  EXPIREE: 'Expirée',
  EMBARQUEE: 'Embarquée',
  TERMINEE: 'Terminée',
}

function statusLabel(status: ReservationStatus) {
  return statusLabels[status] || status
}

function formatDate(value?: string) {
  return value
    ? new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })
      .format(new Date(`${value}T00:00:00`))
    : 'Date à confirmer'
}

function routeLabel(item: Reservation) {
  return `${item.depart?.itineraire?.destination_depart?.nom || 'Départ'} → ${item.depart?.itineraire?.destination_arrivee?.nom || 'Destination'}`
}

function readPaymentReference(reference: string): { reservationNumber: string; token: string } | null {
  try {
    const stored = localStorage.getItem(`reservation-payment:${reference}`)
    if (stored) {
      const access = JSON.parse(stored) as { reservationNumber?: string; token?: string }
      if (typeof access.reservationNumber === 'string' && typeof access.token === 'string') {
        return { reservationNumber: access.reservationNumber, token: access.token }
      }
    }
  } catch (value) {
    console.error('[PUBLIC_RESERVATION_ACCESS_ERROR]', value)
  }
  return null
}

async function lookup() {
  error.value = ''
  storageWarning.value = ''
  reservation.value = null
  const cleanNumber = number.value.trim()
  const cleanToken = token.value.trim()
  if (!cleanNumber || cleanToken.length < 20) {
    error.value = 'Saisissez le numéro de réservation et le code d’accès conservé après le paiement.'
    return
  }

  loading.value = true
  try {
    reservation.value = await reservationService.publicGet(cleanNumber, cleanToken)
  } catch (value) {
    console.error('[PUBLIC_RESERVATION_LOOKUP_ERROR]', value)
    error.value = 'Réservation introuvable ou code d’accès invalide. Vérifiez les informations puis réessayez.'
    loading.value = false
    return
  }
  try {
    localStorage.setItem(`reservation-access:${cleanNumber}`, cleanToken)
  } catch (value) {
    console.error('[PUBLIC_RESERVATION_STORAGE_ERROR]', value)
    storageWarning.value = 'Réservation retrouvée, mais le code d’accès n’a pas pu être mémorisé dans ce navigateur.'
  }
  loading.value = false
}

onMounted(() => {
  const reference = String(route.query.reference || '')
  if (!reference) return

  const saved = readPaymentReference(reference)
  if (saved) {
    number.value = saved.reservationNumber
    token.value = saved.token
  } else {
    number.value = reference
    try {
      token.value = localStorage.getItem(`reservation-access:${reference}`) || ''
    } catch (value) {
      console.error('[PUBLIC_RESERVATION_STORAGE_READ_ERROR]', value)
      storageWarning.value = 'Entrez manuellement le code d’accès conservé après le paiement.'
    }
  }
  if (token.value) void lookup()
})
</script>

<template>
  <main class="public-lookup-page">
    <header class="public-lookup-header">
      <RouterLink class="lookup-brand" to="/"><span>C</span><strong>Coopérative</strong></RouterLink>
      <RouterLink to="/recherche">Rechercher un voyage</RouterLink>
    </header>
    <section class="public-lookup-hero">
      <p>ESPACE VOYAGEUR</p>
      <h1>Retrouvez votre réservation.</h1>
      <span>Consultez son statut et les informations du trajet, même sans compte.</span>
    </section>
    <section class="public-lookup-content">
      <form class="lookup-card" @submit.prevent="lookup" novalidate>
        <div>
          <p class="lookup-kicker">ACCÈS SÉCURISÉ</p>
          <h2>Consulter une réservation</h2>
          <p>Utilisez le numéro de réservation et le code d’accès de votre réservation. Après un paiement effectué dans ce navigateur, ces informations sont préremplies.</p>
        </div>
        <label>Référence de réservation
          <input v-model="number" autocomplete="off" placeholder="Ex. RES-2026-0001" required>
        </label>
        <label>Code d’accès
          <input v-model="token" type="password" autocomplete="off" placeholder="Votre code d’accès" required>
        </label>
        <p v-if="error" class="lookup-error" role="alert">{{ error }}</p>
        <p v-if="storageWarning" class="lookup-warning" role="status">{{ storageWarning }}</p>
        <button class="lookup-submit" type="submit" :disabled="loading">
          {{ loading ? 'Vérification…' : 'Consulter ma réservation' }}
        </button>
      </form>
      <article v-if="reservation" class="lookup-result">
        <div class="lookup-result-head">
          <div>
            <p class="lookup-kicker">RÉSERVATION {{ reservation.numero_reservation }}</p>
            <h2>{{ routeLabel(reservation) }}</h2>
          </div>
          <span class="lookup-status" :class="reservation.statut.toLowerCase().replace('_', '-')">
            {{ statusLabel(reservation.statut) }}
          </span>
        </div>
        <dl>
          <div><dt>Date et heure</dt><dd>{{ formatDate(reservation.depart?.date_depart) }} · {{ reservation.depart?.heure_depart?.slice(0, 5) || '—' }}</dd></div>
          <div><dt>Places</dt><dd>{{ reservation.places.length }}</dd></div>
          <div><dt>Total</dt><dd>{{ Number(reservation.montant_total).toLocaleString('fr-FR') }} Ar</dd></div>
        </dl>
        <p class="lookup-explanation">
          {{ reservation.statut === 'EN_ATTENTE'
            ? 'Le paiement de l’avance est en attente. La réservation sera confirmée après validation du paiement.'
            : reservation.statut === 'PAYEE'
              ? 'Le paiement de l’avance est confirmé. Contactez la coopérative pour connaître le solde restant éventuel.'
              : 'Le statut affiché correspond à la dernière information reçue.' }}
        </p>
      </article>
    </section>
  </main>
</template>

<style scoped>
.public-lookup-page{min-height:100vh;color:#18324b;background:#f4f7fb;font-family:Inter,system-ui,sans-serif}.public-lookup-header{display:flex;align-items:center;justify-content:space-between;gap:1rem;min-height:64px;padding:.7rem max(1rem,calc((100vw - 1180px)/2));border-bottom:1px solid #e1e9ef;background:#fff}.lookup-brand{display:inline-flex;align-items:center;gap:.6rem;color:#123452;text-decoration:none}.lookup-brand span{display:grid;place-items:center;width:2.2rem;height:2.2rem;border-radius:.55rem;color:#fff;background:#ed812e;font-weight:900}.public-lookup-header>a:last-child{display:inline-flex;align-items:center;min-height:44px;color:#df6e27;font-size:.875rem;font-weight:800;text-decoration:none}.public-lookup-hero{padding:4rem max(1rem,calc((100vw - 1180px)/2)) 6rem;color:#fff;background:linear-gradient(115deg,#0b2c4b,#164d74 70%,#d8752e)}.public-lookup-hero p,.lookup-kicker{margin:0 0 .6rem;color:#ffc270;font-size:.75rem;font-weight:900;letter-spacing:.15em}.public-lookup-hero h1{margin:0;font:800 clamp(2.3rem,5vw,4rem)/1.05 Manrope,sans-serif;letter-spacing:-.07em}.public-lookup-hero span{display:block;margin-top:.8rem;color:#d8e4ec;font-size:1.0625rem}.public-lookup-content{display:grid;grid-template-columns:minmax(0,460px) minmax(0,1fr);gap:1rem;max-width:980px;margin:-3rem auto 0;padding:0 1rem 4rem}.lookup-card,.lookup-result{display:grid;gap:1rem;padding:1.4rem;border:1px solid #e1e9ef;border-radius:.7rem;background:#fff;box-shadow:0 14px 35px #18324b12}.lookup-card h2,.lookup-result h2{margin:0;color:#123452;font:800 1.5rem Manrope,sans-serif}.lookup-card p:not(.lookup-kicker){margin:.5rem 0 0;color:#718596;font-size:.875rem;line-height:1.55}.lookup-card label{display:grid;gap:.35rem;color:#536d81;font-size:.8125rem;font-weight:800}.lookup-card input{min-height:46px;padding:0 .75rem;border:1px solid #d9e3e9;border-radius:.35rem;color:#18324b;background:#fbfcfd;font:inherit}.lookup-submit{min-height:46px;border:0;border-radius:.4rem;color:#fff;background:#ed812e;font-size:.9375rem;font-weight:900;cursor:pointer}.lookup-submit:disabled{opacity:.6}.lookup-error,.lookup-warning{margin:0;padding:.8rem;border-radius:.4rem;color:#a44338;background:#fff0ed;font-size:.8125rem;line-height:1.45}.lookup-warning{color:#725513;background:#fff8df}.lookup-result{align-self:start}.lookup-result-head{display:flex;align-items:start;justify-content:space-between;gap:1rem}.lookup-result-head .lookup-kicker{color:#e9782a}.lookup-status{padding:.4rem .6rem;border-radius:99px;color:#9a5a00;background:#fff2d8;font-size:.75rem;font-weight:900;white-space:nowrap}.lookup-status.payee,.lookup-status.confirmee{color:#16704d;background:#e8f8ef}.lookup-status.annulee,.lookup-status.expiree{color:#a13f36;background:#fff0ed}.lookup-result dl{display:grid;gap:.7rem;margin:0}.lookup-result dl div{display:flex;justify-content:space-between;gap:1rem;padding-bottom:.6rem;border-bottom:1px solid #edf1f4}.lookup-result dt{color:#8a9aa7;font-size:.8125rem}.lookup-result dd{margin:0;color:#18324b;font-size:.875rem;font-weight:800;text-align:right}.lookup-explanation{margin:0;padding:.8rem;border-left:3px solid #ed812e;color:#718596;background:#fff8f1;font-size:.8125rem;line-height:1.5}
@media(max-width:760px){.public-lookup-content{grid-template-columns:1fr;margin-top:-2.5rem;padding-right:.75rem;padding-left:.75rem}.lookup-result-head{align-items:start;flex-direction:column}.public-lookup-header>a:last-child{font-size:.8125rem}.public-lookup-hero{padding-top:3.2rem;padding-bottom:5rem}.public-lookup-hero h1{font-size:clamp(2.25rem,10vw,3.25rem)}}
</style>
