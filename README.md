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

Flutter doit être installé localement pour lancer `mobile`. Pour l'émulateur Android, l'URL API par défaut est `http://10.0.2.2:8000/api/v1`; sur un appareil physique, remplacer cette adresse par l'IP de la machine.

## Développement local

Backend : `cd backend; python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --reload`

Web : `cd web; npm install; npm run dev`

Mobile : `cd mobile; flutter pub get; flutter run`

