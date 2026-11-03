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
const availablePlaces = computed(() => places.value.filter((item) => item.statut === 'DISPONIBLE'))
const total = computed(() => Number(depart.value?.tarif?.prix || 0) * selected.value.length)
const minimum = computed(() => Math.max(300, Math.ceil(total.value * .25)))
const currency = computed(() => depart.value?.tarif?.devise || 'MGA')
function price(value: number) { return `${value.toLocaleString('fr-FR')} ${currency.value}` }
function date(value?: string) { return value ? new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }).format(new Date(`${value}T00:00:00`)) : '' }
function togglePlace(id: number) { selected.value = selected.value.includes(id) ? selected.value.filter((item) => item !== id) : [...selected.value, id]; if (advance.value < minimum.value) advance.value = minimum.value }
async function load() {
  if (!Number.isInteger(departId) || departId < 1) { error.value = 'Le départ demandé est introuvable.'; loading.value = false; return }
  try { const [departure, available] = await Promise.all([departService.publicGet(departId), reservationService.publicPlaces(departId)]); depart.value = departure; places.value = available }
  catch (value) { console.error('[PUBLIC_BOOKING_ERROR]', value); error.value = 'Ce départ n’est plus disponible à la réservation.' }
  finally { loading.value = false }
}
async function submit() {
  error.value = ''
  if (!selected.value.length) { error.value = 'Sélectionnez au moins une place.'; return }
  if (name.value.trim().length < 2 || phone.value.trim().length < 8) { error.value = 'Renseignez le nom du réservataire et un téléphone valide.'; return }
  if (advance.value < minimum.value || advance.value > total.value) { error.value = `L’avance doit être comprise entre ${price(minimum.value)} et ${price(total.value)}.`; return }
  submitting.value = true
  try {
    const payload: PublicReservationCreate = { id_depart: departId, places: selected.value.map((id) => ({ id_depart_place: id, nom_passager: name.value.trim() })), nom_reservataire: name.value.trim(), telephone_reservataire: phone.value.trim(), email_reservataire: email.value.trim() || undefined, montant_avance: advance.value, fournisseur: provider.value }
    const result = await reservationService.publicCreate(payload)
    localStorage.setItem(`reservation-access:${result.reservation.numero_reservation}`, result.access_token)
    localStorage.setItem(`reservation-payment:${result.payment.reference_paiement}`, JSON.stringify({
      reservationNumber: result.reservation.numero_reservation,
      token: result.access_token,
    }))
    if (result.payment.checkout_url) window.location.assign(result.payment.checkout_url)
    else error.value = 'Le lien de paiement n’a pas été généré. Réessayez.'
  } catch (value: any) { error.value = value?.response?.data?.detail || 'La réservation n’a pas pu être créée. Vérifiez les informations saisies.' }
  finally { submitting.value = false }
}
onMounted(load)
</script>

<template>
  <main class="booking-refactored"><header class="booking-top"><RouterLink class="travel-brand" to="/"><span class="travel-brand-mark">C</span><strong>Coopérative</strong></RouterLink><RouterLink to="/recherche">← Retour aux départs</RouterLink></header><section v-if="loading" class="booking-state">Chargement du départ…</section><section v-else-if="error && !depart" class="booking-state error" role="alert"><strong>{{ error }}</strong><RouterLink class="booking-outline" to="/recherche">Retour aux départs</RouterLink></section><template v-else-if="depart"><section class="booking-heading"><div><p>RÉSERVER UN VOYAGE</p><h1>Préparez votre réservation.</h1><span>Choisissez vos places, renseignez le nom du réservataire et payez l’avance depuis votre mobile.</span></div></section><nav class="booking-steps" aria-label="Étapes de réservation"><span class="active"><b>1</b>Places</span><i></i><span><b>2</b>Coordonnées</span><i></i><span><b>3</b>Paiement</span><i></i><span><b>4</b>Confirmation</span></nav><section class="booking-layout"><div class="booking-main"><article class="booking-card trip-card"><div><p class="booking-kicker">VOTRE TRAJET</p><h2>{{ depart.itineraire?.destination_depart?.nom || 'Départ' }} <em>→</em> {{ depart.itineraire?.destination_arrivee?.nom || 'Destination' }}</h2><span>{{ date(depart.date_depart) }} · départ à <strong>{{ depart.heure_depart?.slice(0, 5) }}</strong></span></div><strong class="trip-total">{{ price(Number(depart.tarif?.prix || 0)) }}<small>par place</small></strong></article><article class="booking-card"><div class="card-heading"><div><p class="booking-kicker">ÉTAPE 1</p><h2>Choisissez vos places</h2></div><span>{{ availablePlaces.length }} disponible(s)</span></div><div class="seat-grid"><button v-for="placeItem in places" :key="placeItem.id" type="button" :class="['seat', { selected: selected.includes(placeItem.id) }]" :disabled="placeItem.statut !== 'DISPONIBLE'" :aria-label="`Place ${placeItem.numero_place}`" :aria-pressed="selected.includes(placeItem.id)" @click="togglePlace(placeItem.id)">{{ placeItem.numero_place }}</button></div><p class="hint">Les places sont retenues pendant le délai de paiement de la réservation.</p></article><article class="booking-card"><div class="card-heading"><div><p class="booking-kicker">ÉTAPE 2</p><h2>Vos coordonnées</h2></div><span>Pas de compte nécessaire</span></div><div class="fields"><label>Nom du réservataire<input v-model="name" autocomplete="name" placeholder="Votre nom complet" required></label><label>Téléphone<input v-model="phone" autocomplete="tel" placeholder="034 00 000 00" required></label><label class="wide">E-mail <small>(facultatif)</small><input v-model="email" type="email" autocomplete="email" placeholder="vous@exemple.com"></label></div><p class="hint">Un seul nom est nécessaire. Les noms des autres passagers restent facultatifs.</p></article><article class="booking-card"><div class="card-heading"><div><p class="booking-kicker">ÉTAPE 3</p><h2>Payez votre avance</h2></div><span>Mobile money sécurisé</span></div><div class="fields"><label>Moyen de paiement<select v-model="provider"><option value="MVOLA">MVola</option><option value="ORANGE_MONEY">Orange Money</option><option value="AIRTEL_MONEY">Airtel Money</option></select></label><label>Montant de l’avance ({{ currency }})<input v-model.number="advance" type="number" :min="minimum" :max="total" step="1" required></label></div><div class="advance-box"><strong>Minimum à payer : {{ price(minimum) }}</strong><span>Total : {{ price(total) }} · Solde éventuel : {{ price(Math.max(0, total - advance)) }}</span></div></article><p v-if="error" class="booking-error" role="alert">{{ error }}</p><button class="booking-submit" type="button" :disabled="submitting || !selected.length" @click="submit">{{ submitting ? 'Préparation du paiement…' : 'Continuer vers le paiement' }} <b>→</b></button></div><aside class="booking-summary"><div class="summary-sticky"><p class="booking-kicker">RÉCAPITULATIF</p><h2>Votre voyage</h2><div class="summary-route"><strong>{{ depart.itineraire?.destination_depart?.nom || 'Départ' }}</strong><b>→</b><strong>{{ depart.itineraire?.destination_arrivee?.nom || 'Destination' }}</strong></div><dl><div><dt>Date</dt><dd>{{ date(depart.date_depart) }}</dd></div><div><dt>Heure</dt><dd>{{ depart.heure_depart?.slice(0, 5) }}</dd></div><div><dt>Places</dt><dd>{{ selected.length || 'Aucune' }}</dd></div><div><dt>Gare</dt><dd>{{ depart.gare?.nom || 'À confirmer' }}</dd></div><div><dt>Coopérative</dt><dd>{{ depart.cooperative?.nom || 'À confirmer' }}</dd></div></dl><div class="summary-price"><span>Total sélectionné</span><strong>{{ price(total) }}</strong></div><div class="summary-trust"><strong>Après le paiement</strong><span>La réservation passe de « en attente » à valide. Le billet et le QR Code sont ensuite générés.</span></div></div></aside></section></template></main>
</template>

<style scoped>
.booking-refactored{min-height:100vh;color:#18324b;background:#f7f9fb;font-family:Inter,system-ui,sans-serif}.booking-top{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.75rem max(1rem,calc((100vw - 1240px)/2));border-bottom:1px solid #e6edf1;background:#fff}.travel-brand{display:inline-flex;align-items:center;gap:.6rem;color:#123452;text-decoration:none}.travel-brand-mark{display:grid;place-items:center;width:2.2rem;height:2.2rem;border-radius:.55rem;color:#fff;background:#ed812e;font-weight:900}.travel-brand strong{font:800 1.05rem Manrope,sans-serif}.booking-top>a:last-child{color:#e87529;font-size:.78rem;font-weight:900;text-decoration:none}.booking-heading{color:#fff;background:linear-gradient(116deg,#092d4c,#125274 65%,#d9772d)}.booking-heading>div{max-width:1180px;margin:auto;padding:3.7rem 1rem 7rem}.booking-heading p{margin:0 0 .6rem;color:#ffc36e;font-size:.68rem;font-weight:900;letter-spacing:.15em}.booking-heading h1{margin:0;font:800 clamp(2.3rem,5vw,4rem)/1.05 Manrope,sans-serif;letter-spacing:-.07em}.booking-heading span{display:block;max-width:610px;margin-top:.9rem;color:#d5e2e9;line-height:1.6}.booking-steps{position:relative;z-index:4;display:flex;align-items:center;gap:.7rem;max-width:780px;margin:-2rem auto 0;padding:1rem 1.3rem;border:1px solid #e1e9ed;border-radius:.6rem;background:#fff;box-shadow:0 14px 35px #18324b18}.booking-steps span{display:flex;align-items:center;gap:.4rem;color:#92a0aa;font-size:.72rem;font-weight:900;white-space:nowrap}.booking-steps span.active{color:#173b59}.booking-steps b{display:grid;place-items:center;width:1.8rem;height:1.8rem;border-radius:50%;color:#84929d;background:#eef2f4}.booking-steps span.active b{color:#fff;background:#ed812e}.booking-steps i{height:1px;flex:1;background:#dfe7eb}.booking-layout{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(270px,.65fr);gap:1rem;max-width:1180px;margin:auto;padding:2rem 1rem 5rem}.booking-main{display:grid;gap:.9rem}.booking-card,.booking-summary{padding:1.25rem;border:1px solid #e1e9ed;border-radius:.6rem;background:#fff;box-shadow:0 8px 22px #18324b08}.trip-card{display:flex;align-items:center;justify-content:space-between;gap:1rem}.booking-kicker{margin:0 0 .5rem;color:#e87529;font-size:.66rem;font-weight:900;letter-spacing:.15em}.trip-card h2,.booking-card h2,.booking-summary h2{margin:0;color:#123452;font:800 1.25rem Manrope,sans-serif}.trip-card h2 em{color:#ed812e;font-style:normal}.trip-card>div>span{display:block;margin-top:.55rem;color:#718494;font-size:.76rem}.trip-total{display:grid;justify-items:end;color:#df6e27;font-size:1.05rem;white-space:nowrap}.trip-total small{margin-top:.25rem;color:#8c9aa3;font-size:.65rem;font-weight:500}.card-heading{display:flex;align-items:start;justify-content:space-between;gap:1rem}.card-heading>span{color:#81909a;font-size:.7rem}.seat-grid{display:grid;grid-template-columns:repeat(6,minmax(38px,1fr));gap:.55rem;margin-top:1.1rem}.seat{min-height:43px;border:1px solid #b9dcc8;border-radius:.35rem;color:#2c7957;background:#eff9f3;font-weight:900;cursor:pointer}.seat.selected,.seat:hover:not(:disabled){border-color:#ed812e;color:#fff;background:#ed812e}.seat:disabled{border-color:#e0e7ea;color:#a5b1b7;background:#f0f3f4;cursor:not-allowed}.hint{margin:.9rem 0 0;color:#718494;font-size:.72rem;line-height:1.5}.fields{display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-top:1rem}.fields label{display:grid;gap:.35rem;color:#536d81;font-size:.72rem;font-weight:900}.fields label.wide{grid-column:1/-1}.fields label small{display:inline;color:#8a98a1;font-size:.65rem;font-weight:500}.fields input,.fields select{min-height:43px;padding:0 .7rem;border:1px solid #d9e3e9;border-radius:.35rem;color:#18324b;background:#fbfcfd;font:inherit}.advance-box{display:grid;gap:.3rem;margin-top:1rem;padding:.8rem;border-left:3px solid #ed812e;color:#718494;background:#fff8f1;font-size:.73rem}.advance-box strong{color:#cb6529}.booking-error{margin:0;padding:.8rem;border-radius:.4rem;color:#a44338;background:#fff0ed;font-size:.76rem}.booking-submit{display:inline-flex;align-items:center;justify-content:center;gap:.6rem;min-height:45px;border:0;border-radius:.4rem;color:#fff;background:#ed812e;font-weight:900;box-shadow:0 8px 18px #ed812e33;cursor:pointer}.booking-submit:disabled{opacity:.55;cursor:wait}.summary-sticky{position:sticky;top:5.5rem}.summary-route{display:flex;align-items:center;justify-content:space-between;gap:.5rem;margin:1.2rem 0;padding:.8rem;border-radius:.4rem;color:#123452;background:#f3f7f8}.summary-route strong{font:800 .9rem Manrope,sans-serif}.summary-route b{color:#ed812e}.booking-summary dl{display:grid;gap:.75rem;margin:0}.booking-summary dl div{display:flex;justify-content:space-between;gap:1rem;border-bottom:1px solid #edf1f3;padding-bottom:.55rem}.booking-summary dt{color:#8a99a2;font-size:.7rem}.booking-summary dd{margin:0;color:#4d6879;font-size:.72rem;font-weight:800;text-align:right}.summary-price{display:flex;justify-content:space-between;gap:1rem;margin-top:1rem;color:#718494;font-size:.75rem}.summary-price strong{color:#df6e27;font-size:1rem}.summary-trust{display:grid;gap:.35rem;margin-top:1.2rem;padding:.8rem;border-radius:.4rem;color:#587181;background:#eef8f2;font-size:.7rem;line-height:1.45}.summary-trust strong{color:#267352}.booking-state{display:grid;place-items:center;gap:1rem;min-height:60vh;color:#718494}.booking-state.error strong{color:#a44338}.booking-outline{padding:.7rem 1rem;border:1px solid #f0a86d;border-radius:.4rem;color:#df702b;font-weight:900;text-decoration:none}@media(max-width:800px){.booking-steps{margin:-2rem .75rem 0;overflow:auto}.booking-steps span{font-size:.65rem}.booking-layout{grid-template-columns:1fr;padding:1.5rem .75rem 4rem}.booking-summary{order:-1}.summary-sticky{position:static}.fields{grid-template-columns:1fr}.fields label.wide{grid-column:auto}}@media(max-width:500px){.booking-top{align-items:flex-start;flex-direction:column}.booking-heading>div{padding:3rem 1rem 6rem}.booking-steps{gap:.45rem;padding:.8rem}.booking-steps i{min-width:10px}.booking-steps span{display:grid;justify-items:center;gap:.25rem}.trip-card{align-items:flex-start;flex-direction:column}.trip-total{justify-items:start}.seat-grid{grid-template-columns:repeat(4,1fr)}}
</style>

<style scoped>
/* Booking typography prioritises form readability and payment clarity. */
.booking-refactored{font-size:16px;line-height:1.5}
.travel-brand strong{font-size:1.125rem}.booking-top>a:last-child{font-size:.875rem}.booking-heading p{font-size:.75rem}
.booking-heading h1{font-size:clamp(2.35rem,4.8vw,4rem)}.booking-heading span{font-size:1.0625rem}.booking-steps span{font-size:.8125rem}
.trip-card h2,.booking-card h2,.booking-summary h2{font-size:1.375rem}.booking-kicker{font-size:.75rem}.trip-card>div>span{font-size:.875rem}
.trip-total{font-size:1.125rem}.trip-total small{font-size:.75rem}.card-heading>span{font-size:.8125rem}.seat{min-height:46px;font-size:.9375rem}
.hint{font-size:.8125rem}.fields label{font-size:.8125rem}.fields label small{font-size:.75rem}.fields input,.fields select{min-height:46px;font-size:1rem}
.advance-box{font-size:.8125rem}.booking-error{font-size:.875rem}.booking-submit{min-height:48px;font-size:.9375rem}.summary-route strong{font-size:1rem}
.booking-summary dt{font-size:.8125rem}.booking-summary dd{font-size:.8125rem}.summary-price{font-size:.875rem}.summary-price strong{font-size:1.125rem}.summary-trust{font-size:.8125rem}
@media(max-width:800px){.booking-steps span{font-size:.75rem}}
@media(max-width:500px){.booking-heading h1{font-size:clamp(2.25rem,10vw,3.25rem)}.booking-heading span{font-size:1rem}.trip-card h2,.booking-card h2,.booking-summary h2{font-size:1.25rem}}
</style>

<style scoped>
/* Keep the booking back link as a clear, accessible navigation action. */
.booking-top{min-height:64px}
.booking-top>a:last-child{display:inline-flex;align-items:center;min-height:44px;padding:0 .75rem;border-radius:.4rem;transition:color .2s,background .2s}
.booking-top>a:last-child:hover,.booking-top>a:last-child:focus-visible{color:#d96825;background:#fff4ea;outline:none}
.booking-top>a:last-child:focus-visible{outline:3px solid #ffc16c;outline-offset:2px}
@media(max-width:500px){.booking-top{min-height:60px;width:100%;padding-top:.55rem;padding-bottom:.55rem}.booking-top>a:last-child{min-height:42px;padding-left:0}}
</style>
