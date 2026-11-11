# Refonte web et mobile

Référence fonctionnelle : `docs/cc` (cahier des charges présent dans le dépôt).
Référence de parcours : [Taxibrousse](https://taxibrousse.mg/fr/).

## Organisation

- `web/src/views/frontoffice/FrontOffice{Home,Results,Booking}View.vue` : pages publiques actives. Les entrées `RefactoredView` délèguent aux pages canoniques pour conserver la compatibilité des anciens imports.
- `web/src/components/layout/PublicHeader.vue` : navigation publique commune, accès au compte selon le rôle et menu mobile utilisable au clavier.
- `web/src/services/publicCatalog.ts` : chargement paginé de toutes les villes et gares.
- `web/src/utils/travelSearch.ts` : validation commune des dates, villes et nombres de passagers.
- `web/src/styles/workspace.css` : règles communes du backoffice, styles des contrôles et adaptation aux écrans étroits.
- `mobile/lib/core/theme/app_theme.dart` : palette, formulaires et boutons communs. Les couches présentation, repository et API restent séparées.

## Corrections fonctionnelles

| Parcours du cahier des charges | Intervention |
| --- | --- |
| Recherche de voyages | Validation des dates et trajets, date « demain » locale, pagination des résultats web, navigation retour/avance synchronisée avec les critères, protection contre les réponses réseau obsolètes. |
| Consultation des départs | Correction du détail public : les départs suivants d’une même journée étaient refusés par une vérification limitée au premier résultat. Deux tests de non-régression ajoutés. |
| Choix des places | États et sélection accessibles, actualisation des disponibilités après un refus de réservation, protection des contrôles pendant la soumission. |
| Réservation et avance | Coordonnées vérifiées, avance recalée sur le total sélectionné, soumission protégée, conservation du numéro après création et accès au suivi. Si le stockage navigateur échoue, affichage du code à conserver et paiement dans un nouvel onglet. |
| Mobile passager | Accueil remanié, accès rapides aux réservations/billets/profil, navigation inférieure, largeur de lecture limitée sur tablette, inversion des villes fiabilisée, chargement de toutes les destinations et meilleure adaptation des cartes étroites. |
| Backoffice | Palette harmonisée, contrôles tactiles, formulaires et détails adaptatifs, lien d’accès direct au contenu, profil sans contournement du routeur, notifications conditionnées par la permission et suppression du faux indicateur non lu. |
| Sécurité | `production` retiré des environnements de développement : les contrôles des secrets et des liens de réinitialisation s’appliquent désormais en production. |
| Qualité des tests | Charge utile de planification mise à jour avec la gare obligatoire ; tests d’embarquement stabilisés près de minuit. |

Les modifications locales déjà présentes sur le pointage chauffeur, les modèles, le service départ et le routeur ont été conservées.

## Vérifications et limites

- Compilation Vue/TypeScript et build Vite.
- Suite backend : 84 tests réussis sur PostgreSQL dédié, base suffixée `_test`, sans réinitialisation de la base de développement.
- Tests Flutter : 10 scénarios sur les modèles, formats et sélection des sièges.
- Contrôles Edge à 390 px et 1440 px : menu, fermeture par Échap, champs requis, refus du même départ/arrivée, résultats, départ invalide, débordements horizontaux et absence d’erreur JavaScript.
- Formulaire de réservation contrôlé avec API de paiement simulée : places occupées, sélection, avance, création unique et accès au suivi. Aucun débit réel.
- Captures de contrôle dans `web/build/qa/` (artefacts locaux ignorés par Git).
- Connexion au backoffice local et menu mobile vérifiés avec le compte de développement configuré ; styles chargés et indicateurs du tableau de bord contrôlés.

Le paiement réel PAPI, la livraison effective des e-mails et la recette Android/iOS sur appareils physiques restent à vérifier avec leurs environnements respectifs. La recette visuelle authentifiée couvre le tableau de bord administrateur et son menu mobile ; les autres rôles sont couverts par les tests API, pas par une recette visuelle exhaustive. Les modules statistiques, rapports et aide à la décision existants ne sont pas une nouvelle implémentation dans cette refonte.

L’analyse Flutter globale relève des remarques préexistantes dans la gestion des véhicules et l’édition de réservation ; les fichiers modifiés sont analysés séparément. Les règles d’avance et de réservation existantes ont été conservées ; leur validation par la gare reste une étape de recette métier.
