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

Set-Location mobile
flutter pub get
flutter build apk --release --dart-define=MOBILE_API_BASE_URL=https://cooperative-api-3yuz.onrender.com/api/v1

PAPI_ENV=sandbox
PAPI_BASE_URL=https://app.papi.mg/engine/api
ONLINE_PAYMENT_ENABLED=true
PAYMENT_PROVIDER=papi
FRONTEND_URL=https://cooperative-opal.vercel.app
PAPI_API_KEY=replace-with-sandbox-api-key
PAPI_SIGNING_SECRET=replace-with-sandbox-signing-secret
PAPI_NOTIFICATION_URL=https://your-public-api.example.com/api/v1/paiements/webhooks/papi
PAPI_VALID_DURATION_HOURS=1
