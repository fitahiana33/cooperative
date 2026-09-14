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
