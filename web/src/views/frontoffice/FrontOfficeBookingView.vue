<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { departService } from '../../services/depart/service'
import { reservationService } from '../../services/reservation/service'
import type { DepartPlace, PublicReservationCreate } from '../../models/reservation/model'
import type { PublicProgramme } from '../../models/depart/model'

const route = useRoute()
const departId = Number(route.query.depart_id)
const depart = ref<PublicProgramme | null>(null)
const places = ref<DepartPlace[]>([])
const selected = ref<number[]>([])
const name = ref('')
const phone = ref('')
const email = ref('')
const provider = ref<PublicReservationCreate['fournisseur']>('MVOLA')
const advance = ref(0)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')

const total = computed(() => Number(depart.value?.tarif?.prix || 0) * selected.value.length)
const minimum = computed(() => Math.max(300, Math.ceil(total.value * 0.25)))
const currency = computed(() => depart.value?.tarif?.devise || 'MGA')
const availablePlaces = computed(() => places.value.filter((place) => place.statut === 'DISPONIBLE'))

function displayPrice(value: number) { return `${value.toLocaleString('fr-FR')} ${currency.value}` }
function displayDate(value?: string) {
  return value ? new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }).format(new Date(`${value}T00:00:00`)) : ''
}
function togglePlace(id: number) {
  selected.value = selected.value.includes(id) ? selected.value.filter((value) => value !== id) : [...selected.value, id]
  if (advance.value < minimum.value) advance.value = minimum.value
}
async function load() {
  if (!Number.isInteger(departId) || departId < 1) { error.value = 'Le départ demandé est introuvable.'; loading.value = false; return }
  try {
    const [departure, available] = await Promise.all([departService.publicGet(departId), reservationService.publicPlaces(departId)])
    depart.value = departure
    places.value = available
  } catch (value) {
    console.error('[PUBLIC_BOOKING_ERROR]', value)
    error.value = 'Ce départ n’est plus disponible à la réservation.'
  } finally { loading.value = false }
}
async function submit() {
  error.value = ''
  if (!selected.value.length) { error.value = 'Sélectionnez au moins une place.'; return }
  if (name.value.trim().length < 2 || phone.value.trim().length < 8) { error.value = 'Renseignez votre nom et un numéro de téléphone valide.'; return }
  if (advance.value < minimum.value || advance.value > total.value) { error.value = `L’avance doit être comprise entre ${displayPrice(minimum.value)} et ${displayPrice(total.value)}.`; return }
  submitting.value = true
  try {
    const payload: PublicReservationCreate = {
      id_depart: departId,
      places: selected.value.map((id) => ({ id_depart_place: id, nom_passager: name.value.trim() })),
      nom_reservataire: name.value.trim(),
      telephone_reservataire: phone.value.trim(),
      email_reservataire: email.value.trim() || undefined,
      montant_avance: advance.value,
      fournisseur: provider.value,
    }
    const result = await reservationService.publicCreate(payload)
    sessionStorage.setItem(`reservation-access:${result.payment.reference_paiement}`, result.access_token)
    if (result.payment.checkout_url) window.location.assign(result.payment.checkout_url)
    else error.value = 'Le lien de paiement n’a pas été généré. Réessayez.'
  } catch (value: any) {
    error.value = value?.response?.data?.detail || 'La réservation n’a pas pu être créée. Vérifiez les informations saisies.'
  } finally { submitting.value = false }
}
onMounted(load)
</script>

<template>
  <main class="booking-page">
    <header class="booking-header"><RouterLink class="booking-brand" to="/"><span>C</span><strong>Coopérative</strong></RouterLink><RouterLink to="/recherche">← Modifier la recherche</RouterLink></header>
    <section v-if="loading" class="booking-state" aria-live="polite">Chargement du départ…</section>
    <section v-else-if="error && !depart" class="booking-state error-state" role="alert"><strong>{{ error }}</strong><RouterLink class="booking-button secondary" to="/recherche">Retour aux départs</RouterLink></section>
    <template v-else-if="depart">
      <section class="booking-hero"><p>RÉSERVATION SANS COMPTE</p><h1>Préparez votre voyage.</h1><span>Choisissez vos places, indiquez vos coordonnées et payez une avance mobile money d’au moins 25 %.</span></section>
      <section class="booking-layout">
        <div class="booking-main">
          <article class="trip-summary"><div><p class="booking-kicker">VOTRE DÉPART</p><h2>{{ depart.itineraire?.destination_depart?.nom }} <span>→</span> {{ depart.itineraire?.destination_arrivee?.nom }}</h2><p>{{ displayDate(depart.date_depart) }} · départ à <strong>{{ depart.heure_depart.slice(0, 5) }}</strong></p></div><strong class="trip-price">{{ displayPrice(Number(depart.tarif?.prix || 0)) }}<small>par place</small></strong></article>
          <article class="booking-card"><div class="booking-card-heading"><div><p class="booking-kicker">ÉTAPE 1</p><h2>Choisissez vos places</h2></div><span>{{ availablePlaces.length }} disponible(s)</span></div><div class="seat-grid"><button v-for="place in places" :key="place.id" type="button" :class="['seat', { selected: selected.includes(place.id) }]" :disabled="place.statut !== 'DISPONIBLE'" :aria-label="`Place ${place.numero_place}`" :aria-pressed="selected.includes(place.id)" @click="togglePlace(place.id)">{{ place.numero_place }}</button></div><p class="booking-help">Les places sélectionnées seront retenues pendant le délai de paiement indiqué sur votre réservation.</p></article>
          <article class="booking-card"><div class="booking-card-heading"><div><p class="booking-kicker">ÉTAPE 2</p><h2>Vos coordonnées</h2></div><span>Pas de compte nécessaire</span></div><div class="booking-fields"><label>Nom du réservataire<input v-model="name" autocomplete="name" required placeholder="Votre nom complet" /></label><label>Téléphone<input v-model="phone" autocomplete="tel" required placeholder="034 00 000 00" /></label><label class="wide">E-mail (facultatif)<input v-model="email" type="email" autocomplete="email" placeholder="vous@exemple.com" /></label></div><p class="booking-help">Un seul nom est nécessaire pour créer la réservation. Les autres passagers peuvent être ajoutés par la gare si besoin.</p></article>
          <article class="booking-card"><div class="booking-card-heading"><div><p class="booking-kicker">ÉTAPE 3</p><h2>Votre avance</h2></div><span>Paiement sécurisé Papi</span></div><div class="payment-fields"><label>Moyen de paiement<select v-model="provider"><option value="MVOLA">MVola</option><option value="ORANGE_MONEY">Orange Money</option><option value="AIRTEL_MONEY">Airtel Money</option></select></label><label>Montant de l’avance ({{ currency }})<input v-model.number="advance" type="number" :min="minimum" :max="total" step="1" required /></label></div><div class="advance-note"><strong>Minimum : {{ displayPrice(minimum) }}</strong><span>Total sélectionné : {{ displayPrice(total) }} · Solde éventuel : {{ displayPrice(Math.max(0, total - advance)) }}</span></div></article>
          <p v-if="error" class="booking-error" role="alert">{{ error }}</p>
          <button class="booking-button primary" type="button" :disabled="submitting || !selected.length" @click="submit">{{ submitting ? 'Préparation du paiement…' : 'Continuer vers le paiement' }} <span>→</span></button>
        </div>
        <aside class="booking-trust"><h2>Après votre réservation</h2><ol><li><b>Réservation en attente</b><span>Vos places sont retenues pendant le délai de paiement.</span></li><li><b>Paiement confirmé</b><span>Papi confirme le paiement mobile money par notification sécurisée.</span></li><li><b>Billet disponible</b><span>Le billet et le QR Code sont générés après confirmation.</span></li></ol><p>Vos informations de réservation et votre code d’accès seront conservés dans votre navigateur pour consulter le résultat du paiement.</p></aside>
      </section>
    </template>
  </main>
</template>

<style scoped>
.booking-page { min-height: 100vh; color: #173b59; background: #f4f7fb; font-family: Inter, system-ui, sans-serif; }.booking-header { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .9rem max(1rem, calc((100vw - 1240px) / 2)); border-bottom: 1px solid #e1e9ef; background: white; }.booking-header a { color: #e9782a; font-size: .8rem; font-weight: 800; text-decoration: none; }.booking-brand { display: inline-flex; align-items: center; gap: .6rem; color: #123452 !important; }.booking-brand span { display: grid; place-items: center; width: 2.2rem; height: 2.2rem; border-radius: .55rem; color: white; background: #ef8d2f; }.booking-hero { padding: 4rem max(1rem, calc((100vw - 1180px) / 2)) 6.5rem; color: white; background: linear-gradient(115deg, #0b2c4b, #164d74 70%, #d8752e); }.booking-hero p, .booking-kicker { margin: 0 0 .55rem; color: #e9782a; font-size: .7rem; font-weight: 900; letter-spacing: .14em; }.booking-hero p { color: #ffc270; }.booking-hero h1 { margin: 0 0 .8rem; font: 800 clamp(2.2rem, 5vw, 4rem)/1.08 Manrope, sans-serif; letter-spacing: -.06em; }.booking-hero span { display: block; max-width: 680px; color: #d6e3ec; line-height: 1.6; }.booking-layout { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(260px, .65fr); gap: 1rem; max-width: 1180px; margin: -3.8rem auto 0; padding: 0 1rem 4rem; }.booking-main { display: grid; gap: 1rem; }.trip-summary, .booking-card, .booking-trust { padding: 1.3rem; border: 1px solid #e1e9ef; border-radius: .7rem; background: white; box-shadow: 0 10px 25px #18324b0b; }.trip-summary { display: flex; justify-content: space-between; gap: 1rem; }.trip-summary h2 { margin: 0; color: #123452; font: 800 1.4rem Manrope, sans-serif; }.trip-summary h2 span { color: #e9782a; }.trip-summary p { margin: .6rem 0 0; color: #718596; font-size: .8rem; }.trip-price { color: #e56822; font-size: 1.1rem; text-align: right; }.trip-price small { display: block; margin-top: .25rem; color: #8192a1; font-size: .68rem; font-weight: 500; }.booking-card-heading { display: flex; justify-content: space-between; align-items: start; gap: 1rem; }.booking-card-heading h2, .booking-trust h2 { margin: 0; color: #123452; font: 800 1.15rem Manrope, sans-serif; }.booking-card-heading > span { color: #7a8d9c; font-size: .72rem; }.booking-kicker { margin-bottom: .4rem; }.seat-grid { display: grid; grid-template-columns: repeat(6, minmax(38px, 1fr)); gap: .6rem; margin-top: 1.2rem; }.seat { min-height: 44px; border: 1px solid #b7dcc8; border-radius: .4rem; color: #287153; background: #effaf3; font-weight: 800; }.seat:hover:not(:disabled), .seat.selected { border-color: #ef7828; color: white; background: #ef7828; }.seat:disabled { border-color: #e1e6ea; color: #a2adb5; background: #f1f4f6; cursor: not-allowed; }.booking-help { margin: 1rem 0 0; color: #718596; font-size: .75rem; line-height: 1.5; }.booking-fields, .payment-fields { display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; margin-top: .9rem; }.booking-fields label, .payment-fields label { display: grid; gap: .35rem; color: #536d81; font-size: .75rem; font-weight: 800; }.booking-fields .wide { grid-column: 1 / -1; }.booking-fields input, .payment-fields input, .payment-fields select { min-height: 44px; padding: 0 .7rem; border: 1px solid #d9e3eb; border-radius: .35rem; color: #18324b; background: white; font: inherit; }.advance-note { display: grid; gap: .3rem; margin-top: 1rem; padding: .75rem; border-left: 3px solid #ef7828; color: #607487; background: #fff8f1; font-size: .76rem; }.advance-note strong { color: #d86521; }.booking-button { display: inline-flex; justify-content: center; align-items: center; gap: .5rem; min-height: 44px; padding: 0 1.1rem; border-radius: .4rem; font-weight: 800; }.booking-button.primary { border: 0; color: white; background: #ef7828; box-shadow: 0 8px 18px #ef782833; }.booking-button.secondary { color: #e9782a; background: white; border: 1px solid #efb17d; }.booking-button:disabled { opacity: .55; cursor: wait; }.booking-error { margin: 0; padding: .8rem; border-radius: .4rem; color: #a43f36; background: #fff0ed; font-size: .8rem; }.booking-trust { align-self: start; }.booking-trust ol { display: grid; gap: 1.1rem; margin: 1.4rem 0; padding-left: 1.5rem; }.booking-trust li { padding-left: .3rem; }.booking-trust b, .booking-trust span { display: block; }.booking-trust b { color: #123452; font-size: .82rem; }.booking-trust span, .booking-trust p { color: #718596; font-size: .75rem; line-height: 1.5; }.booking-trust p { margin: 0; padding-top: 1rem; border-top: 1px solid #edf1f4; }.booking-state { display: grid; justify-items: center; gap: 1rem; min-height: 50vh; place-content: center; padding: 1rem; color: #607487; text-align: center; }.error-state strong { color: #a43f36; }
@media (max-width: 800px) { .booking-layout { grid-template-columns: 1fr; }.booking-trust { order: -1; }.seat-grid { grid-template-columns: repeat(6, 1fr); } }.booking-trust { min-width: 0; }
@media (max-width: 560px) { .booking-header { align-items: flex-start; flex-direction: column; }.booking-hero { padding: 3rem 1rem 5.5rem; }.booking-layout { margin-top: -3rem; padding-right: .75rem; padding-left: .75rem; }.trip-summary { align-items: flex-start; flex-direction: column; }.trip-price { text-align: left; }.booking-fields, .payment-fields { grid-template-columns: 1fr; }.booking-fields .wide { grid-column: auto; }.seat-grid { gap: .35rem; }.seat { min-height: 40px; } }
</style>
