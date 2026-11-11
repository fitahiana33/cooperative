import { expect, test, type Page } from "playwright/test";

function localDate() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function currentWeekPeriod() {
  const start = new Date(`${localDate()}T12:00:00`);
  const day = start.getDay() || 7;
  start.setDate(start.getDate() - day + 1);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const format = (value: Date) => value.toLocaleDateString("fr-FR");
  return `${format(start)} — ${format(end)}`;
}

const departures = Array.from({ length: 12 }, (_, index) => ({
  id: index + 1,
  id_itineraire: 1,
  id_cooperative: 1,
  id_gare: 1,
  id_vehicule: 1,
  id_chauffeur: 1,
  id_tarif: 1,
  date_depart: localDate(),
  heure_depart: `${String(6 + Math.floor(index / 2)).padStart(2, "0")}:${index % 2 ? "30" : "00"}:00`,
  nombre_places: 24,
  places_reservees: 8 + index,
  places_disponibles: 16 - index,
  taux_remplissage: 40,
  statut: index === 2 ? "RETARDE" : "PROGRAMME",
  created_at: `${localDate()}T00:00:00Z`,
  itineraire: { id: 1, destination_depart: { id: 1, nom: "Antananarivo" }, destination_arrivee: { id: 2, nom: "Antsirabe" } },
  cooperative: { id: 1, nom: "Coopérative Soa" },
  gare: { id: 1, nom: "Gare centrale", ville: "Antananarivo" },
  vehicule: { id: 1, immatriculation: "1234 TAA", nombre_places: 24 },
  chauffeur: { id: 1, id_user: 2, numero_permis: "MG-PC-100" },
}));

async function mockBackoffice(page: Page) {
  await page.addInitScript(() => localStorage.setItem("cooperative_access_token", "admin-session"));
  await page.route("**/api/v1/**", (route) => route.fulfill({ json: { items: [], total: 0, page: 1, pages: 0, page_size: 100 } }));
  await page.route("**/api/v1/auth/me", (route) => route.fulfill({ json: { id: 1, name: "Admin", first_name: "Système", role: "admin", roles: [{ id: 1, libelle: "admin" }], permissions: [], is_active: true } }));
  await page.route("**/api/v1/departs?**", (route) => route.fulfill({ json: { items: departures, total: departures.length, page: 1, pages: 1, page_size: 100 } }));
  await page.route("**/api/v1/gares?**", (route) => route.fulfill({ json: { items: [{ id: 1, nom: "Gare centrale", ville: "Antananarivo", adresse: "Centre", is_active: true, quais: [], zones: [] }], total: 1, page: 1, pages: 1 } }));
  await page.route("**/api/v1/cooperatives?**", (route) => route.fulfill({ json: { items: [{ id: 1, nom: "Coopérative Soa", sigle: "SOA", is_active: true, created_at: localDate() }], total: 1, page: 1, pages: 1 } }));
  await page.route("**/api/v1/itineraires?**", (route) => route.fulfill({ json: { items: [{ id: 1, id_destination_depart: 1, id_destination_arrivee: 2, is_active: true, created_at: localDate(), destination_depart: { id: 1, nom: "Antananarivo" }, destination_arrivee: { id: 2, nom: "Antsirabe" } }], total: 1, page: 1, pages: 1 } }));
}

for (const width of [390, 1440]) {
  test(`planning offers three readable views at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await mockBackoffice(page);
    await page.goto("/planning");
    await expect(page.getByRole("heading", { name: "Planning des départs" })).toBeVisible();
    await expect(page.locator(".agenda-row")).toHaveCount(8);
    await page.screenshot({ path: `build/planning-agenda-${width}.png`, fullPage: true });
    await page.getByRole("button", { name: "Semaine", exact: true }).click();
    await expect(page.locator(".calendar-item")).toHaveCount(12);
    await page.getByRole("button", { name: "Tableau", exact: true }).click();
    await expect(page.locator(".planning-table-wrap tbody tr")).toHaveCount(12);
    await page.getByRole("button", { name: "Ressources", exact: true }).click();
    await expect(page.locator(".resource-card")).toHaveCount(1);
    await page.locator(".resource-item").first().click();
    await expect(page.locator(".planning-drawer")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}

test("driver pointage is paginated instead of becoming a paper roll", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await mockBackoffice(page);
  await page.goto("/pointage-chauffeur");
  await expect(page.getByRole("heading", { name: "Pointage des chauffeurs" })).toBeVisible();
  await expect(page.locator(".operations-card tbody tr")).toHaveCount(6);
  await expect(page.getByText("12 trajet(s)")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "build/pointage-mobile-390.png", fullPage: true });
});

test("operational lists expose the same advanced dimensions", async ({ page }) => {
  await mockBackoffice(page);
  for (const path of ["/departs", "/reservations", "/billets"]) {
    await page.goto(path);
    const filters = page.locator(".operational-filters");
    await expect(filters).toBeVisible();
    await expect(filters.getByText("Gare", { exact: true })).toBeVisible();
    await expect(filters.getByText("Coopérative", { exact: true })).toBeVisible();
    await expect(filters.getByText("Trajet", { exact: true })).toBeVisible();
  }
});

test("planning filters survive a full page refresh", async ({ page }) => {
  await mockBackoffice(page);
  await page.goto("/planning");

  const filters = page.locator(".operational-filters");
  await filters.locator(".operational-filters__toggle").click();
  const statusFilter = filters.locator("label").filter({ hasText: "Statut" }).locator("select");
  const stationFilter = filters.locator("label").filter({ hasText: "Gare" }).locator("select");
  await statusFilter.selectOption("RETARDE");
  await expect(stationFilter.locator("option")).toHaveCount(2);
  await stationFilter.selectOption("1");
  await page.getByRole("button", { name: "Tableau", exact: true }).click();

  await expect.poll(() => page.evaluate(() => localStorage.getItem("cooperative:filters:1:planning"))).toContain('"status":"RETARDE"');
  await expect.poll(() => page.evaluate(() => localStorage.getItem("cooperative:filters:1:planning"))).toContain('"gareId":1');
  await page.getByRole("button", { name: "Semaine précédente" }).click();
  await expect(page.getByRole("button", { name: "Aujourd’hui", exact: true })).toBeEnabled();
  await page.reload();

  await expect(statusFilter).toHaveValue("RETARDE");
  await expect(stationFilter).toHaveValue("1");
  await expect(page.getByRole("button", { name: "Tableau", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText(currentWeekPeriod(), { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Aujourd’hui", exact: true })).toBeDisabled();
});
