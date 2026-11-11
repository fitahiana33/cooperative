import { expect, test, type Page } from "playwright/test";

const policy = {
  max_seats: 6,
  deposit_rate: 0.375,
  minimum_deposit_amount: 300,
  online_payment_enabled: false,
};
const offer = {
  id: 999,
  date_depart: "2026-12-01",
  heure_depart: "08:00",
  statut: "PROGRAMME",
  nombre_places: 18,
  places_disponibles: 12,
  itineraire: {
    destination_depart: { nom: "Antananarivo" },
    destination_arrivee: { nom: "Antsirabe" },
  },
  cooperative: { nom: "Coopérative de test" },
  gare: { nom: "Gare de test" },
  tarif: { prix: 40000, devise: "MGA" },
};
async function mocks(page: Page, admin = false) {
  if (admin)
    await page.addInitScript(() =>
      localStorage.setItem("cooperative_access_token", "test-admin"),
    );
  await page.route("**/api/v1/**", (route) =>
    route.fulfill({ json: { items: [], total: 0, page: 1, pages: 0 } }),
  );
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      json: {
        id: 1,
        name: "Test",
        first_name: "Admin",
        role: "admin",
        roles: [{ id: 1, libelle: "ADMIN" }],
        permissions: [],
        is_active: true,
      },
    }),
  );
  await page.route("**/api/v1/reservations/policy", (route) =>
    route.fulfill({ json: policy }),
  );
  await page.route("**/api/v1/destinations/public?**", (route) =>
    route.fulfill({
      json: {
        items: [
          { id: 1, nom: "Antananarivo" },
          { id: 2, nom: "Antsirabe" },
        ],
        total: 2,
        pages: 1,
        page: 1,
      },
    }),
  );
  await page.route("**/api/v1/gares/public?**", (route) =>
    route.fulfill({
      json: {
        items: [
          {
            id: 1,
            nom: "Gare de test",
            ville: "Antananarivo",
            cooperatives: [],
          },
        ],
        total: 1,
        pages: 1,
        page: 1,
      },
    }),
  );
  await page.route("**/api/v1/departs/public/programme?**", (route) =>
    route.fulfill({ json: { items: [offer], total: 1, page: 1, pages: 1 } }),
  );
}

for (const width of [320, 390, 768, 1440]) {
  test(`public home is usable at ${width}px and displays the current deposit`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await mocks(page);
    await page.goto("/");
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator(".search-panel-heading")).toContainText("37,5 %");
    await expect(page.locator(".travel-hero-photograph")).toBeVisible();
    expect(
      await page
        .locator(".travel-hero-photograph")
        .evaluate(
          (img: HTMLImageElement) => img.complete && img.naturalWidth > 0,
        ),
    ).toBe(true);
    await expect(page.locator(".departure-offer")).toHaveCount(1);
    await page.getByRole("tab", { name: "Gares de départ" }).click();
    await expect(page.locator(".station-tile")).toBeVisible();
    await expect(page.locator(".destination-tile").first()).toBeHidden();
    await page.getByRole("tab", { name: "Destinations", exact: true }).click();
    await expect(page.locator(".destination-tile").first()).toBeVisible();
    const passengerControl = page.locator(".passenger-stepper");
    await expect(passengerControl.locator("output")).toHaveText(/1\s*passager/);
    await passengerControl.getByRole("button", { name: /Ajouter un passager/ }).click();
    await expect(passengerControl.locator("output")).toHaveText(/2\s*passagers/);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({
      path: `build/travel-home-${width}.png`,
      fullPage: true,
    });
    await page.locator(".offer-price button").click();
    await expect(page).toHaveURL(/reserver\?depart_id=999/);
  });
}

test("administrator can set a fractional deposit percentage", async ({
  page,
}) => {
  await mocks(page, true);
  let percentage = 25;
  await page.route("**/api/v1/system/booking-settings", async (route) => {
    if (route.request().method() === "PUT")
      percentage = route.request().postDataJSON().deposit_percentage;
    await route.fulfill({
      json: {
        deposit_percentage: percentage,
        minimum_deposit_amount: 300,
        booking_close_minutes: 10,
        updated_at: "2026-11-11T08:00:00Z",
      },
    });
  });
  await page.goto("/parametres");
  await page.getByLabel("Pourcentage d’acompte minimum (%)").fill("37.5");
  await expect(page.locator("#deposit-example")).toContainText("18");
  await page
    .getByRole("button", { name: "Enregistrer les conditions" })
    .click();
  await expect(page.locator(".success-banner")).toContainText(
    "nouvelles réservations",
  );
  expect(percentage).toBe(37.5);
});

test("decision support keeps forecasts, planning and limitations in separate tabs", async ({
  page,
}) => {
  await mocks(page, true);
  await page.route("**/api/v1/aide-decision", (route) =>
    route.fulfill({
      json: {
        date_reference: "2026-11-11",
        periode_observee: { du: "2026-08-13", au: "2026-11-10" },
        previsions: [
          {
            id_itineraire: 1,
            id_cooperative: 1,
            id_gare: 1,
            libelle: "Antananarivo → Antsirabe",
            cooperative: "Test",
            gare: "Gare de test",
            qualite: "INSUFFISANT",
            observations: 3,
            raison_qualite: "Historique trop court.",
            passagers_7_jours: null,
            passagers_30_jours: null,
            remplissage_7_jours: null,
          },
        ],
        recommandations: [],
        anomalies: [],
        destinations_demandees: [],
        limites: "Estimation indicative de l’activité confirmée.",
      },
    }),
  );
  await page.goto("/aide-decision");
  await expect(
    page.getByText("Données insuffisantes", { exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: /Départs & horaires/ }).click();
  await expect(
    page.getByText("Aucun historique suffisant pour recommander des départs."),
  ).toBeVisible();
  await expect(
    page.getByText("Données insuffisantes", { exact: true }),
  ).toBeHidden();
  await page.getByRole("tab", { name: "Méthode & limites" }).click();
  await expect(
    page.getByText("Estimation indicative de l’activité confirmée."),
  ).toBeVisible();
});
