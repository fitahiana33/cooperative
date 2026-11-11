export interface NavigationItem {
  label: string;
  to: string;
  name: string;
  icon: string;
  permission?: string;
  admin?: boolean;
}
export interface NavigationGroup {
  label: string;
  items: NavigationItem[];
}
export const navigation: NavigationGroup[] = [
  {
    label: "Au quotidien",
    items: [
      {
        label: "Vue d’ensemble",
        to: "/backoffice",
        name: "home",
        icon: "grid",
      },
      {
        label: "Départs",
        to: "/departs",
        name: "departs",
        icon: "bus",
        permission: "DEPART_READ",
      },
      {
        label: "Planning",
        to: "/planning",
        name: "planning-calendar",
        icon: "calendar",
        permission: "DEPART_READ",
      },
      {
        label: "Réservations",
        to: "/reservations",
        name: "reservations",
        icon: "ticket",
        permission: "RESERVATION_READ",
      },
      {
        label: "Billets",
        to: "/billets",
        name: "billets",
        icon: "file",
        permission: "BILLET_READ",
      },
      {
        label: "Embarquement",
        to: "/embarquement",
        name: "embarquement",
        icon: "scan",
        permission: "EMBARQUEMENT_MANAGE",
      },
      {
        label: "Pointage chauffeur",
        to: "/pointage-chauffeur",
        name: "driver-pointage",
        icon: "check",
        permission: "DEPART_POINTAGE",
      },
    ],
  },
  {
    label: "Réseau & ressources",
    items: [
      {
        label: "Gares",
        to: "/gares",
        name: "gares",
        icon: "building",
        permission: "GARE_READ",
      },
      {
        label: "Coopératives",
        to: "/cooperatives",
        name: "cooperatives",
        icon: "users",
        permission: "COOPERATIVE_READ",
      },
      {
        label: "Véhicules",
        to: "/vehicules",
        name: "vehicules",
        icon: "bus",
        permission: "VEHICULE_READ",
      },
      {
        label: "Chauffeurs",
        to: "/chauffeurs",
        name: "chauffeurs",
        icon: "user",
        permission: "CHAUFFEUR_READ",
      },
      {
        label: "Destinations",
        to: "/destinations",
        name: "destinations",
        icon: "pin",
        permission: "DESTINATION_READ",
      },
      {
        label: "Itinéraires",
        to: "/itineraires",
        name: "itineraires",
        icon: "route",
        permission: "ITINERAIRE_READ",
      },
      {
        label: "Tarifs",
        to: "/tarifs",
        name: "tarifs",
        icon: "wallet",
        permission: "TARIF_READ",
      },
      {
        label: "Marques",
        to: "/marques",
        name: "marques",
        icon: "settings",
        permission: "VEHICULE_READ",
      },
      {
        label: "Modèles",
        to: "/modeles",
        name: "modeles",
        icon: "settings",
        permission: "VEHICULE_READ",
      },
    ],
  },
  {
    label: "Finances & pilotage",
    items: [
      {
        label: "Paiements & caisse",
        to: "/finance",
        name: "finance",
        icon: "wallet",
        permission: "CAISSE_READ",
      },
      {
        label: "Statistiques",
        to: "/statistiques",
        name: "statistiques",
        icon: "chart",
        permission: "STATISTIQUE_READ",
      },
      {
        label: "Rapports",
        to: "/rapports",
        name: "rapports",
        icon: "file",
        permission: "RAPPORT_READ",
      },
      {
        label: "Aide à la décision",
        to: "/aide-decision",
        name: "aide-decision",
        icon: "sun",
        permission: "AIDE_DECISION_READ",
      },
    ],
  },
  {
    label: "Administration",
    items: [
      {
        label: "Paramètres",
        to: "/parametres",
        name: "booking-settings",
        icon: "settings",
        admin: true,
      },
      {
        label: "Utilisateurs",
        to: "/users",
        name: "users",
        icon: "users",
        permission: "USER_READ",
      },
      {
        label: "Rôles & permissions",
        to: "/roles",
        name: "roles",
        icon: "shield",
        permission: "ROLE_MANAGE",
      },
      {
        label: "Notifications",
        to: "/notifications",
        name: "notifications",
        icon: "bell",
        permission: "NOTIFICATION_READ",
      },
      {
        label: "Réinitialisation",
        to: "/system/reset",
        name: "system-reset",
        icon: "settings",
        admin: true,
      },
    ],
  },
];
export const roleLabels: Record<string, string> = {
  admin: "Administrateur",
  responsable_gare: "Responsable de gare",
  agent_gare: "Agent de gare",
  responsable_cooperative: "Responsable de coopérative",
  chauffeur: "Chauffeur",
  passenger: "Passager",
  passager: "Passager",
};
