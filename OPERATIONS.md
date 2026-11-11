# Exploitation et reprise des incidents

## Configuration et migration

Les règles actuelles sont configurées côté serveur : `PASSENGER_MAX_SEATS_PER_RESERVATION`,
`PASSENGER_MAX_PENDING_RESERVATIONS`, `RESERVATION_HOLD_MINUTES`, `CANCELLATION_DEADLINE_MINUTES`,
`DEPOSIT_RATE`, `MINIMUM_DEPOSIT_AMOUNT`, `BOARDING_REQUIRES_FULL_PAYMENT` et `DEFAULT_COMMISSION_RATE`.
Valider ces valeurs avec l'exploitant. `/api/v1/reservations/policy` fournit les valeurs appliquées aux clients.
Elles s'appliquent actuellement à l'ensemble de l'installation.

Avant de déployer : sauvegarder PostgreSQL et les fichiers téléversés, vérifier la restauration,
puis exécuter `alembic upgrade head`. La migration `0040_operational_reliability` conserve les données
et ajoute les informations de reprise, les dates financières et le périmètre du journal.
Elle est prête mais n’a pas été appliquée à la base applicative locale, conformément au choix
de conserver la migration pour son application ultérieure.
Les dates financières historiques utilisent le callback enregistré lorsqu'il existe, sinon l'ancienne date.
Les anciennes traces dont le périmètre ne peut pas être retrouvé restent réservées à l'administrateur.

Rattacher chaque responsable à sa gare depuis la gestion du personnel de gare, avec un administrateur.
Un responsable sans rattachement ne reçoit plus d'accès global implicite. Aucun rattachement n'est
deviné lors de la migration des données réelles.

## Déploiement

`compose.production.yml` utilise les Dockerfiles de production, une migration préalable unique,
un contrôle de disponibilité PostgreSQL et des volumes persistants pour la base et les fichiers.
Configurer `DATABASE_URL` avec l'hôte interne `db`, des secrets privés et les URL publiques HTTPS.
Le proxy HTTPS de l'hébergement doit desservir les ports locaux du web et de l'API.

```powershell
docker compose -f compose.production.yml build
docker compose -f compose.production.yml up -d
docker compose -f compose.production.yml run --rm api python -m app.db.seed
```

La dernière commande initialise les permissions et le compte administrateur configuré ; elle ne crée
pas les voyages de démonstration. Aucun déploiement n'est exécuté automatiquement par ce dépôt.
La CI vérifie l'API sur PostgreSQL, la compilation web, les parcours navigateur simulés et Flutter.

## Sauvegardes et restauration

Sauvegarder avec `pg_dump --format=custom --file=<fichier>` en passant les paramètres de connexion
par les variables PostgreSQL de l'environnement. Utiliser `--file` évite les altérations d'un flux
binaire redirigé par certaines versions de PowerShell. Conserver aussi le volume des téléversements.
Restaurer régulièrement une sauvegarde avec `pg_restore --exit-on-error` dans une base distincte de
la production et vérifier réservations, encaissements, remboursements, pièces jointes et droits d'accès.
Consigner la date, la taille, le résultat de restauration et le responsable du contrôle.
La fréquence et la rétention doivent être définies selon les pertes de données acceptables par la gare.

## Réservation et paiement interrompus

La création publique retourne la référence et le code d'accès avant d'appeler le prestataire.
La clé de commande permet de récupérer la même réservation après une réponse perdue.
Le navigateur conserve temporairement la demande dans la session ; les accès publics sont protégés
par un secret stocké sous forme de hash sur le serveur.

Un délai réseau du prestataire n'est pas une preuve d'échec. La demande reste `EN_ATTENTE`,
avec `verification_requise=true`. Une seconde tentative récupère la demande existante.
Dans le backoffice, filtrer les paiements « à vérifier », consulter le compte du prestataire avec
la référence marchande et enregistrer une référence de vérification uniquement si l'absence
d'encaissement est confirmée. La validation du paiement reste issue d'un callback signé.
Un callback signé peut rétablir une réponse d'initialisation perdue ; un paiement tardif sur un voyage
annulé ou expiré est signalé à rembourser sans reprendre les places d'un autre voyageur.

## Remboursements et caisse

Choisir explicitement la méthode :

- Espèces : sortie d'une caisse ouverte de la gare du départ, avec contrôle du solde physique.
- Mobile Money, virement ou carte déjà effectué : enregistrement de la référence externe confirmée,
  sans sortie d'espèces. L'application conserve la preuve ; cette opération ne déclenche pas de virement.

Les rapports conservent l'encaissement initial, puis un mouvement négatif à la date du remboursement.
Les opérations de caisse enregistrent leur auteur. Un trop-perçu remboursé ne doit pas annuler le voyage
qui reste intégralement financé. Une vente au guichet échouée est entièrement annulée par la transaction.

## Panne, remplacement, retard et embarquement

Signaler l'incident dans le détail du départ et consigner les mesures prises avant sa clôture.
Ce journal ajoute des traces ; il ne remplace pas les contrôles de planning ou de paiement.
Avant embarquement, utiliser les fonctions existantes de retard ou d'annulation, puis traiter les
réservations et remboursements associés. Un véhicule utilisé par des réservations actives ne peut
pas être remplacé silencieusement. Après utilisation d'un billet, ne pas simuler une annulation ordinaire :
la procédure de débarquement, de transfert des voyageurs et de responsabilité financière doit être
validée par l'exploitant avant de développer une opération de transfert automatique.

## Notifications et surveillance

Les rappels des départs dans les prochaines 24 heures sont créés par la maintenance, sans doublon
pour un même horaire. Un horaire modifié permet un nouveau rappel.

L'envoi par SMTP des nouvelles notifications est disponible après l'autorisation donnée pour
leur titre et leur message uniquement. Activer `NOTIFICATION_EMAIL_ENABLED=true` et configurer
`SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, les identifiants privés et le mode TLS/SSL du serveur.
Le réglage reste désactivé par défaut ; aucun fichier `.env` local n'est modifié automatiquement.
Le destinataire est l'adresse du compte voyageur actif, ou l'adresse saisie pour la réservation
invitée concernée. Sans adresse, la notification reste disponible dans l'application.
Aucun code d'accès, QR, secret de paiement ou pièce jointe n'est ajouté au message.
Les notifications historiques ne sont pas renvoyées par email. SMS et push ne sont pas implémentés.

La maintenance traite jusqu'à cinq emails par exécution. Les erreurs de transport sont reprises
avec un délai croissant, jusqu'à cinq tentatives ; les adresses invalides sont marquées en échec.
Les champs `delivery_status`, `delivery_attempts`, `next_attempt_at` et `delivery_error` permettent
le suivi. Les erreurs mémorisées restent génériques et ne contiennent pas les secrets SMTP.
Un arrêt après acceptation SMTP et avant validation en base peut provoquer un doublon lors de la
reprise ; le `Message-ID` reste stable, sans garantie de déduplication par le serveur destinataire.
Les tests remplacent le transport SMTP et n'envoient aucun email réel.

Surveiller `/health/ready`, les erreurs de maintenance, les demandes de paiement à vérifier,
les remboursements en attente et les écarts de clôture de caisse. Conserver les logs avec un accès
limité et ne jamais journaliser les secrets, les codes d'accès publics ou les tokens du prestataire.

## Vérifications reproductibles

Le backend exige une URL PostgreSQL de test distincte dont le nom finit par `_test` avant toute
recréation de base. Les scénarios concurrentiels utilisent de vraies connexions PostgreSQL.
Les scénarios préparent désormais leur caisse au lieu de supposer qu'un autre test l'a laissée ouverte.

```powershell
python -B -m pytest -p no:cacheprovider
cd web
npm ci
npx playwright install chromium
npm run test:e2e
```

Sur Windows, `PLAYWRIGHT_CHANNEL=msedge` permet d'utiliser Edge déjà installé. Tous les appels
de paiement des tests navigateur sont simulés. Flutter couvre aussi le respect des autorisations
serveur et une demande de paiement dont le résultat est incertain.
La validation du compte prestataire réel, les appareils physiques et la charge cible de la gare
doivent faire l'objet d'une recette d'exploitation séparée.

## Profil personnel et photos

La migration `0041_user_photo`, après `0040_operational_reliability`, ajoute le champ nullable
`users.photo_version`. Elle reste prête à appliquer sur la base applicative. Avant de démarrer
le backend mis à jour, appliquer `alembic upgrade head` depuis `backend` avec la configuration
de la base cible vérifiée. Les comptes existants gardent leurs initiales tant qu'ils n'ont pas de photo.

Les images sont conservées dans `UPLOADS_DIR/profiles` : conserver ce répertoire dans le volume
persistant et dans les sauvegardes, avec la base de données. Ne pas publier ce répertoire par un
serveur de fichiers statiques. L'API exige la session du propriétaire, ou `USER_READ` pour une
consultation administrative ; seule la personne connectée peut ajouter ou supprimer sa propre photo.

JPEG, PNG et WebP sont acceptés jusqu'à 4 Mo et 10 millions de pixels. Le serveur vérifie le contenu,
réoriente l'image et produit un JPEG de 512 pixels maximum sans métadonnées EXIF/GPS. Le remplacement
et la suppression nettoient l'ancien fichier après validation en base ; un fichier refusé conserve
la photo précédente. Les réponses image sont privées avec `Cache-Control: private, no-store`.

Le profil du personnel est `/profil`, celui des voyageurs `/mon-profil`. La gestion `/users/:id`
reste administrative. Le changement de mot de passe demande le mot de passe actuel puis impose
une reconnexion sur tous les appareils. Les clients ne permettent pas de changer leurs rôles,
leur statut ou leur adresse email dans le profil personnel.
