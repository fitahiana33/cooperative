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

Le menu `Administration > Réinitialiser les données` est réservé aux administrateurs. Il supprime les données métier et les utilisateurs non administrateurs, remet les séquences PostgreSQL à zéro et conserve les comptes administrateurs, les rôles, les permissions et leurs associations. L'action exige de saisir `RESET` et ne doit jamais être utilisée sur une base de production.

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
