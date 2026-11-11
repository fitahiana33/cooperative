# Audit et corrections métier

Référence : `docs/cc`, notamment les sections coopératives, flotte, chauffeurs, départs, réservations, paiements, caisse, embarquement et aide à la décision.

Les contrôles décisifs restent dans l’API et PostgreSQL. Le web et le mobile présentent les mêmes montants et états ; ils ne peuvent pas contourner les validations serveur.

## Corrections

| Domaine | Problème corrigé | Comportement retenu |
| --- | --- | --- |
| Plan des places | Le web appelait une URL absente ; l’API publique ne renvoyait que les places libres. | URL commune aux clients, ancien alias conservé, états libre/réservé/occupé/bloqué visibles sans données personnelles. |
| Disponibilité | Les places bloquées étaient annoncées disponibles. | Elles sont déduites des places vendables et du filtrage par nombre de passagers, sans être comptées comme des voyageurs. |
| Réservation | Une réservation expirée pouvait retrouver un délai en étant modifiée. | Modification refusée après expiration et libération des places. |
| Paiement en cours | Une réservation pouvait être déplacée ou recalculée alors qu’un lien de paiement existait. | Modification refusée pendant la demande de paiement pour préserver le montant et les places associés. |
| Encaissement | Une contrainte limitait chaque réservation à un seul paiement validé. | Plusieurs reçus sont autorisés : acompte puis solde exact. Le total est contrôlé sous verrou ; un encaissement supplémentaire est refusé. |
| Webhook | Un paiement tardif pouvait réactiver une réservation annulée/expirée. | L’argent reçu est tracé et signalé à rembourser, sans réémettre de billet ni reprendre une place revendue. |
| Remboursement | Le remboursement d’une ancienne réservation pouvait libérer une place déjà revendue. | La réservation suivante et sa place restent intactes. |
| Trop-perçu | Rembourser un paiement reçu en surplus pouvait annuler le voyage entièrement payé. | Seul le reçu en surplus est remboursé ; la réservation financée et ses billets restent valides. |
| Idempotence | Une clé de paiement pouvait retourner une demande différente ; plusieurs tentatives partageaient une référence fournisseur. | Clé liée à la réservation et au montant, un seul appel fournisseur par clé, références distinctes par tentative. |
| Expiration du lien | Le lien PAPI pouvait rester payable après la libération des places. | Le délai des places couvre au moins la validité configurée du lien. Un retour tardif reste traité comme remboursement. |
| Caisse | Une caisse d’une autre gare pouvait encaisser si la même coopérative y était présente. | L’encaissement et le remboursement utilisent la gare d’origine du départ. |
| Caisse simultanée | Clôture, opérations et remboursements pouvaient se chevaucher. | Les écritures verrouillent la caisse ; le remboursement verrouille aussi la réservation et le paiement. Un test lance deux remboursements concurrents et vérifie une seule sortie. |
| Espèces | Une dépense ou un remboursement pouvait rendre le solde physique négatif. | Refus si les fonds disponibles sont insuffisants. Le caissier doit disposer des espèces avant la sortie. |
| Soldes clients | L’acompte pouvait être présenté comme un règlement complet, ou une annulation comme un montant encore dû. | Exposition du montant reçu, du reste à régler et du remboursement à traiter. Une réservation annulée/expirée n’affiche plus de solde à encaisser. |
| Embarquement | Un billet issu d’un acompte pouvait être accepté sans règlement du solde. | Contrôle du total réglé avant embarquement, selon la configuration explicite de la gare. |
| Groupes | Après l’embarquement du premier passager, la réservation pouvait encore être annulée ou remboursée. | Annulation/remboursement refusés dès qu’un billet du groupe est utilisé ; contrôle sérialisé avec les scans. |
| Planning | Un départ futur pouvait être pointé comme parti aujourd’hui. | Embarquement/départ physique le jour du voyage ; arrivée après départ. Le chauffeur utilise les mêmes transitions que le backoffice. |
| Contrat de voyage | Un départ réservé pouvait changer de trajet, gare, coopérative, véhicule ou tarif sans traitement des réservations. | Ces remplacements sont refusés tant que des réservations actives existent. Les changements d’horaire restent notifiés. |
| Durée du trajet | Une durée manquante était remplacée implicitement par une heure. | Durée réelle estimée obligatoire avant planification ; vérification des conflits sans limite artificielle de deux jours. |
| Ressources | Une gare, coopérative, destination, véhicule ou un chauffeur pouvait être désactivé malgré ses départs prévus. | Réaffecter ou annuler les départs concernés avant la désactivation ; même protection pour les dates des autorisations et affectations. |
| Historique | Modifier les villes d’un itinéraire utilisé changeait aussi les voyages historiques. | Création d’un nouvel itinéraire requise pour remplacer les villes d’un trajet déjà utilisé. |
| Affectation future | Une affectation valide à une date future était refusée car non active aujourd’hui. | La planification vérifie la période contractuelle et l’absence d’annulation, distinctes de l’activation du jour. |
| Affectation annulée | La maintenance pouvait réactiver une affectation désactivée. | Marqueur d’annulation durable, vérifié par le traitement automatique et les sélecteurs de disponibilité. |
| Flotte | Un véhicule réparé ne pouvait pas retrouver simultanément son bon état et sa disponibilité. | Validation sur l’état demandé, avec maintien des contrôles du planning. |
| Périmètres | Un agent voyait des réservations d’autres gares de la même coopérative ; un chauffeur voyait celles de ses collègues. | Réservations, billets, QR et manifestes limités à la gare de l’agent et aux voyages du chauffeur. Les permissions restent nécessaires. |
| Administrateur | Malgré ses permissions, l’administrateur était exclu de la vente réservée au personnel. | Inclusion explicite dans le personnel, approuvée par l’utilisateur, avec test de vente au guichet. |
| Prévisions | « 7 jours » contenait une seule journée ; la capacité moyenne était pondérée par les réservations et certains voyages sans client étaient omis. | Somme des prévisions journalières sur l’horizon, comptage par départ avant agrégation, journées sans réservation conservées et hypothèse de remplissage identifiée comme indicative. |

## Règles configurables et validation par la gare

Les paramètres existants de délai de réservation, nombre de réservations en attente, nombre de places par réservation, délai d’annulation, acompte et commission ne sont pas des obligations universelles du cahier des charges. Ils doivent être validés par l’exploitant avant mise en production.

`BOARDING_REQUIRES_FULL_PAYMENT=true` impose le règlement du solde avant embarquement. Une gare autorisant explicitement un autre fonctionnement peut désactiver ce contrôle ; les autres validations restent appliquées. La validité du lien est définie par `PAPI_VALID_DURATION_HOURS`.

Une annulation après le début de l’embarquement est refusée par cette version. Une procédure opérationnelle de débarquement, d’incident ou de remplacement avec passagers déjà à bord doit être définie avant d’autoriser ce cas ; elle ne peut pas être assimilée à une annulation ordinaire.

## Migrations et vérifications

- `0037_payment_installments` : retrait de la contrainte empêchant acompte et solde.
- `0038_assignment_cancellation` : distinction des affectations annulées et futures.
- `0039_surplus_refunds` : remboursement d’un trop-perçu sans annulation du voyage financé.
- Tests d’intégration sur une base PostgreSQL dédiée, y compris callbacks signés simulés et remboursements concurrents.
- Tests des projections, des modèles mobiles et de l’affichage des soldes ; compilation TypeScript/Vite et analyse Flutter ciblée.

Vérification locale du 10 novembre 2026 : **137 tests backend réussis** sur PostgreSQL isolé, **7 tests navigateur réussis**, **13 tests Flutter réussis** et compilation web TypeScript/Vite réussie. L'analyse Flutter n'a ni erreur ni avertissement ; 13 informations de style ou de dépréciation préexistantes restent signalées. La migration `0040_operational_reliability` est prête, vérifiée en aller-retour sur une base de test, et n'a pas été appliquée à la base applicative locale. Les tests SMTP et prestataire sont simulés ; aucun email ni paiement réel n'a été envoyé.

Les tests de paiement utilisent des notifications et liens simulés : aucun débit réel n’est effectué. Une recette PAPI avec le compte de test de l’exploitant, les remboursements réels, les procédures exceptionnelles et les appareils mobiles physiques reste nécessaire avant exploitation.
