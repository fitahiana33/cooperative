<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()

const pages = {
  'conditions-voyage': {
    eyebrow: 'INFORMATIONS VOYAGE',
    title: 'Conditions de voyage',
    intro: 'Les informations affichées sur cette plateforme servent à préparer votre réservation auprès de la gare et de la coopérative choisies.',
    sections: [
      ['Avant le départ', 'Vérifiez la date, l’heure, la gare et les informations du billet avant de vous présenter. L’heure de présentation dépend des consignes de la gare et doit être confirmée sur votre réservation ou votre billet.'],
      ['Réservation', 'Le programme et la réservation sont accessibles sans compte. Le nom du réservataire suffit ; les noms des autres passagers peuvent être complétés si nécessaire. Une avance doit être payée pour valider la réservation.'],
      ['Règlement', 'Le règlement s’effectue au guichet selon les modalités communiquées par la gare. Le délai applicable est celui indiqué sur votre réservation.'],
    ],
  },
  annulation: {
    eyebrow: 'INFORMATIONS RÉSERVATION',
    title: 'Annulation et modification',
    intro: 'Les possibilités d’annulation ou de modification dépendent de l’état de la réservation et des règles de la gare ou de la coopérative.',
    sections: [
      ['Réservation en attente', 'Vous pouvez consulter les actions disponibles depuis votre espace client tant que la réservation est en attente. Une réservation non réglée peut expirer selon le délai affiché.'],
      ['Réservation confirmée', 'Pour une réservation confirmée ou réglée, contactez la gare ou la coopérative concernée afin de connaître les conditions applicables et les éventuelles modalités de remboursement.'],
      ['Besoin d’aide', 'Conservez la référence de réservation et le trajet concerné lorsque vous contactez la gare.'],
    ],
  },
  confidentialite: {
    eyebrow: 'DONNÉES PERSONNELLES',
    title: 'Confidentialité',
    intro: 'Vos données sont utilisées pour créer et suivre votre compte, votre réservation et vos billets.',
    sections: [
      ['Données utilisées', 'La plateforme peut traiter votre identité, vos coordonnées et les informations nécessaires au trajet réservé. Les données saisies pour les passagers servent à préparer le dossier de réservation.'],
      ['Accès à vos informations', 'Vous pouvez consulter et mettre à jour les informations de votre profil depuis Mon espace. Pour toute demande concernant vos données, adressez-vous à l’administrateur de la plateforme ou à la gare concernée.'],
      ['Paiement', 'Le règlement étant effectué au guichet, la plateforme ne demande pas de coordonnées de carte bancaire pour réserver en ligne.'],
    ],
  },
} as const

const page = computed(() => pages[route.name as keyof typeof pages] || pages['conditions-voyage'])
document.title = page.value.title
</script>

<template>
  <main class="public-info-page">
    <header class="public-info-header">
      <RouterLink class="public-info-brand" to="/"><span>C</span><strong>Coopérative</strong></RouterLink>
      <nav aria-label="Navigation informations"><RouterLink to="/">Rechercher un voyage</RouterLink><RouterLink to="/espace-client">Mon espace</RouterLink></nav>
    </header>
    <section class="public-info-hero"><p>{{ page.eyebrow }}</p><h1>{{ page.title }}</h1><span>{{ page.intro }}</span></section>
    <section class="public-info-content">
      <article v-for="section in page.sections" :key="section[0]" class="public-info-card"><h2>{{ section[0] }}</h2><p>{{ section[1] }}</p></article>
    </section>
    <footer class="public-info-footer"><RouterLink to="/">Retour à l’accueil</RouterLink><nav><RouterLink to="/conditions-voyage">Conditions</RouterLink><RouterLink to="/annulation">Annulation</RouterLink><RouterLink to="/confidentialite">Confidentialité</RouterLink></nav></footer>
  </main>
</template>

<style scoped>
.public-info-page { min-height: 100vh; color: #173b59; background: #f7fafc; font-family: Inter, system-ui, sans-serif; }.public-info-header { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 1rem max(1rem, calc((100vw - 1180px) / 2)); border-bottom: 1px solid #dce6ed; background: white; }.public-info-brand { display: inline-flex; align-items: center; gap: .6rem; color: #123452; text-decoration: none; }.public-info-brand span { display: grid; place-items: center; width: 2.2rem; height: 2.2rem; border-radius: .55rem; color: white; background: #e9782a; font-weight: 900; }.public-info-header nav, .public-info-footer nav { display: flex; flex-wrap: wrap; gap: 1rem; }.public-info-header a, .public-info-footer a { color: #e9782a; font-size: .8rem; font-weight: 800; text-decoration: none; }.public-info-hero { padding: 5rem max(1rem, calc((100vw - 900px) / 2)) 3rem; color: white; background: linear-gradient(115deg, #0b2c4b, #164d74); }.public-info-hero p { margin: 0 0 .7rem; color: #ffc270; font-size: .7rem; font-weight: 900; letter-spacing: .15em; }.public-info-hero h1 { margin: 0 0 1rem; font: 800 clamp(2rem, 5vw, 3.6rem)/1.1 Manrope, sans-serif; letter-spacing: -.06em; }.public-info-hero span { display: block; max-width: 720px; color: #d8e4ec; line-height: 1.7; }.public-info-content { display: grid; gap: 1rem; max-width: 900px; margin: auto; padding: 3rem 1rem; }.public-info-card { padding: 1.4rem; border: 1px solid #e1e9ef; border-radius: .7rem; background: white; box-shadow: 0 8px 22px #18324b0b; }.public-info-card h2 { margin: 0 0 .6rem; color: #123452; font-size: 1.1rem; }.public-info-card p { margin: 0; color: #607487; line-height: 1.7; }.public-info-footer { display: flex; justify-content: space-between; gap: 1rem; max-width: 900px; margin: auto; padding: 1rem 1rem 2.5rem; font-size: .8rem; }
@media (max-width: 600px) { .public-info-header, .public-info-footer { align-items: flex-start; flex-direction: column; }.public-info-hero { padding-top: 3.5rem; } }
</style>
