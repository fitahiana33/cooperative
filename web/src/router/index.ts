import { createRouter, createWebHistory } from "vue-router";
import { useAuthenticationStore } from "../stores/authentication/store";

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition;
    if (to.hash) return { el: to.hash, top: 96 };
    if (to.path !== from.path) return { top: 0 };
  },
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("../views/authentication/LoginView.vue"),
      meta: { layout: "auth" },
    },
    {
      path: "/register",
      name: "register",
      component: () => import("../views/authentication/RegisterView.vue"),
      meta: { layout: "auth" },
    },
    {
      path: "/forgot-password",
      name: "forgot-password",
      component: () => import("../views/authentication/ForgotPasswordView.vue"),
      meta: { layout: "auth" },
    },
    {
      path: "/",
      name: "frontoffice",
      component: () => import("../views/frontoffice/FrontOfficeHomeView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/programme",
      name: "programme",
      component: () => import("../views/frontoffice/FrontOfficeHomeView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/recherche",
      name: "search-results",
      component: () =>
        import("../views/frontoffice/FrontOfficeResultsView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/reserver",
      name: "public-booking",
      component: () =>
        import("../views/frontoffice/FrontOfficeBookingView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/paiement/succes",
      name: "payment-success",
      component: () => import("../views/frontoffice/PaymentResultView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/paiement/echec",
      name: "payment-failure",
      component: () => import("../views/frontoffice/PaymentResultView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/ma-reservation",
      name: "public-reservation-lookup",
      component: () =>
        import("../views/frontoffice/PublicReservationLookupView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/espace-client",
      name: "client-space",
      component: () => import("../views/frontoffice/ClientSpaceView.vue"),
      meta: { requiresAuth: true, clientOnly: true, layout: "frontoffice" },
    },
    {
      path: "/mes-reservations",
      name: "client-reservations",
      component: () =>
        import("../views/frontoffice/ClientReservationsView.vue"),
      meta: { requiresAuth: true, clientOnly: true, layout: "frontoffice" },
    },
    {
      path: "/mes-billets",
      name: "client-tickets",
      component: () => import("../views/frontoffice/ClientTicketsView.vue"),
      meta: { requiresAuth: true, clientOnly: true, layout: "frontoffice" },
    },
    {
      path: "/mon-profil",
      name: "client-profile",
      component: () => import("../views/frontoffice/ClientProfileView.vue"),
      meta: { requiresAuth: true, clientOnly: true, layout: "frontoffice" },
    },
    {
      path: "/conditions-voyage",
      name: "travel-conditions",
      component: () => import("../views/frontoffice/PublicInfoView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/annulation",
      name: "cancellation-policy",
      component: () => import("../views/frontoffice/PublicInfoView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/confidentialite",
      name: "privacy-policy",
      component: () => import("../views/frontoffice/PublicInfoView.vue"),
      meta: { layout: "frontoffice" },
    },
    {
      path: "/backoffice",
      name: "home",
      component: () => import("../views/dashboard/HomeView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/profil",
      name: "profile",
      component: () => import("../views/account/ProfileView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/users",
      name: "users",
      component: () => import("../views/administration/users/UsersView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/users/:id",
      name: "user-detail",
      component: () =>
        import("../views/administration/users/UserDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/users/new",
      name: "user-create",
      component: () => import("../views/administration/users/UserFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/users/:id/edit",
      name: "user-edit",
      component: () => import("../views/administration/users/UserFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/gares",
      name: "gares",
      component: () => import("../views/management/ManagementView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/gares/:id",
      name: "gare-detail",
      component: () => import("../views/management/GareDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/gares/new",
      name: "gare-create",
      component: () => import("../views/management/GareFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/gares/:id/edit",
      name: "gare-edit",
      component: () => import("../views/management/GareFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/cooperatives",
      name: "cooperatives",
      component: () => import("../views/management/ManagementView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/cooperatives/:id",
      name: "cooperative-detail",
      component: () => import("../views/management/CooperativeDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/cooperatives/new",
      name: "cooperative-create",
      component: () => import("../views/management/CooperativeFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/cooperatives/:id/edit",
      name: "cooperative-edit",
      component: () => import("../views/management/CooperativeFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/roles",
      name: "roles",
      component: () =>
        import("../views/administration/roles/RolesPermissionsView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/parametres",
      name: "booking-settings",
      component: () =>
        import("../views/administration/BookingSettingsView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/system/reset",
      name: "system-reset",
      component: () => import("../views/administration/SystemResetView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/vehicules",
      name: "vehicules",
      component: () => import("../views/management/FleetListView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/vehicules/new",
      name: "vehicule-create",
      component: () => import("../views/management/FleetFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/vehicules/:id",
      name: "vehicule-detail",
      component: () => import("../views/management/FleetDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/vehicules/:id/edit",
      name: "vehicule-edit",
      component: () => import("../views/management/FleetFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/chauffeurs",
      name: "chauffeurs",
      component: () => import("../views/management/FleetListView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/chauffeurs/new",
      name: "chauffeur-create",
      component: () => import("../views/management/FleetFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/chauffeurs/:id",
      name: "chauffeur-detail",
      component: () => import("../views/management/FleetDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/chauffeurs/:id/edit",
      name: "chauffeur-edit",
      component: () => import("../views/management/FleetFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/marques",
      name: "marques",
      component: () => import("../views/management/FleetListView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/marques/new",
      name: "marque-create",
      component: () => import("../views/management/FleetFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/marques/:id",
      name: "marque-detail",
      component: () => import("../views/management/FleetDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/marques/:id/edit",
      name: "marque-edit",
      component: () => import("../views/management/FleetFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/modeles",
      name: "modeles",
      component: () => import("../views/management/FleetListView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/modeles/new",
      name: "modele-create",
      component: () => import("../views/management/FleetFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/modeles/:id",
      name: "modele-detail",
      component: () => import("../views/management/FleetDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/modeles/:id/edit",
      name: "modele-edit",
      component: () => import("../views/management/FleetFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/destinations",
      name: "destinations",
      component: () => import("../views/management/RouteListView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/destinations/new",
      name: "destination-create",
      component: () => import("../views/management/RouteFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/destinations/:id",
      name: "destination-detail",
      component: () => import("../views/management/RouteDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/destinations/:id/edit",
      name: "destination-edit",
      component: () => import("../views/management/RouteFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/itineraires",
      name: "itineraires",
      component: () => import("../views/management/RouteListView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/itineraires/new",
      name: "itineraire-create",
      component: () => import("../views/management/RouteFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/itineraires/:id",
      name: "itineraire-detail",
      component: () => import("../views/management/RouteDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/itineraires/:id/edit",
      name: "itineraire-edit",
      component: () => import("../views/management/RouteFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/tarifs",
      name: "tarifs",
      component: () => import("../views/management/RouteListView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/tarifs/new",
      name: "tarif-create",
      component: () => import("../views/management/RouteFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/tarifs/:id",
      name: "tarif-detail",
      component: () => import("../views/management/RouteDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/tarifs/:id/edit",
      name: "tarif-edit",
      component: () => import("../views/management/RouteFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/departs",
      name: "departs",
      component: () => import("../views/management/DepartListView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/planning",
      name: "planning-calendar",
      component: () => import("../views/operations/PlanningBoardView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/pointage-chauffeur",
      name: "driver-pointage",
      component: () => import("../views/operations/DriverPointageWorkspaceView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/departs/new",
      name: "depart-create",
      component: () => import("../views/management/DepartFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/departs/:id",
      name: "depart-detail",
      component: () => import("../views/management/DepartDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/departs/:id/edit",
      name: "depart-edit",
      component: () => import("../views/management/DepartFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/reservations",
      name: "reservations",
      component: () => import("../views/operations/ReservationsView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/reservations/new",
      name: "reservation-create",
      component: () => import("../views/operations/ReservationFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/reservations/:id",
      name: "reservation-detail",
      component: () => import("../views/operations/ReservationDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/reservations/:id/edit",
      name: "reservation-edit",
      component: () => import("../views/operations/ReservationFormView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/departs/:id/places",
      name: "places-depart",
      component: () => import("../views/operations/DepartPlacesView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/billets",
      name: "billets",
      component: () => import("../views/operations/BilletsWorkspaceView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/billets/:id",
      name: "billet-detail",
      component: () => import("../views/operations/BilletDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/embarquement",
      name: "embarquement",
      component: () => import("../views/operations/BoardingView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/finance",
      name: "finance",
      component: () => import("../views/operations/FinanceView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/finance/caisses/:id",
      name: "caisses-detail",
      component: () => import("../views/operations/CaisseDetailView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/notifications",
      name: "notifications",
      component: () => import("../views/operations/NotificationsView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/statistiques",
      name: "statistiques",
      component: () => import("../views/operations/StatisticsView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/rapports",
      name: "rapports",
      component: () => import("../views/operations/ReportsView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/aide-decision",
      name: "aide-decision",
      component: () => import("../views/operations/DecisionSupportView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/acces-refuse",
      name: "forbidden",
      component: () => import("../views/ForbiddenView.vue"),
      meta: { requiresAuth: true, layout: "default" },
    },
    {
      path: "/:pathMatch(.*)*",
      name: "not-found",
      component: () => import("../views/NotFoundView.vue"),
      meta: { layout: "default" },
    },
  ],
});

// Not a real permission: only administrators (who hold every permission) pass.
const ADMIN_ONLY = "ADMIN_ONLY";
const STAFF_ROLES = new Set([
  "admin",
  "responsable_gare",
  "agent_gare",
  "responsable_cooperative",
  "chauffeur",
]);

function isClientAccount(
  user: ReturnType<typeof useAuthenticationStore>["user"],
) {
  if (!user) return false;
  const assigned = [
    user.role,
    ...(user.roles || []).map((role) => role.libelle),
  ].map((role) => role.toLowerCase());
  return (
    assigned.includes("passenger") &&
    !assigned.some((role) => STAFF_ROLES.has(role))
  );
}

router.beforeEach((to) => {
  const auth = useAuthenticationStore();
  const clientAccount = isClientAccount(auth.user);
  const publicAuthRoutes = ["login", "register", "forgot-password"];
  const routePermissions: Record<string, string> = {
    users: "USER_READ",
    "user-detail": "USER_READ",
    "user-create": "USER_CREATE",
    "user-edit": "USER_UPDATE",
    gares: "GARE_READ",
    "gare-create": "GARE_CREATE",
    "gare-edit": "GARE_UPDATE",
    "gare-detail": "GARE_READ",
    cooperatives: "COOPERATIVE_READ",
    "cooperative-detail": "COOPERATIVE_READ",
    "cooperative-create": "COOPERATIVE_CREATE",
    "cooperative-edit": "COOPERATIVE_UPDATE",
    roles: "ROLE_MANAGE",
    vehicules: "VEHICULE_READ",
    "vehicule-detail": "VEHICULE_READ",
    "vehicule-create": "VEHICULE_CREATE",
    "vehicule-edit": "VEHICULE_UPDATE",
    chauffeurs: "CHAUFFEUR_READ",
    "chauffeur-detail": "CHAUFFEUR_READ",
    "chauffeur-create": "CHAUFFEUR_CREATE",
    "chauffeur-edit": "CHAUFFEUR_UPDATE",
    // Brands, models, destinations and itineraries are edited by administrators only (backend rule).
    marques: "VEHICULE_READ",
    "marque-detail": "VEHICULE_READ",
    "marque-create": ADMIN_ONLY,
    "marque-edit": ADMIN_ONLY,
    modeles: "VEHICULE_READ",
    "modele-detail": "VEHICULE_READ",
    "modele-create": ADMIN_ONLY,
    "modele-edit": ADMIN_ONLY,
    destinations: "DESTINATION_READ",
    "destination-detail": "DESTINATION_READ",
    "destination-create": ADMIN_ONLY,
    "destination-edit": ADMIN_ONLY,
    itineraires: "ITINERAIRE_READ",
    "itineraire-detail": "ITINERAIRE_READ",
    "itineraire-create": ADMIN_ONLY,
    "itineraire-edit": ADMIN_ONLY,
    tarifs: "TARIF_READ",
    "tarif-detail": "TARIF_READ",
    "tarif-create": "TARIF_CREATE",
    "tarif-edit": "TARIF_UPDATE",
    departs: "DEPART_READ",
    "planning-calendar": "DEPART_READ",
    "driver-pointage": "DEPART_POINTAGE",
    "depart-detail": "DEPART_READ",
    "depart-create": "DEPART_CREATE",
    "depart-edit": "DEPART_UPDATE",
    reservations: "RESERVATION_READ",
    "reservation-detail": "RESERVATION_READ",
    "reservation-create": "RESERVATION_CREATE",
    "reservation-edit": "RESERVATION_UPDATE",
    "client-reservations": "RESERVATION_READ",
    "client-tickets": "BILLET_READ",
    // Anyone who sees the departure sees its seats; changing a seat needs PLACE_MANAGE (checked in the view).
    "places-depart": "DEPART_READ",
    "booking-settings": ADMIN_ONLY,
    "system-reset": ADMIN_ONLY,
    billets: "BILLET_READ",
    "billet-detail": "BILLET_READ",
    embarquement: "EMBARQUEMENT_MANAGE",
    finance: "CAISSE_READ",
    "caisses-detail": "CAISSE_READ",
    notifications: "NOTIFICATION_READ",
    statistiques: "STATISTIQUE_READ",
    rapports: "RAPPORT_READ",
    "aide-decision": "AIDE_DECISION_READ",
  };

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    // L'application démarre toujours sur le frontoffice lorsqu'aucune session
    // n'est active. La connexion ne doit être ouverte que volontairement.
    return { name: "frontoffice" };
  }

  // Keep the current URL during a temporary API outage. The authentication
  // store deliberately preserves a still-valid token in that case; redirecting
  // to "forbidden" would make a simple refresh lose the user's working page.
  if (auth.isAuthenticated && !auth.user) return true;

  if (publicAuthRoutes.includes(to.name as string) && auth.isAuthenticated) {
    return { name: clientAccount ? "client-space" : "home" };
  }

  // A passenger never enters the administration shell, even when they type a
  // backoffice URL directly or follow an old saved link.
  if (clientAccount && to.name === "profile") return { name: "client-profile" };
  if (clientAccount && to.meta.layout === "default") {
    return { name: "client-space" };
  }
  if (to.meta.clientOnly && !clientAccount) {
    return { name: auth.isAuthenticated ? "home" : "frontoffice" };
  }

  // Access is decided by permissions only, exactly like the API, so custom
  // roles work and the menu (also permission-based) never shows a page that
  // then refuses to open.
  const requiredPermission = routePermissions[String(to.name || "")];
  if (requiredPermission && !auth.hasPermission(requiredPermission)) {
    return { name: "forbidden", query: { from: to.fullPath } };
  }
});

export default router;
