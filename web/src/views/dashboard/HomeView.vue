<script setup lang="ts">
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import StatCard from '../../components/ui/StatCard.vue'
const stats = [{ label: 'Départs aujourd’hui', value: '—', detail: 'En préparation', icon: '◷', tone: 'stat-blue' }, { label: 'Réservations', value: '—', detail: 'Données à venir', icon: '▤', tone: 'stat-purple' }, { label: 'Coopératives actives', value: '—', detail: 'Module à configurer', icon: '♧', tone: 'stat-orange' }, { label: 'Recettes du jour', value: '—', detail: 'Module à configurer', icon: '◈', tone: 'stat-green' }]
</script>
<template><AppLayout><template #title>Vue d’ensemble</template><section class="page-intro"><div><span class="eyebrow">AUJOURD’HUI</span><h2>Bonjour, bienvenue 👋</h2><p>Voici un aperçu de l’activité de votre gare.</p></div><BaseButton>Télécharger le rapport <span>↓</span></BaseButton></section><section class="stats-grid"><StatCard v-for="stat in stats" :key="stat.label" v-bind="stat" /></section><section class="content-grid"><BaseCard v-for="item in [{ title: 'Prochains départs', description: 'Suivez les départs programmés', icon: '◷', empty: 'Aucun départ enregistré' }, { title: 'Activité récente', description: 'Dernières opérations', icon: '✦', empty: 'Tout est calme' }]" :key="item.title"><div class="card-heading"><div><h2>{{ item.title }}</h2><p>{{ item.description }}</p></div><button class="card-link">Voir tout <span>→</span></button></div><EmptyState :icon="item.icon" :title="item.empty" description="Les informations apparaîtront ici." /></BaseCard></section></AppLayout></template>
