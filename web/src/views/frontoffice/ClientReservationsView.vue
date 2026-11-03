<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { reservationService } from '../../services/reservation/service'
import type { Reservation, ReservationStatus } from '../../models/reservation/model'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { userError } from '../../utils/errors'

const auth = useAuthenticationStore()
const router = useRouter()
const items = ref<Reservation[]>([])
const loading = ref(true)
const error = ref('')

const statusLabels: Record<ReservationStatus, string> = {
  EN_ATTENTE: 'Paiement en attente', CONFIRMEE: 'Confirmée', PAYEE: 'Acompte payé',
  ANNULEE: 'Annulée', EXPIREE: 'Expirée', EMBARQUEE: 'Embarquée', TERMINEE: 'Terminée',
}

function statusClass(status: ReservationStatus) { return status.toLowerCase().replace('_', '-') }
function formatDate(value?: string) { return value ? new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }).format(new Date(`${value}T00:00:00`)) : 'Date à confirmer' }
function routeLabel(item: Reservation) {
  const route = item.depart?.itineraire
  return `${route?.destination_depart?.nom || 'Départ'} → ${route?.destination_arrivee?.nom || 'Destination'}`
}
function seatLabel(item: Reservation) { return item.places.map((place) => place.depart_place?.numero_place || '—').join(', ') || '—' }
async function load() {
  loading.value = true; error.value = ''
  try {
    const result = await reservationService.list({ page: 1, page_size: 50, sort_by: 'date_depart', sort_order: 'asc' })
    items.value = result.items || []
  } catch (value: unknown) { error.value = userError(value, 'Impossible de charger votre activité.', 'CLIENT_RESERVATIONS_ERROR') }
  finally { loading.value = false }
}
async function logout() { await auth.logout(); await router.push({ name: 'frontoffice' }) }
onMounted(load)
</script>

<template>
  <main class="client-activity-page">
    <header class="client-activity-header"><RouterLink class="client-activity-brand" to="/"><span>C</span> Coopérative</RouterLink><nav><RouterLink to="/espace-client">Mon espace</RouterLink><RouterLink class="active" to="/mes-reservations">Mes réservations</RouterLink><RouterLink to="/mes-billets">Mes billets</RouterLink><RouterLink to="/mon-profil">Mon profil</RouterLink></nav><button type="button" @click="logout">Déconnexion</button></header>
    <section class="client-activity-hero"><p>ESPACE PASSAGER</p><h1>Mes réservations</h1><span>Retrouvez vos voyages, leur statut et les places réservées.</span></section>
    <section class="client-activity-content"><div class="client-activity-heading"><div><p class="client-activity-kicker">HISTORIQUE PERSONNEL</p><h2>{{ items.length }} réservation{{ items.length > 1 ? 's' : '' }}</h2></div><RouterLink class="client-activity-primary" to="/recherche">Rechercher un voyage →</RouterLink></div>
      <p v-if="loading" class="client-activity-state">Chargement de vos réservations…</p><p v-else-if="error" class="client-activity-error" role="alert">{{ error }} <button type="button" @click="load">Réessayer</button></p>
      <div v-else-if="items.length" class="client-reservation-list"><article v-for="item in items" :key="item.id" class="client-reservation-card"><div class="client-reservation-top"><span class="client-status" :class="statusClass(item.statut)">{{ statusLabels[item.statut] || item.statut }}</span><strong>{{ item.numero_reservation }}</strong></div><h3>{{ routeLabel(item) }}</h3><p class="client-reservation-date">{{ formatDate(item.depart?.date_depart) }} · départ à {{ item.depart?.heure_depart?.slice(0, 5) || '—' }}</p><div class="client-reservation-meta"><span><small>Places</small><b>{{ seatLabel(item) }}</b></span><span><small>Total</small><b>{{ Number(item.montant_total).toLocaleString('fr-FR') }} Ar</b></span><span><small>Coopérative</small><b>{{ item.depart?.cooperative?.nom || '—' }}</b></span></div><p v-if="item.statut === 'EN_ATTENTE'" class="client-payment-note">La réservation sera valide après le paiement de l’avance minimale.</p><p v-else-if="item.statut === 'PAYEE'" class="client-payment-note success">Votre avance est confirmée. Vos billets sont disponibles dans « Mes billets ».</p></article></div>
      <div v-else class="client-activity-empty"><strong>Vous n’avez encore aucune réservation.</strong><span>Consultez le programme et choisissez votre prochain voyage.</span><RouterLink class="client-activity-primary" to="/recherche">Voir les départs</RouterLink></div>
    </section>
  </main>
</template>

<style scoped>
.client-activity-page{min-height:100vh;color:#18324b;background:#f4f7fb;font-family:Inter,system-ui,sans-serif}.client-activity-header{display:flex;align-items:center;gap:2rem;padding:.85rem max(1rem,calc((100vw - 1240px)/2));border-bottom:1px solid #e4ecf2;background:#fff}.client-activity-brand{display:inline-flex;align-items:center;gap:.6rem;color:#123452;font-weight:900;text-decoration:none}.client-activity-brand span{display:grid;place-items:center;width:2.15rem;height:2.15rem;border-radius:.55rem;color:#fff;background:#ef8d2f}.client-activity-header nav{display:flex;gap:1.1rem;margin-left:auto}.client-activity-header nav a,.client-activity-header button{border:0;color:#607487;background:none;font-size:.78rem;font-weight:800;text-decoration:none;cursor:pointer}.client-activity-header nav a.active,.client-activity-header nav a:hover,.client-activity-header button:hover{color:#e9782a}.client-activity-hero{padding:3.7rem max(1rem,calc((100vw - 1180px)/2));color:#fff;background:linear-gradient(115deg,#0b2c4b,#164d74 70%,#d8752e)}.client-activity-hero p,.client-activity-kicker{margin:0 0 .55rem;color:#ffc270;font-size:.7rem;font-weight:900;letter-spacing:.15em}.client-activity-hero h1{margin:0;font:800 clamp(2rem,4vw,3.25rem)/1.1 Manrope,sans-serif;letter-spacing:-.06em}.client-activity-hero span{display:block;margin-top:.75rem;color:#d8e4ec}.client-activity-content{max-width:1180px;margin:auto;padding:3.2rem 1rem}.client-activity-heading{display:flex;align-items:end;justify-content:space-between;gap:1rem;margin-bottom:1.5rem}.client-activity-heading h2{margin:0;color:#123452;font:800 1.8rem Manrope,sans-serif}.client-activity-kicker{color:#e9782a}.client-activity-primary{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:0 1rem;border-radius:.4rem;color:#fff;background:#ef7828;font-size:.78rem;font-weight:800;text-decoration:none}.client-reservation-list{display:grid;gap:1rem}.client-reservation-card{padding:1.3rem;border:1px solid #e1e9ef;border-radius:.7rem;background:#fff;box-shadow:0 10px 25px #18324b0b}.client-reservation-top{display:flex;justify-content:space-between;gap:1rem;align-items:center}.client-reservation-top strong{color:#7b8b99;font-size:.72rem}.client-status{padding:.35rem .55rem;border-radius:99px;font-size:.68rem;font-weight:900;background:#edf2f6;color:#617486}.client-status.en-attente{color:#9a5a00;background:#fff2d8}.client-status.payee,.client-status.confirmee{color:#16704d;background:#e8f8ef}.client-status.annulee,.client-status.expiree{color:#a13f36;background:#fff0ed}.client-reservation-card h3{margin:1rem 0 .35rem;color:#123452;font:800 1.2rem Manrope,sans-serif}.client-reservation-date{margin:0;color:#63798a;font-size:.82rem}.client-reservation-meta{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:1.2rem;padding-top:1rem;border-top:1px solid #edf1f4}.client-reservation-meta span{display:grid;gap:.25rem}.client-reservation-meta small{color:#8a9aa7;font-size:.68rem}.client-reservation-meta b{color:#18324b;font-size:.82rem}.client-payment-note{margin:1rem 0 0;padding:.75rem;border-left:3px solid #ef7828;color:#8a5a25;background:#fff8f1;font-size:.76rem}.client-payment-note.success{border-color:#27a56e;color:#237252;background:#effaf4}.client-activity-state,.client-activity-empty{display:grid;place-items:center;gap:.6rem;min-height:220px;padding:2rem;border:1px dashed #d7e1e8;border-radius:.7rem;color:#718596;text-align:center}.client-activity-empty strong{color:#18324b}.client-activity-empty .client-activity-primary{margin-top:.5rem}.client-activity-error{padding:1rem;border-radius:.5rem;color:#a43f36;background:#fff0ed}.client-activity-error button{margin-left:.5rem;border:0;color:#a43f36;background:none;font-weight:800;cursor:pointer}@media(max-width:700px){.client-activity-header{justify-content:space-between}.client-activity-header nav{display:none}.client-activity-heading{align-items:start;flex-direction:column}.client-reservation-meta{grid-template-columns:1fr 1fr}}@media(max-width:440px){.client-reservation-meta{grid-template-columns:1fr}.client-activity-content{padding-right:.75rem;padding-left:.75rem}}
</style>
