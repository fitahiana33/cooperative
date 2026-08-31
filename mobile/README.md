# Cooperative Mobile

Application Flutter destinée principalement aux passagers.

Structure : `presentation` (écrans/widgets) → `controllers` (état et orchestration) → `services` (cas d'utilisation) → `repositories` (contrat d'accès) → `data` (API/modèles).

Après installation de Flutter :

```bash
flutter pub get
flutter run --dart-define=MOBILE_API_BASE_URL=http://10.0.2.2:8000/api/v1
```

