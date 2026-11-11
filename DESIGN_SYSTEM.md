# Refonte des interfaces web — 8 novembre 2026

Références : `docs/cc` et [Un projet de stage qu’on utilise vraiment](https://app.notion.com/p/Un-projet-de-stage-qu-on-utilise-vraiment-336f17a04f4681328e95d3b0edc520d3), consulté dans le navigateur local. Les recommandations du document sont appliquées au périmètre de l’interface ; elles ne constituent pas une certification de mise en production.

## Organisation

| Source | Responsabilité |
| --- | --- |
| `web/src/styles/tokens.css` | Palette, typographies, rayons, ombres et états partagés. |
| `web/src/styles/main.css` | Réinitialisation, utilitaires et structures des modules. Les anciens thèmes successifs ont été retirés. |
| `web/src/styles/workspace.css` | Navigation de gestion, tableaux, formulaires, indicateurs et adaptations aux petits écrans. |
| `web/src/styles/public*.css` | Navigation publique, accueil, recherche, réservation, suivi et espace voyageur. |
| `web/src/styles/auth.css` | Connexion, inscription et réinitialisation. |
| `web/src/components/layout/navigation.ts` | Catalogue des modules, icônes et permissions nécessaires ; source partagée du menu et des repères de navigation. |
| `PublicLayout`, `PublicHeader`, `PublicFooter`, `ClientNavigation`, `AuthLayout` | Structures communes des pages publiques et du compte. |
| `SearchSelect` | Sélection native pour les petites listes ; recherche sans distinction d’accents, liste accessible et clavier au-delà de vingt options. |
| `useSessionFilters` | Mémorisation des filtres départs/réservations dans l’onglet, séparée par utilisateur. |
| `web/public/images/highlands.svg` | Illustration vectorielle originale stockée localement. |

Le routeur, les services API, les modèles et les vues conservent leurs responsabilités. Les contrôles métier et les autorisations restent appliqués par l’API.

## Décisions d’ergonomie

- L’espace de gestion place les tâches quotidiennes avant les référentiels et l’administration. Le menu présente uniquement les modules permis au compte connecté ; il peut être filtré et réduit.
- L’espace public met la recherche au premier plan. Chaque offre distingue l’horaire, le trajet, la gare, la coopérative, les places et le tarif. L’illustration n’affirme pas représenter un lieu réel précis.
- Les actions principales utilisent une couleur commune ; les avertissements et erreurs restent distincts et possèdent un libellé. Les couleurs n’expliquent pas seules un état.
- Titres de page, titre du navigateur et fil d’Ariane donnent le contexte. Les liens directs vers départs, billets, caisse et réservation réduisent les retours au menu.
- Les listes personnelles utilisent la pagination serveur, des compteurs fondés sur le total retourné, une recherche de référence, un filtre de statut et les deux ordres chronologiques. Un échec de chargement ne devient plus un faux compteur nul.
- Les longues listes de référence proposent une recherche. Le nombre d’options visibles est limité et l’utilisateur est invité à préciser son terme. La recherche s’effectue dans le catalogue chargé ; une recherche serveur sera préférable si ce catalogue devient très volumineux.
- La saisie dans une barre de recherche reste possible pendant une requête. La dernière recherche est relancée à la fin de la précédente pour éviter les requêtes simultanées provoquées par le composant.
- Les billets personnels permettent de charger et enregistrer leur véritable QR Code via l’API authentifiée. Les ressources temporaires sont libérées à la fermeture de la page.
- Total, montant reçu, solde restant et remboursement à traiter ont des libellés distincts. Un acompte n’est pas décrit comme un règlement intégral.
- Les informations d’annulation et de confidentialité correspondent maintenant aux bonnes routes. Le texte explique le paiement mobile money et le solde au guichet.

## Statistiques

Le tableau de bord présente les indicateurs opérationnels et les prochains voyages, avec leur date d’actualisation. Les analyses temporelles sont dans la page Statistiques.

Cette page présente trois comparaisons : départs, réservations et remplissage. Une base précédente nulle n’est plus présentée comme une hausse de 100 %. La variation du remplissage est exprimée en points. Le graphique affiche un seul indicateur à la fois, des barres quotidiennes, les unités et les jours sans activité. Les détails restent consultables dans un onglet séparé, avec recherche, tri et pagination.

## Accessibilité et adaptation

Liens d’accès au contenu, intitulés des contrôles, navigation clavier des sélecteurs et onglets, fermeture par Échap, restitution du focus, confinement du focus dans le menu mobile, arrière-plan inerte pendant son ouverture et préférence de réduction des animations sont pris en charge.

Les tableaux larges défilent dans leur propre conteneur. Les formulaires passent à une colonne sur téléphone. Les champs publics gardent une taille de texte adaptée au mobile. Les contrastes des textes secondaires ont été renforcés. Cela ne remplace pas un audit d’accessibilité complet avec technologies d’assistance.

## Recette reproductible

Depuis `web`, `npm run build` vérifie TypeScript et construit la version de production.

Le parcours automatisé principal est `npm run test:e2e`, après `npm ci` et
`npx playwright install chromium`. Les réponses API sont simulées et aucun serveur métier
n'est nécessaire. Les tests couvrent la réservation, la reprise d'un paiement incertain,
la consultation et l'annulation, la recherche distante de véhicules dans le backoffice,
et les pages publiques à 320, 390, 768 et 1440 pixels. Sous Windows, la variable
`PLAYWRIGHT_CHANNEL=msedge` permet d'utiliser Edge installé. La CI lance aussi ces tests.
`web/scripts/booking-qa.cjs` utilise désormais ce même lanceur local.

Le script suivant reste une recette complémentaire avec l'application locale :

Depuis la racine du dépôt, avec l’application locale et Playwright/Edge disponibles :

```text
node web/scripts/design-qa.cjs <chemin-du-module-playwright>
```

Le script vérifie les pages publiques à 320, 390, 768 et 1440 pixels, puis les principaux modules de gestion à 390, 768 et 1440 pixels. Il contrôle aussi les sélecteurs longs, les menus et le clavier, l’espace voyageur, la pagination et le chargement des QR Codes. Le compte administrateur vient de la configuration locale ; aucun secret n’est affiché. Les données passager du scénario sont simulées dans un contexte navigateur séparé. Aucune vente ni aucun paiement réel n’est effectué.

Les captures et autres artefacts de contrôle restent dans `web/build/qa/`, ignoré par Git. Les tests de paiement réel, la recette avec les équipes de gare, les charges de production et les vérifications sur appareils physiques restent des validations distinctes.


## Organisation par tâches — 10 novembre 2026

Les fiches et formulaires chargés sont répartis en sections accessibles depuis des onglets.
La synthèse utile reste visible au-dessus des sections. La barre d'onglets du backoffice
reste sous l'en-tête pendant le défilement ; sa position suit la hauteur réelle de l'en-tête.
Les flèches, Début et Fin permettent la navigation au clavier, et l'onglet sélectionné
reste visible dans une barre étroite. `PageTabPanel` associe les nouveaux panneaux à leurs
onglets par leurs identifiants ARIA et conserve les saisies pendant un changement de section.

- Départ : informations, opérations, incidents.
- Réservation de gestion : voyage, passagers et billets, règlement, opérations autorisées.
- Chauffeur : informations et affectations.
- Formulaire véhicule : identification, caractéristiques et documents. À l'enregistrement,
  un champ invalide provoque l'ouverture de son onglet avant de recevoir le focus.
- Réservation publique : places, coordonnées, règlement et suivi. Une étape est affichée
  à la fois ; les valeurs et les clés de reprise sont conservées. Un résumé compact du
  voyage reste disponible et le pied de page est réduit pendant cette transaction.
- Mobile : réservation en trois étapes ; détail réparti en Voyage, Passagers et Règlement,
  avec l'action de paiement disponible en bas de l'écran.

La hauteur des pages reste libre : aucune taille fixe ne coupe les formulaires ou les
messages sur un petit écran. La répartition réduit les empilements de tâches ; les tableaux
et les contenus longs d'une même section conservent un défilement normal.

Les vérifications couvrent les retours entre étapes, la conservation des saisies, la
validation d'un champ dans un onglet masqué, les panneaux actifs et le clavier. Le contrôle
visuel utilise des données simulées sur téléphone et ordinateur, sans appel aux prestataires.

## Profil connecté

Le profil personnel possède sa propre route, distincte des fiches de gestion des utilisateurs.
`components/account/ProfilePanel.vue` partage les informations, la photo et la sécurité entre
les deux présentations web. Les onglets Informations et Sécurité conservent les saisies.
Le bloc identité est compact sur téléphone ; ses commandes de photo se trouvent dans Informations.
Les avatars de l'en-tête et des fiches utilisent une image chargée avec la session, sans jeton dans
l'URL, et reviennent aux initiales si elle est absente ou indisponible. Le mobile conserve la même
organisation et actualise aussi le compte mémorisé après une modification.
