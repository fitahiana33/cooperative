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

Modules actuellement actifs : `authentication`, `user`, `role`, `permission`. Les autres domaines seront ajoutés uniquement après validation complète de l’authentification.

Le frontend Vue est organisé par couche, avec un sous-dossier par domaine : `models/authentication`, `controllers/authentication`, `services/authentication`, `stores/authentication` et `views/authentication`. Les composants transverses résident dans `components/ui` et `components/layout`. Un module ne doit pas dupliquer un service ou un modèle dans un autre emplacement.
