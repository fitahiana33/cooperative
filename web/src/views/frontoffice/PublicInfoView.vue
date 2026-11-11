<script setup lang="ts">
import PublicLayout from "../../components/layout/PublicLayout.vue";
import { computed } from "vue";
import { RouterLink, useRoute } from "vue-router";

const route = useRoute();

const pages = {
  "travel-conditions": {
    eyebrow: "INFORMATIONS VOYAGE",
    title: "Conditions de voyage",
    intro:
      "Les informations affichées sur cette plateforme servent à préparer votre réservation auprès de la gare et de la coopérative choisies.",
    sections: [
      [
        "Avant le départ",
        "Vérifiez la date, l’heure, la gare et les informations du billet avant de vous présenter. L’heure de présentation dépend des consignes de la gare et doit être confirmée sur votre réservation ou votre billet.",
      ],
      [
        "Réservation",
        "Le programme et la réservation sont accessibles sans compte. Le nom du réservataire suffit ; les noms des autres passagers peuvent être complétés si nécessaire. Une avance doit être payée pour valider la réservation.",
      ],
      [
        "Règlement",
        "Le montant minimum est précisé avant confirmation. Le paiement mobile money est proposé lorsqu’il est activé. Au guichet, le montant restant est encaissé intégralement. Conservez votre référence et respectez le délai de paiement indiqué.",
      ],
    ],
  },
  "cancellation-policy": {
    eyebrow: "INFORMATIONS RÉSERVATION",
    title: "Annulation et modification",
    intro:
      "Les possibilités d’annulation ou de modification dépendent de l’état de la réservation et des règles de la gare ou de la coopérative.",
    sections: [
      [
        "Réservation en attente",
        "Vous pouvez consulter les actions disponibles depuis votre espace client tant que la réservation est en attente. Une réservation non réglée peut expirer selon le délai affiché.",
      ],
      [
        "Réservation confirmée",
        "Pour une réservation confirmée ou réglée, contactez la gare ou la coopérative concernée afin de connaître les conditions applicables et les éventuelles modalités de remboursement.",
      ],
      [
        "Besoin d’aide",
        "Conservez la référence de réservation et le trajet concerné lorsque vous contactez la gare.",
      ],
    ],
  },
  "privacy-policy": {
    eyebrow: "DONNÉES PERSONNELLES",
    title: "Confidentialité",
    intro:
      "Vos données sont utilisées pour créer et suivre votre compte, votre réservation et vos billets.",
    sections: [
      [
        "Données utilisées",
        "La plateforme peut traiter votre identité, vos coordonnées et les informations nécessaires au trajet réservé. Les données saisies pour les passagers servent à préparer le dossier de réservation.",
      ],
      [
        "Accès à vos informations",
        "Vous pouvez consulter et mettre à jour les informations de votre profil depuis Mon espace. Pour toute demande concernant vos données, adressez-vous à l’administrateur de la plateforme ou à la gare concernée.",
      ],
      [
        "Paiement",
        "Le paiement en ligne est traité par le prestataire de mobile money. Ne communiquez jamais votre code secret à la gare ou à un tiers. La plateforme conserve les références nécessaires au suivi de votre paiement.",
      ],
    ],
  },
} as const;

const page = computed(
  () => pages[route.name as keyof typeof pages] || pages["travel-conditions"],
);
</script>

<template>
  <PublicLayout class="public-info-page">
    <section class="public-info-hero">
      <p>{{ page.eyebrow }}</p>
      <h1>{{ page.title }}</h1>
      <span>{{ page.intro }}</span>
    </section>
    <section class="public-info-content">
      <article
        v-for="section in page.sections"
        :key="section[0]"
        class="public-info-card"
      >
        <h2>{{ section[0] }}</h2>
        <p>{{ section[1] }}</p>
      </article>
    </section>
  </PublicLayout>
</template>
