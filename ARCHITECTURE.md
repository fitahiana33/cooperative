# Organisation modulaire

Chaque fonctionnalité métier est isolée par domaine et suit le même chemin dans chaque application.

```text
backend/app/
├── api/controllers/<module>/       # HTTP uniquement
├── services/<module>/              # cas d’utilisation et règles métier
├── repositories/<module>/          # accès aux données
├── schemas/<module>/               # contrats API
└── models/<module>/                # modèles PostgreSQL
```

Modules actifs : `authentication`, `user`, `role`, `permission`, `cooperative`, `gare`, `destination`, `itineraire`, `tarif`, `vehicule`, `chauffeur`, `depart`, `place`, `reservation`, `billet`, `finance`, `notification` et `dashboard`.

## Parcours métier principal

1. Un véhicule définit la capacité maximale (`nombre_places`).
2. La création d'un départ utilise cette capacité par défaut et crée automatiquement les places du départ.
3. Une réservation verrouille les places sélectionnées dans une transaction PostgreSQL. La base refuse les doublons et les places indisponibles.
4. La confirmation génère un billet et son QR code pour chaque passager.
5. Le paiement validé fait passer la réservation à `PAYEE` et crée l'opération de caisse correspondante.
6. L'annulation ou l'expiration libère les places réservées.

## Règles de capacité et de places

- `Depart.nombre_places` ne peut pas dépasser `Vehicule.nombre_places`.
- Les places sont numérotées à partir de 1 et sont générées par un trigger après la création du départ.
- Le redimensionnement d'un départ ajoute ou supprime uniquement les places disponibles ; une place utilisée ne peut pas être supprimée.
- Les états possibles sont `DISPONIBLE`, `RESERVEE`, `BLOQUEE` et `OCCUPEE`.

## Autorisation et périmètre des données

Les routes sont protégées par permissions. Un utilisateur rattaché à une coopérative ne voit que les départs, réservations, statistiques et opérations de son périmètre ; l'administrateur dispose de l'accès global. Les tableaux de bord doivent donc toujours appliquer le même filtre coopérative que les listes métier.

## Statistiques

`/api/v1/dashboard/summary` fournit les indicateurs opérationnels du jour. `/api/v1/statistiques` fournit les séries quotidiennes, les jours sans activité à zéro et la comparaison avec la période précédente. La comparaison est calculée côté backend pour conserver une définition métier identique entre le web et le mobile.

## Triggers PostgreSQL importants

- génération et redimensionnement des places de départ ;
- verrouillage et libération des places de réservation ;
- synchronisation de `places_reservees` ;
- passage de la réservation à `PAYEE` après paiement validé ;
- validation des opérations d'embarquement.

Le frontend Vue est organisé par couche, avec un sous-dossier par domaine : `models/authentication`, `controllers/authentication`, `services/authentication`, `stores/authentication` et `views/authentication`. Les composants transverses résident dans `components/ui` et `components/layout`. Un module ne doit pas dupliquer un service ou un modèle dans un autre emplacement.
