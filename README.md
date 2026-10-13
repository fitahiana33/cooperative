# Coopérative — socle technique

Application mobile et web de réservation de taxi-brousse et de gestion de gare.

## Architecture

Les clients (`web`, `mobile`) communiquent avec l'API REST FastAPI. Dans le backend, le flux est : `controller (API) → service (règles métier) → repository (accès aux données) → PostgreSQL`.

Les modèles de validation (`schemas`) et les modèles de persistance (`models`) sont séparés afin de limiter le couplage.

## Démarrage Docker

```powershell
docker compose up -d --build
```

Le fichier `.env` contient la configuration et les paramètres sensibles. Il
doit être présent à la racine du projet avant le démarrage et peut être modifié
sans changer le code.

- API et documentation OpenAPI : http://localhost:8000/docs
- Web : http://localhost:5173
- PostgreSQL : localhost:5432

Identifiants administrateur de développement : `admin@cooperative.local` / `Admin123!`. Ils sont configurés par `DEFAULT_ADMIN_EMAIL` et `DEFAULT_ADMIN_PASSWORD` dans `.env` et ne doivent pas être conservés tels quels en production.

Si une ancienne base de développement existe déjà avec l’ancien schéma, supprimer uniquement le volume du projet puis relancer les services : `docker compose down -v` suivi de `docker compose up -d --build`.

Flutter doit être installé localement pour lancer `mobile`. Pour l'émulateur Android, l'URL API par défaut est `http://10.0.2.2:8000/api/v1`; sur un appareil physique, remplacer cette adresse par l'IP de la machine.

## Développement local

Backend : `cd backend; python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --reload`

Web : `cd web; npm install; npm run dev`

Mobile : `cd mobile; flutter pub get; flutter run`

## Parcours de validation rapide

1. Créer ou sélectionner un véhicule avec sa capacité.
2. Créer un départ : le nombre de places est limité par la capacité du véhicule.
3. Dans `Réservations > Nouvelle réservation`, choisir le départ puis les places disponibles.
4. Confirmer la réservation pour générer les billets QR.
5. Ouvrir une caisse et enregistrer le paiement.
6. Vérifier le tableau de bord et les statistiques sur la même période.

Les statistiques distinguent les indicateurs instantanés des tendances : la page Statistiques compare la période choisie à la période précédente et affiche les jours sans activité avec une valeur nulle.

## Réinitialisation des données de développement

Le menu `Administration > Réinitialiser les données` est réservé aux administrateurs et fonctionne uniquement quand `ENVIRONMENT` vaut `development` (ou `dev`, `local`, `test`). Il supprime les données métier et les utilisateurs non administrateurs, remet les séquences PostgreSQL à zéro et conserve les comptes administrateurs, les rôles, les permissions et la liste des sessions révoquées. L'action exige de saisir `RESET` et le mot de passe de l'administrateur.

## Sécurité de la configuration

Hors développement, l'API refuse de démarrer si `SECRET_KEY` est trop courte ou garde une valeur d'exemple, si `DEFAULT_ADMIN_PASSWORD` garde sa valeur par défaut, ou si `DEBUG_RETURN_RESET_URL` est activé. Générer une clé avec `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Les fichiers `.env` ne doivent pas être versionnés : `git rm --cached .env backend/.env web/.env`.

Les documents des véhicules et les QR codes des billets ne sont plus servis publiquement : ils passent par `GET /vehicules/documents/{id}/download` et `GET /billets/{id}/qr.png`, qui exigent une authentification.

## Données de démonstration (seed)

Le script `backend/app/db/seed_dev.py` remplit **toutes les tables** avec un jeu de données cohérent : gares (quais, zones, emplacements), coopératives et membres, destinations, itinéraires et tarifs, marques, modèles, véhicules, documents et chauffeurs, puis environ 200 départs répartis de J-10 à J+7 avec réservations, billets (QR codes générés), paiements, caisses, embarquements et notifications. Les dates sont calculées à partir du jour de lancement : le tableau de bord affiche donc toujours des départs terminés, en cours et à venir.

Les migrations doivent être appliquées (`alembic upgrade head`) avant le premier lancement.

Avec Docker :

```powershell
# Remplir une base vide (refusé si la base contient déjà des données)
docker compose exec backend python -m app.db.seed_dev

# Réinitialiser : vider toutes les tables puis les remplir à nouveau
docker compose exec backend python -m app.db.seed_dev --reset

# Réinitialiser sans données de démonstration (rôles, permissions et admin uniquement)
docker compose exec backend python -m app.db.seed_dev --reset --empty
```

En local, lancer les mêmes commandes depuis `backend` avec l'environnement virtuel activé : `python -m app.db.seed_dev --reset`.

`--reset` vide **toutes** les tables (comptes administrateurs compris), remet les séquences à zéro et supprime les QR codes générés dans `uploads/qr_codes`. Le compte admin est ensuite recréé à partir de `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD`. Le script demande de taper `RESET` ; l'option `--yes` supprime cette confirmation (utile en CI). Il refuse de s'exécuter quand `ENVIRONMENT=production`. L'option `--seed <nombre>` change la graine aléatoire.

Comptes créés, tous avec le mot de passe `Demo123!` :

| Rôle | Identifiants |
| --- | --- |
| Responsable de gare | `responsable.gare1@cooperative.com`, `responsable.gare2@cooperative.com` |
| Agent de gare | `agent.<gare>@cooperative.com` : `ampasampito`, `fasankarana`, `ambodivona`, `toamasina`, `moramanga`, `antsirabe`, `ambositra`, `fianarantsoa`, `mahajanga`, `toliara` |
| Responsable de coopérative | `responsable.fte@`, `responsable.mdt@`, `responsable.smr@`, `responsable.zav@cooperative.com` |
| Chauffeur | `chauffeur01@cooperative.com` à `chauffeur14@cooperative.com` |
| Passager | `passager01@cooperative.com` à `passager25@cooperative.com` |

## Tâches planifiées

L'API exécute chaque minute une maintenance (`app/jobs/maintenance.py`) :

- les réservations non payées dont le délai est dépassé passent à `EXPIREE` et libèrent leurs places ;
- les réservations des départs terminés passent à `TERMINEE`, et les billets non utilisés à `EXPIRE` ;
- les affectations chauffeur–véhicule échues sont clôturées, celles qui commencent sont activées ;
- les jetons révoqués expirés sont purgés.

Un verrou PostgreSQL garantit qu'un seul processus l'exécute à la fois. Pour la lancer depuis un cron plutôt que depuis l'API : `SCHEDULER_ENABLED=false` sur l'API, puis `python -m app.jobs.maintenance`. L'intervalle se règle avec `MAINTENANCE_INTERVAL_SECONDS`.

## Fuseau horaire

Les dates métier (« aujourd'hui », date d'un départ, contrôle d'embarquement) sont calculées dans le fuseau de la gare, `TIMEZONE=Indian/Antananarivo` par défaut, même si le serveur est en UTC.

## Rôles, permissions et agents de gare

`python -m app.db.seed` crée les rôles, les permissions et le compte administrateur manquants. Il est lancé au démarrage du conteneur, avant l'API. Il ne modifie jamais l'existant : un rôle désactivé ou une permission retirée par un administrateur le reste. Pour changer les droits par défaut d'une base existante, écrire une migration Alembic.

Un agent de gare est rattaché à une gare depuis la page de la gare (section « Agents de la gare »). Il voit alors les départs, réservations, billets et caisses des coopératives qui opèrent dans cette gare. Un agent ne peut être rattaché qu'à une seule gare.

## Tests

Les tests du backend s'exécutent sur une vraie base PostgreSQL (les règles métier reposent sur des triggers). La base `<nom>_test` est recréée à chaque lancement, à partir de `DATABASE_URL` ou de `TEST_DATABASE_URL`.

```powershell
docker compose exec backend pip install -r requirements-dev.txt
docker compose exec backend python -m pytest
```

La vérification des types du web : `docker compose exec web npm run typecheck`. L'intégration continue (`.github/workflows/ci.yml`) lance les tests du backend, la vérification des types et le build du web, et `flutter analyze` sur chaque pull request.

## Règles de réservation, d'annulation et de caisse

- **Réservation par un passager :** les places sont retenues `RESERVATION_HOLD_MINUTES` (30 par défaut). La réservation est confirmée et les billets sont émis au paiement au guichet. Un passager a au plus `PASSENGER_MAX_PENDING_RESERVATIONS` réservations en attente et `PASSENGER_MAX_SEATS_PER_RESERVATION` places par réservation.
- **Vente au guichet :** l'agent ou le responsable de gare réserve, confirme et peut encaisser en une seule opération (`POST /reservations/guichet`). En cas d'échec, la réservation est annulée et les places sont libérées.
- **Annulation :** possible jusqu'au départ. Une réservation payée ne peut plus être annulée par le passager moins de `CANCELLATION_DEADLINE_MINUTES` (120) avant le départ. Si la personne qui annule ne peut pas sortir d'argent d'une caisse, le remboursement reste « à effectuer » et apparaît dans `Paiements & caisse` pour un caissier.
- **Clôture de caisse :** le montant compté est saisi ; l'écart avec le solde attendu est enregistré. Seul l'agent qui a ouvert la caisse, ou un responsable, peut la clôturer.
- **Embarquement :** l'agent choisit le départ en cours ; un billet d'un autre départ est refusé. La liste des passagers embarqués et non embarqués s'affiche à l'écran.
- **Changement de mot de passe :** toutes les sessions ouvertes avant le changement sont fermées. Un mot de passe contient au moins 8 caractères, dont des lettres et des chiffres.
