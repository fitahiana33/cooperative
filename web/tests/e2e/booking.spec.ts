import { expect, test } from "playwright/test";

const offer = {
  id: 999,
  date_depart: "2026-12-01",
  heure_depart: "08:00:00",
  nombre_places: 3,
  places_reservees: 1,
  places_disponibles: 2,
  statut: "PROGRAMME",
  tarif: { prix: 40000, devise: "MGA" },
  vehicule: { id: 1, places_avant: 1, places_par_rangee: 2 },
  itineraire: {
    destination_depart: { nom: "Antananarivo" },
    destination_arrivee: { nom: "Antsirabe" },
  },
  cooperative: { nom: "Coopérative de test" },
  gare: { nom: "Gare de test" },
};
const token = "test-access-token-with-sufficient-length";

test.beforeEach(async ({ page }) => {
  // All API calls are isolated from operational data and payment providers.
  await page.route("**/api/v1/**", (route) =>
    route.fulfill({
      json: { items: [], total: 0, page: 1, pages: 0, page_size: 20 },
    }),
  );
  await page.route("**/departs/public/999", (route) =>
    route.fulfill({ json: offer }),
  );
  await page.route("**/reservations/policy", (route) =>
    route.fulfill({
      json: {
        max_seats: 6,
        max_pending: 2,
        hold_minutes: 30,
        cancellation_deadline_minutes: 120,
        deposit_rate: 0.25,
        minimum_deposit_amount: 300,
        online_payment_enabled: true,
        boarding_requires_full_payment: true,
      },
    }),
  );
  await page.route("**/reservations/public/departs/999/places", (route) =>
    route.fulfill({
      json: [
        { id: 1, numero_place: 1, statut: "DISPONIBLE" },
        { id: 2, numero_place: 2, statut: "DISPONIBLE" },
        { id: 3, numero_place: 3, statut: "RESERVEE" },
      ],
    }),
  );
});

test("mobile booking saves access before payment and retries without creating another reservation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  let bookings = 0;
  let payments = 0;
  const keys: string[] = [];
  await page.route("**/reservations/public", async (route) => {
    bookings++;
    expect(route.request().postDataJSON().cle_idempotence).toHaveLength(36);
    await route.fulfill({
      json: {
        reservation: { numero_reservation: "TEST-LOCAL" },
        access_token: token,
        payment: null,
        acompte_minimum: 10000,
      },
    });
  });
  await page.route(
    "**/reservations/public/TEST-LOCAL/paiement",
    async (route) => {
      payments++;
      keys.push(route.request().postDataJSON().cle_idempotence);
      expect(route.request().headers()["x-reservation-token"]).toBe(token);
      await route.fulfill({
        json: {
          id_paiement: 1,
          statut: "EN_ATTENTE",
          reference_paiement: "PAY-TEST",
          montant: 10000,
          checkout_url: null,
          verification_requise: true,
          message: "Demande à vérifier auprès du prestataire.",
        },
      });
    },
  );
  await page.goto("/reserver?depart_id=999&passengers=1");
  await expect(page.getByRole("button", { name: /Place 3,/ })).toBeDisabled();
  await expect(page.locator('input[autocomplete="name"]')).toHaveCount(0);
  await page.getByRole("button", { name: /Place 1,/ }).click();
  await page
    .getByRole("button", { name: /Continuer vers les coordonnées/ })
    .click();
  await page.locator('input[autocomplete="name"]').fill("Voyageur Test");
  await page.locator('input[type="tel"]').fill("0340011122");
  await page.locator('input[type="email"]').fill("voyageur@example.com");
  const emailBox = await page.locator('input[type="email"]').boundingBox();
  const actionsBox = await page.locator(".booking-stage-actions").boundingBox();
  expect(
    emailBox && actionsBox && emailBox.y + emailBox.height <= actionsBox.y,
  ).toBe(true);
  await page
    .getByRole("button", { name: /Continuer vers le règlement/ })
    .click();
  await expect(page.locator('input[type="number"]')).toHaveValue("10000");
  await page.locator(".booking-submit").click();
  await expect(
    page.getByRole("link", { name: /Retrouver la réservation TEST-LOCAL/ }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("vérifier");
  expect(
    await page.evaluate(() =>
      localStorage.getItem("reservation-access:TEST-LOCAL"),
    ),
  ).toBe(token);
  await page.locator(".booking-submit").click();
  await expect.poll(() => payments).toBe(2);
  expect(bookings).toBe(1);
  expect(keys[0]).toBe(keys[1]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("booking steps keep the entered values and block incomplete contact details", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/reserver?depart_id=999&passengers=1");
  await expect(
    page.getByRole("button", { name: /Continuer vers les coordonnées/ }),
  ).toBeDisabled();
  await page.getByRole("button", { name: /Place 1,/ }).click();
  await page
    .getByRole("button", { name: /Continuer vers les coordonnées/ })
    .click();
  await page
    .getByRole("button", { name: /Continuer vers le règlement/ })
    .click();
  await expect(page.locator('input[type="number"]')).toHaveCount(0);
  await page.locator('input[autocomplete="name"]').fill("Voyageur Test");
  await page.locator('input[type="tel"]').fill("0340011122");
  await page
    .getByRole("button", { name: /Continuer vers le règlement/ })
    .click();
  await page.locator('input[type="number"]').fill("20000");
  await page.getByRole("button", { name: "Retour aux coordonnées" }).click();
  await expect(page.locator('input[autocomplete="name"]')).toHaveValue(
    "Voyageur Test",
  );
  await page.getByRole("button", { name: "Retour aux places" }).click();
  await expect(page.getByRole("button", { name: /Place 1,/ })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await page.getByRole("button", { name: "3 Règlement", exact: true }).click();
  await expect(page.locator('input[type="number"]')).toHaveValue("20000");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("lookup shows partial payment clearly and cancels with its access token", async ({
  page,
}) => {
  const reservation = {
    id: 3,
    numero_reservation: "RES-TEST",
    statut: "PAYEE",
    montant_total: 40000,
    montant_paye: 10000,
    montant_restant: 30000,
    montant_a_rembourser: 0,
    etat_paiement: "ACOMPTE_RECU",
    peut_annuler: true,
    peut_payer: false,
    places: [],
    depart: offer,
  };
  await page.route("**/reservations/public/RES-TEST", (route) =>
    route.fulfill({ json: reservation }),
  );
  await page.route("**/reservations/public/RES-TEST/cancel", async (route) => {
    expect(route.request().headers()["x-reservation-token"]).toBe(token);
    await route.fulfill({
      json: {
        ...reservation,
        statut: "ANNULEE",
        peut_annuler: false,
        montant_restant: 0,
        montant_a_rembourser: 10000,
      },
    });
  });
  await page.goto("/ma-reservation");
  await page.locator('input[placeholder*="RES-"]').fill("RES-TEST");
  await page.locator('input[type="password"]').fill(token);
  await page.getByRole("button", { name: "Consulter ma réservation" }).click();
  await page.getByText("Détails et actions de la réservation").click();
  await expect(page.getByText("Acompte reçu, solde restant")).toBeVisible();
  await page
    .getByRole("button", { name: "Annuler la réservation", exact: true })
    .click();
  await page.getByRole("button", { name: "Confirmer l’annulation" }).click();
  await expect(page.getByRole("status")).toContainText("remboursement");
});

test("backoffice can find a vehicle outside the initial page and recover from search errors", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() =>
    localStorage.setItem("cooperative_access_token", "simulated-admin-session"),
  );
  await page.route("**/auth/me", (route) =>
    route.fulfill({
      json: {
        id: 1,
        name: "Administration",
        first_name: "Test",
        email: "admin@example.com",
        role: "admin",
        roles: [{ id: 1, libelle: "ADMIN" }],
        permissions: [],
        is_active: true,
      },
    }),
  );
  const queries: string[] = [];
  await page.route(
    (url) => url.pathname.endsWith("/vehicules"),
    async (route) => {
      const query =
        new URL(route.request().url()).searchParams.get("search") || "";
      queries.push(query);
      if (query === "indisponible") {
        await route.fulfill({
          status: 503,
          json: { detail: "Service temporairement indisponible" },
        });
        return;
      }
      const items =
        query === "9999"
          ? [
              {
                id: 210,
                id_cooperative: 1,
                immatriculation: "9999 TEST",
                nombre_places: 18,
                is_active: true,
                disponibilite: true,
              },
            ]
          : [];
      await route.fulfill({
        json: { items, total: items.length, page: 1, page_size: 60, pages: 1 },
      });
    },
  );
  await page.goto("/departs/new");
  const vehicle = page.getByRole("combobox", { name: "Choisir un véhicule" });
  await vehicle.fill("indisponible");
  await expect(page.getByRole("alert")).toContainText("Recherche indisponible");
  await vehicle.fill("9999");
  await page.getByRole("option", { name: "9999 TEST", exact: true }).click();
  await expect(vehicle).toHaveValue(/9999 TEST/);
  await expect(page.locator('input[max="18"]')).toHaveValue("18");
  expect(queries).toContain("9999");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
});

for (const width of [320, 390, 768, 1440]) {
  test(`public pages have a single heading and fit ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    for (const route of [
      "/",
      "/recherche",
      "/ma-reservation",
      "/login",
      "/conditions-voyage",
    ]) {
      await page.goto(route);
      await expect(page.locator("h1")).toHaveCount(1);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
      ).toBe(true);
    }
  });
}

test("a changed deposit is disclosed before payment and the booking is reused", async ({
  page,
}) => {
  let bookings = 0,
    payments = 0;
  await page.route("**/api/v1/reservations/public", async (route) => {
    bookings++;
    await route.fulfill({
      json: {
        reservation: { numero_reservation: "CHANGED-DEPOSIT" },
        access_token: token,
        acompte_minimum: 20000,
      },
    });
  });
  await page.route(
    "**/api/v1/reservations/public/CHANGED-DEPOSIT/paiement",
    async (route) => {
      payments++;
      expect(route.request().postDataJSON().montant).toBe(20000);
      await route.fulfill({
        json: {
          statut: "EN_ATTENTE",
          reference_paiement: "PAY-CHANGED",
          verification_requise: true,
          message: "À vérifier.",
        },
      });
    },
  );
  await page.goto("/reserver?depart_id=999&passengers=1");
  await page.getByRole("button", { name: /Place 1,/ }).click();
  await page
    .getByRole("button", { name: /Continuer vers les coordonnées/ })
    .click();
  await page.locator('input[autocomplete="name"]').fill("Voyageur Test");
  await page.locator('input[type="tel"]').fill("0340011122");
  await page
    .getByRole("button", { name: /Continuer vers le règlement/ })
    .click();
  await expect(page.locator('input[type="number"]')).toHaveValue("10000");
  await page.locator(".booking-submit").click();
  await expect(page.getByRole("alert")).toContainText(
    "Les conditions ont changé",
  );
  expect(payments).toBe(0);
  await page.getByRole("button", { name: /Reprendre le paiement/ }).click();
  await expect.poll(() => payments).toBe(1);
  expect(bookings).toBe(1);
});
