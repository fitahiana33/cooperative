import { expect, test } from "playwright/test";

const departure = {
  id: 999,
  date_depart: "2026-12-01",
  heure_depart: "08:00:00",
  statut: "PROGRAMME",
  id_itineraire: 1,
  id_cooperative: 1,
  id_vehicule: 1,
  id_chauffeur: 1,
  nombre_places: 18,
  places_disponibles: 12,
  taux_remplissage: 33.3,
  itineraire: {
    destination_depart: { nom: "Antananarivo" },
    destination_arrivee: { nom: "Antsirabe" },
  },
  cooperative: { nom: "Coopérative de test" },
  vehicule: { immatriculation: "1234 TEST" },
  chauffeur: { numero_permis: "PERMIS-TEST" },
  tarif: { prix: 40000, devise: "MGA" },
};

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("cooperative_access_token", "simulated-admin-session"),
  );
  await page.route("**/api/v1/**", (route) =>
    route.fulfill({
      json: { items: [], total: 0, page: 1, pages: 0, page_size: 20 },
    }),
  );
  await page.route("**/auth/me", (route) =>
    route.fulfill({
      json: {
        id: 1,
        name: "Test",
        first_name: "Administration",
        email: "admin@example.com",
        role: "admin",
        roles: [{ id: 1, libelle: "ADMIN" }],
        permissions: [],
        is_active: true,
      },
    }),
  );
  await page.route("**/api/v1/departs/999", (route) =>
    route.fulfill({ json: departure }),
  );
  await page.route("**/api/v1/departs/999/incidents", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/reservations/77", (route) =>
    route.fulfill({
      json: {
        id: 77,
        numero_reservation: "RES-TABS",
        statut: "PAYEE",
        id_depart: 999,
        depart: departure,
        montant_total: 80000,
        montant_paye: 20000,
        montant_restant: 60000,
        montant_a_rembourser: 0,
        places: [
          {
            id: 1,
            id_depart_place: 2,
            nom_passager: "Voyageur Test",
            depart_place: { numero_place: 2 },
          },
        ],
      },
    }),
  );
});

test("vehicle form reveals the tab containing an invalid field and preserves typed data", async ({
  page,
}) => {
  await page.goto("/vehicules/new");
  await page.getByRole("tab", { name: /Documents/ }).click();
  await page.getByRole("button", { name: "Enregistrer", exact: true }).click();
  await expect(
    page.getByRole("tab", { name: "Identification", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("#vehicle-registration")).toBeFocused();
  await page.locator("#vehicle-registration").fill("4321 TEST");
  await page
    .getByRole("tab", { name: "Caractéristiques", exact: true })
    .click();
  await page.getByRole("tab", { name: "Identification", exact: true }).click();
  await expect(page.locator("#vehicle-registration")).toHaveValue("4321 TEST");
});

for (const width of [390, 1280]) {
  test(`departure sections support keyboard navigation and retain operations at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/departs/999");
    const information = page.getByRole("tab", {
      name: "Informations",
      exact: true,
    });
    await expect(information).toHaveAttribute("aria-selected", "true");
    await expect(page.getByRole("tabpanel")).toHaveCount(1);
    await expect(
      page.getByRole("heading", { name: "Journal des incidents" }),
    ).not.toBeVisible();
    await information.focus();
    await page.keyboard.press("ArrowRight");
    await expect(page.getByRole("tab", { name: "Opérations" })).toBeFocused();
    await expect(
      page.getByRole("link", { name: "Gérer les places" }),
    ).toBeVisible();
    await page.keyboard.press("End");
    await expect(
      page.getByRole("heading", { name: "Journal des incidents" }),
    ).toBeVisible();
    await expect(page.getByRole("tabpanel")).toHaveAttribute(
      "aria-labelledby",
      "departure-detail-tab-incidents",
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
  });

  test(`reservation separates passengers and finance at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/reservations/77");
    await expect(page.getByRole("table")).not.toBeVisible();
    await page.getByRole("tab", { name: /Passagers et billets/ }).click();
    await expect(
      page.getByRole("cell", { name: "Voyageur Test", exact: true }),
    ).toBeVisible();
    await page.getByRole("tab", { name: "Règlement", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Situation du règlement" }),
    ).toBeVisible();
    await expect(page.getByRole("table")).not.toBeVisible();
    await page.getByRole("tab", { name: "Opérations", exact: true }).click();
    await expect(
      page.getByRole("button", { name: "Annuler", exact: true }),
    ).toBeVisible();
    await expect(page.getByRole("tabpanel")).toHaveCount(1);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
  });
}
