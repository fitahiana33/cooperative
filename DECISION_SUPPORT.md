# Aide à la décision et acompte de réservation

## Couverture du cahier des charges (§ 24)

L’écran `/aide-decision` est réservé aux comptes disposant de `AIDE_DECISION_READ`. Les données sont limitées aux gares et coopératives accessibles au compte. Chaque analyse distingue l’itinéraire, la coopérative et la gare d’origine.

| Besoin | Traitement |
| --- | --- |
| Historique et destinations demandées | Classement des places confirmées, nombre de départs et remplissage observé sur 90 jours. |
| Prévisions passagers et remplissage | Projection de l’activité confirmée sur 7 et 30 jours ; rapport entre la projection à 7 jours et les places effectivement planifiées, hors places bloquées. Un dépassement de 100 % reste visible. |
| Périodes de forte activité | Variations inhabituelles du nombre de places confirmées par journée de service ; comparaison des jours de la prochaine semaine dans les conseils de planning. |
| Nombre de départs | Ajouts à étudier, jour par jour, après déduction de la capacité déjà planifiée, avec un objectif de remplissage de 80 %. Les places déjà retenues constituent un minimum à servir. |
| Horaires | Créneaux historiques classés par remplissage, avec au moins quatre départs observés par créneau. Ces créneaux sont des pistes à examiner, pas une garantie de disponibilité. |
| Anomalies de réservation et recettes | Signalement d’un volume inhabituel (> deux écarts types, au moins 14 journées observées). Les recettes sont les paiements actuellement validés, regroupés par date de validation dans le fuseau de Madagascar. Ce sont des encaissements bruts, pas un résultat net. |

## Conditions et limites

Une projection exige au moins 14 journées de service dans les 30 derniers jours, 28 jours de recul et une activité datant de 14 jours au plus. Sinon, l’interface affiche « données insuffisantes » et ne recommande pas de départ supplémentaire.

Le modèle combine une moyenne pondérée sur les **30 derniers jours calendaires** (65 %) et la saisonnalité hebdomadaire (35 %), calculées sur l’historique disponible de 90 jours. Les journées sans service représentent une activité nulle : elles ne prouvent pas l’absence de demande. Les statuts retenus sont CONFIRMEE, PAYEE, EMBARQUEE et TERMINEE ; les départs annulés sont exclus.

Les réservations, paiements et plannings sont lus dans leur état actuel. Une date de référence passée n’est pas une reconstitution de l’état du système à cette époque. Les fêtes, vacances, recherches sans réservation et refus de vente ne sont pas modélisés. Aucune précision prédictive mesurée sur une exploitation réelle n’est revendiquée. Avant toute décision, confronter les projections aux réalisations et vérifier les ressources dans le planning. Aucun départ n’est créé, annulé ou déplacé par l’analyse.

## Pourcentage d’acompte

- Administration → Paramètres (`/parametres`), accès administrateur uniquement.
- Valeur supérieure à 0 et inférieure ou égale à 100 %, avec deux décimales. La modification est auditée et persistée en base.
- Sans valeur enregistrée, la politique reprend `DEPOSIT_RATE` de la configuration existante.
- Le montant minimum est arrondi à l’ariary supérieur, respecte le plancher configuré et ne dépasse jamais le montant de la réservation.
- Le taux et le plancher sont enregistrés à la création de chaque nouvelle réservation. Les réservations antérieures à la migration conservent le calcul issu de la configuration d’origine ; changer le paramètre administrable ne modifie pas leurs conditions.
- Le paiement en ligne vérifie le minimum enregistré sur la réservation. Après un premier paiement validé, le règlement demandé correspond au solde. Au guichet, le solde est encaissé intégralement.
- Le web et le mobile lisent la même politique publique. Si le minimum augmente entre l’estimation et la création sur le web, le montant est annoncé et une nouvelle action du voyageur est exigée avant de lancer le paiement.

## Déploiement

La migration `0042_booking_settings` doit être appliquée avant de démarrer cette version du backend (`alembic upgrade head`, depuis `backend`). Elle a été vérifiée sur une base PostgreSQL isolée. La base définie dans le fichier local `.env` n’a pas été modifiée.

Les tests vérifient les droits d’accès, les bornes du pourcentage, sa persistance, l’audit, la stabilité des conditions des réservations, les horizons calendaires, les historiques insuffisants et la prise en compte du planning. Les parcours navigateur utilisent une API simulée ; aucun paiement réel n’est envoyé.
