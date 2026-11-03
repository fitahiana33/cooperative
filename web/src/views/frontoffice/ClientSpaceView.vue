<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { reservationService } from '../../services/reservation/service'
import { billetService } from '../../services/billet/service'
import type { Reservation } from '../../models/reservation/model'

const auth = useAuthenticationStore()
const router = useRouter()
const reservationCount = ref(0)
const billetCount = ref(0)
const nextReservation = ref<Reservation | null>(null)
const pendingReservation = ref<Reservation | null>(null)
const mobileMenuOpen = ref(false)

async function logout() {
  await auth.logout()
  await router.push({ name: 'frontoffice' })
}
onMounted(async () => {
  const [reservations, billets] = await Promise.allSettled([
    reservationService.list({ page: 1, page_size: 20, sort_by: 'date_depart', sort_order: 'asc' }),
    billetService.list({ page: 1, page_size: 1 }),
  ])
  if (reservations.status === 'fulfilled') {
    reservationCount.value = reservations.value.total || 0
    const reservationsList = reservations.value.items || []
    pendingReservation.value = reservationsList.find((item: Reservation) => item.statut === 'EN_ATTENTE') || null
    nextReservation.value = reservationsList.find((item: Reservation) => !['ANNULEE', 'EXPIREE', 'TERMINEE'].includes(item.statut)) || null
  }
  if (billets.status === 'fulfilled') billetCount.value = billets.value.total || 0
})
</script>

<template>
  <main class="client-space-page">
    <header class="client-header"><RouterLink class="client-brand" to="/"><span class="client-brand-mark">C</span><span>Coopérative</span></RouterLink><nav class="client-desktop-nav"><RouterLink to="/">Rechercher un voyage</RouterLink><RouterLink to="/mes-reservations">Mes réservations</RouterLink><RouterLink to="/mes-billets">Mes billets</RouterLink></nav><div class="client-header-actions"><button class="client-menu-toggle" type="button" :aria-label="mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'" :aria-expanded="mobileMenuOpen" @click="mobileMenuOpen = !mobileMenuOpen">☰</button><button class="client-logout" type="button" @click="logout">Déconnexion</button></div></header>
    <nav v-if="mobileMenuOpen" class="client-mobile-nav" aria-label="Menu mobile"><RouterLink to="/" @click="mobileMenuOpen = false">Rechercher un voyage</RouterLink><RouterLink to="/mes-reservations" @click="mobileMenuOpen = false">Mes réservations</RouterLink><RouterLink to="/mes-billets" @click="mobileMenuOpen = false">Mes billets</RouterLink><RouterLink to="/mon-profil" @click="mobileMenuOpen = false">Mon profil</RouterLink></nav>
    <section class="client-welcome"><p class="client-kicker">ESPACE PASSAGER</p><h1>Bonjour {{ auth.user?.first_name || auth.user?.name }}.</h1><p>Retrouvez vos réservations, vos billets et vos informations personnelles au même endroit.</p></section>
    <section class="client-content"><div class="client-section-title"><div><p class="client-kicker">MON ESPACE</p><h2>Que souhaitez-vous faire ?</h2></div><RouterLink class="client-outline" to="/recherche">Rechercher un voyage</RouterLink></div><div class="client-cards"><RouterLink class="client-card client-card-primary" to="/mes-reservations"><span class="client-card-icon">01</span><strong>Mes réservations</strong><span>Suivez l’état de vos demandes et retrouvez les informations de chaque trajet.</span><b>{{ reservationCount }} réservation(s) →</b></RouterLink><RouterLink class="client-card" to="/mes-billets"><span class="client-card-icon">02</span><strong>Mes billets</strong><span>Accédez à vos billets disponibles et à vos QR Codes pour l’embarquement.</span><b>{{ billetCount }} billet(s) →</b></RouterLink><RouterLink class="client-card" to="/mon-profil"><span class="client-card-icon">03</span><strong>Mon profil</strong><span>Modifiez votre nom, votre téléphone, votre adresse et votre mot de passe.</span><b>Gérer mon profil →</b></RouterLink></div></section>
    <section class="client-steps"><p class="client-kicker">COMMENT ÇA MARCHE ?</p><h2>De la recherche au billet</h2><div><article><b>1</b><strong>Choisissez votre départ</strong><span>Comparez les horaires, les prix, les gares et les places disponibles.</span></article><article><b>2</b><strong>Réservez vos places</strong><span>Indiquez le nom de la personne qui réserve. Les autres noms sont facultatifs.</span></article><article><b>3</b><strong>Payez l’avance</strong><span>La réservation reste en attente jusqu’à la confirmation du paiement de l’avance.</span></article><article><b>4</b><strong>Recevez votre billet</strong><span>Après confirmation, le billet et son QR Code sont disponibles dans votre espace.</span></article></div></section>
    <footer class="client-footer"><span>Besoin d’aide ? Consultez les <RouterLink to="/#aide">questions fréquentes</RouterLink>.</span><button type="button" @click="logout">Se déconnecter</button></footer>
  </main>
</template>

<style scoped>
.client-space-page { min-height: 100vh; color: #18324b; background: #f4f7fb; font-family: Inter, system-ui, sans-serif; }.client-header { display: flex; align-items: center; gap: 2rem; padding: .85rem max(1rem, calc((100vw - 1240px) / 2)); border-bottom: 1px solid #e4ecf2; background: #fff; }.client-brand { display: inline-flex; align-items: center; gap: .6rem; color: #0d2b4f; font-weight: 800; text-decoration: none; }.client-brand-mark { display: grid; place-items: center; width: 2.15rem; height: 2.15rem; border-radius: .55rem; color: white; background: #ef8d2f; }.client-header nav { display: flex; gap: 1.2rem; margin-left: auto; }.client-header nav a, .client-logout, .client-footer button { border: 0; color: #607487; background: none; font-size: .78rem; font-weight: 800; text-decoration: none; cursor: pointer; }.client-header nav a:hover, .client-logout:hover { color: #e9782a; }.client-welcome { padding: 4rem max(1rem, calc((100vw - 1180px) / 2)); color: white; background: linear-gradient(115deg, #0b2c4b, #164d74 70%, #d8752e); }.client-kicker { margin: 0 0 .55rem; color: #e9782a; font-size: .7rem; font-weight: 900; letter-spacing: .15em; }.client-welcome .client-kicker { color: #ffc270; }.client-welcome h1 { margin: 0; font: 800 clamp(2.1rem, 4vw, 3.4rem)/1.1 Manrope, sans-serif; letter-spacing: -.06em; }.client-welcome p:last-child { max-width: 650px; color: #d8e4ec; line-height: 1.6; }.client-content, .client-steps { max-width: 1180px; margin: auto; padding: 3.5rem 1rem 1rem; }.client-section-title { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }.client-section-title h2, .client-steps h2 { margin: 0; color: #123452; font: 800 1.8rem Manrope, sans-serif; letter-spacing: -.05em; }.client-outline { min-height: 40px; padding: .7rem 1rem; border: 1px solid #ef7828; border-radius: .4rem; color: #e9782a; font-size: .78rem; font-weight: 800; text-decoration: none; }.client-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1.5rem; }.client-card { display: grid; gap: .7rem; min-height: 210px; padding: 1.3rem; border: 1px solid #e1e9ef; border-radius: .7rem; color: #18324b; background: white; box-shadow: 0 10px 25px #18324b0b; text-decoration: none; }.client-card:hover { border-color: #efb17d; transform: translateY(-2px); }.client-card-primary { border-top: 3px solid #ef7828; }.client-card-icon { color: #e9782a; font-size: .75rem; font-weight: 900; }.client-card strong { color: #123452; font: 800 1.1rem Manrope, sans-serif; }.client-card span:not(.client-card-icon) { color: #718596; font-size: .8rem; line-height: 1.5; }.client-card b { margin-top: auto; color: #e9782a; font-size: .78rem; }.client-steps { padding-top: 4.5rem; }.client-steps > div { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 1.4rem; }.client-steps article { display: grid; gap: .5rem; padding: 1rem 0; border-top: 2px solid #ef7828; }.client-steps article b { color: #ef7828; }.client-steps article strong { color: #123452; font-size: .9rem; }.client-steps article span { color: #718596; font-size: .76rem; line-height: 1.5; }.client-footer { display: flex; justify-content: space-between; max-width: 1180px; margin: 4rem auto 0; padding: 1.5rem 1rem 2rem; border-top: 1px solid #dce6ed; color: #718596; font-size: .78rem; }.client-footer a, .client-footer button { color: #e9782a; font-weight: 800; text-decoration: none; }
@media (max-width: 800px) { .client-desktop-nav { display: none; }.client-header { justify-content: space-between; }.client-header-actions { display: flex; align-items: center; gap: .5rem; }.client-menu-toggle { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 0 .6rem; border: 1px solid #dce6ed; border-radius: .4rem; color: #123452; background: white; font-size: 1.1rem; }.client-cards, .client-steps > div { grid-template-columns: 1fr 1fr; }.client-section-title { align-items: start; flex-direction: column; } }.client-header-actions { display: flex; align-items: center; gap: .5rem; }.client-menu-toggle { display: none; }.client-mobile-nav { display: none; }.client-outline { display: inline-flex; align-items: center; }.client-footer { margin-right: 1rem; margin-left: 1rem; }
@media (max-width: 560px) { .client-welcome { padding: 3rem 1rem; }.client-content, .client-steps { padding-right: 1rem; padding-left: 1rem; }.client-cards, .client-steps > div { grid-template-columns: 1fr; }.client-footer { align-items: start; flex-direction: column; gap: .8rem; } }
@media (max-width: 800px) { .client-menu-toggle { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 0 .6rem; border: 1px solid #dce6ed; border-radius: .4rem; color: #123452; background: white; font-size: 1.1rem; }.client-mobile-nav { display: grid; gap: .2rem; padding: .7rem 1rem; border-bottom: 1px solid #e4ecf2; background: white; }.client-mobile-nav a { padding: .65rem .45rem; color: #18324b; font-size: .82rem; font-weight: 800; text-decoration: none; } }
</style>
