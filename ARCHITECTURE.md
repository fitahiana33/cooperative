# Organisation modulaire

Les clients Vue et Flutter utilisent une API commune organisée par domaine. Les contrôleurs appliquent les permissions et traduisent les requêtes HTTP ; les services portent les cas d’utilisation et leurs transactions.

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
4. La confirmation émet un billet par passager ; son QR code est rendu à la demande par un accès protégé.
5. Un paiement validé confirme la réservation. `PAYEE` peut représenter un acompte : les champs `montant_paye`, `montant_restant`, `montant_rembourse` et `etat_paiement` distinguent les situations. Seuls les encaissements en espèces créent une recette de caisse physique.
6. L'annulation ou l'expiration libère les places réservées.

## Règles de capacité et de places

- `Depart.nombre_places` ne peut pas dépasser `Vehicule.nombre_places`.
- Les places sont numérotées à partir de 1 et sont générées par un trigger après la création du départ.
- Le redimensionnement d'un départ ajoute ou supprime uniquement les places disponibles ; une place utilisée ne peut pas être supprimée.
- Les états possibles sont `DISPONIBLE`, `RESERVEE`, `BLOQUEE` et `OCCUPEE`.

## Autorisation et périmètre des données

Les routes sont protégées par permissions. Un utilisateur rattaché à une coopérative ne voit que les départs, réservations, statistiques et opérations de son périmètre ; l'administrateur dispose de l'accès global. Les agents et responsables sont rattachés à leur gare via `gare_agents`. Paiements, tableaux de bord, rapports, aide à la décision et audit appliquent aussi ce périmètre de gare. Un responsable sans rattachement ne dispose pas d’accès global. Les chauffeurs restent limités à leurs réservations et voyages pour les données passagers.

## Statistiques

`/api/v1/dashboard/summary` fournit les indicateurs opérationnels du jour. `/api/v1/statistiques` fournit les séries quotidiennes, les jours sans activité à zéro et la comparaison avec la période précédente. La comparaison est calculée côté backend pour conserver une définition métier identique entre le web et le mobile.

## Triggers PostgreSQL importants

- génération et redimensionnement des places de départ ;
- verrouillage et libération des places de réservation ;
- synchronisation de `places_reservees` ;
- passage de la réservation à `PAYEE` après paiement validé ;
- validation des opérations d'embarquement.

Le frontend Vue est organisé par couche, avec un sous-dossier par domaine : `models/authentication`, `controllers/authentication`, `services/authentication`, `stores/authentication` et `views/authentication`. Les composants transverses résident dans `components/ui` et `components/layout`. Un module ne doit pas dupliquer un service ou un modèle dans un autre emplacement.


## Frontières des transactions et intégrations

Les services métier utilisent SQLAlchemy pour les requêtes spécifiques à leurs cas d’usage ; les repositories restent utilisés lorsqu’ils apportent une recherche réutilisable. Ne pas ajouter une couche CRUD qui valide séparément chaque étape d’un même cas d’usage.

- `services/reservation/counter_sale.py` coordonne réservation, confirmation et encaissement avec un seul commit ; les méthodes composables acceptent `commit=False`.
- Le paiement externe ne peut pas être inclus dans une transaction PostgreSQL. Réservation, tentative et résultat ont des états persistants, une clé de commande et une procédure de vérification.
- `integrations/papi.py` contient le transport HTTP du prestataire ; le domaine financier conserve les règles de montants, d’accès et de remboursement.
- `services/booking_policy.py` expose la politique serveur utilisée par les clients. Les boutons utilisent aussi `peut_annuler`, `peut_payer` et `date_limite_annulation` calculés par l’API.
- Les QR sont rendus à la demande par l’endpoint protégé ; leur émission n’ajoute plus de fichier avant la validation d’une vente.
- Les événements financiers portent leur date de validation et de remboursement, ainsi que leur méthode et leur référence. L’audit porte l’auteur et le périmètre.
- `services/report_pdf.py` gère les tableaux imprimables. L’export CSV des réservations parcourt toutes les lignes par lots avant de transmettre un fichier temporaire.
- Le verrou de maintenance reste sur une connexion dédiée malgré les commits des traitements. Les rappels sont créés automatiquement.
- Les notifications sont enregistrées avec la transaction métier. `services/notification/delivery.py` traite ensuite les emails autorisés via SMTP, avec verrouillage, suivi de livraison et nouvelles tentatives. L’historique reste dans l’application ; aucun accès public ou secret de paiement n’est ajouté au contenu envoyé.

Côté web, `services/pagination.ts` fournit les contrats `Page<T>` et le chargement complet des petits référentiels. `SearchSelect` sait aussi rechercher côté serveur avec temporisation et rejet des réponses obsolètes pour les listes de véhicules et chauffeurs. Les actions voyageurs, remboursements et incidents sont des composants séparés des grandes pages.

Les procédures d’exploitation, de migration et de rapprochement sont décrites dans [OPERATIONS.md](OPERATIONS.md).
