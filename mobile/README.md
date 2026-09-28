# Cooperative Mobile

Application Flutter destinée principalement aux passagers.

Structure : `presentation` (écrans/widgets) → `controllers` (état et orchestration) → `services` (cas d'utilisation) → `repositories` (contrat d'accès) → `data` (API/modèles).

Après installation de Flutter, démarrez le backend depuis la racine du projet :

```bash
docker compose up -d --build
```

Pour un émulateur Android, `10.0.2.2` représente le PC hôte :

```bash
flutter pub get
flutter run --dart-define=MOBILE_API_BASE_URL=http://10.0.2.2:8000/api/v1
```

## Installation sur un vrai smartphone

Le téléphone et le PC doivent être connectés au même réseau Wi-Fi. L'adresse `127.0.0.1` et `10.0.2.2` ne conviennent pas à un téléphone réel.

1. Sur Windows, trouvez l'adresse IPv4 Wi-Fi du PC avec `ipconfig` (par exemple `192.168.88.19`).
2. Vérifiez depuis le navigateur du téléphone : `http://192.168.88.19:8000/health` doit retourner une réponse du backend.
3. Construisez un APK release avec l'adresse du PC :

```bash
flutter pub get
flutter build apk --release --split-per-abi --dart-define=MOBILE_API_BASE_URL=http://192.168.88.19:8000/api/v1
```

Pour la plupart des smartphones récents, installez :

```text
build/app/outputs/flutter-apk/app-arm64-v8a-release.apk
```

`--split-per-abi` produit un APK par architecture et réduit fortement sa taille. L'APK universel est plus lourd. Si l'adresse IP du PC change, il faut reconstruire l'APK avec la nouvelle adresse.

Si le navigateur du téléphone n'accède pas à `/health`, autorisez le port TCP 8000 dans le pare-feu Windows pour le profil réseau Privé, puis vérifiez que les conteneurs sont actifs avec `docker compose ps`. Le manifeste Android autorise ici HTTP uniquement pour le réseau local de développement ; une mise en production devra utiliser HTTPS.
