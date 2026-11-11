/* Read-only local browser checks. Supply an installed Playwright module path.
   Run from the repository root. Credentials stay in memory; payments are mocked. */
const { chromium } = require(process.argv[2] || "playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const base = process.env.QA_WEB_URL || "http://127.0.0.1:5173";
const output = "web/build/qa";
fs.mkdirSync(output, { recursive: true });
const pageOf = (items, total = items.length, page = 1) => ({
  items,
  total,
  page,
  page_size: 12,
  pages: Math.max(1, Math.ceil(total / 12)),
});
async function noOverflow(page, label) {
  const size = await page.evaluate(() => ({
    width: innerWidth,
    content: document.documentElement.scrollWidth,
  }));
  assert(
    size.content <= size.width + 1,
    `${label}: overflow ${size.content}/${size.width}`,
  );
}
async function topScreenshot(page, file) {
  await page.evaluate(() => {
    document.activeElement?.blur();
    scrollTo(0, 0);
  });
  await page.screenshot({ path: `${output}/${file}.png`, fullPage: true });
}
(async () => {
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  const errors = [];
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    page.on("pageerror", (error) => errors.push(error.message));
    const publicRoutes = [
      "/",
      "/recherche",
      "/ma-reservation",
      "/conditions-voyage",
      "/annulation",
      "/confidentialite",
      "/paiement/succes",
      "/reserver?depart_id=invalid",
      "/login",
      "/register",
      "/forgot-password",
      "/page-inconnue",
    ];
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 950 });
      for (const path of publicRoutes) {
        await page.goto(base + path, { waitUntil: "networkidle" });
        assert.equal(
          await page.locator("h1").count(),
          1,
          `${path}: unique visible heading`,
        );
        assert((await page.title()).includes("Coopérative"), `${path}: title`);
        await noOverflow(page, `${path}@${width}`);
      }
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base, { waitUntil: "networkidle" });
    await page
      .getByRole("button", { name: "Ouvrir le menu", exact: true })
      .click();
    assert(
      await page
        .getByRole("navigation", { name: "Navigation mobile" })
        .isVisible(),
    );
    await page.keyboard.press("Escape");
    assert.equal(
      await page.getByRole("navigation", { name: "Navigation mobile" }).count(),
      0,
    );
    await page.locator(".search-submit").click();
    assert(await page.locator("#search-from-error").isVisible());
    await topScreenshot(page, "home-mobile");
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(base, { waitUntil: "networkidle" });
    await topScreenshot(page, "home-desktop");
    await page.goto(base + "/confidentialite", { waitUntil: "networkidle" });
    assert.equal(await page.locator("h1").innerText(), "Confidentialité");
    await page.goto(base + "/annulation", { waitUntil: "networkidle" });
    assert.equal(
      await page.locator("h1").innerText(),
      "Annulation et modification",
    );
    // Searchable controls must work with real long lists and accented terms.
    const cities = Array.from({ length: 30 }, (_, i) => ({
      id: i + 1,
      nom: `Ville ${i + 1}`,
      region: "Région de test",
    }));
    cities[28].nom = "Été 29";
    await page.route("**/destinations/public?**", (route) =>
      route.fulfill({ json: { ...pageOf(cities), pages: 1 } }),
    );
    await page.goto(base, { waitUntil: "networkidle" });
    const from = page.getByRole("combobox", {
      name: "Ville de départ",
      exact: true,
    });
    await from.fill("ete");
    await from.press("Enter");
    assert.equal(await from.inputValue(), "Été 29");
    await from.focus();
    await from.press("Escape");
    assert.equal(await from.inputValue(), "Été 29");
    const to = page.getByRole("combobox", {
      name: "Ville d’arrivée",
      exact: true,
    });
    await to.fill("Ville 30");
    await to.press("Enter");
    await page.locator(".search-submit").click();
    await page.waitForURL("**/recherche?**");
    assert.equal(new URL(page.url()).searchParams.get("from"), "29");
    assert.equal(new URL(page.url()).searchParams.get("to"), "30");
    await page.unroute("**/destinations/public?**");
    console.log(
      "PASS: 48 public viewport checks, menus, validation, information routes, long selectors and keyboard selection",
    );
    // Authenticated administration: no records are created or deleted.
    const env = Object.fromEntries(
      fs
        .readFileSync(".env", "utf8")
        .split(/\r?\n/)
        .filter((line) => /^[A-Z_]+=/.test(line))
        .map((line) => {
          const at = line.indexOf("=");
          return [
            line.slice(0, at),
            line
              .slice(at + 1)
              .trim()
              .replace(/^['"]|['"]$/g, ""),
          ];
        }),
    );
    await page.goto(base + "/login", { waitUntil: "networkidle" });
    await topScreenshot(page, "login-desktop");
    await page
      .locator("input[type=email]")
      .fill(env.DEFAULT_ADMIN_EMAIL || "admin@cooperative.local");
    await page
      .locator("input[type=password]")
      .fill(env.DEFAULT_ADMIN_PASSWORD || "Admin123!");
    await page
      .getByRole("button", { name: "Se connecter", exact: true })
      .click();
    await page.waitForURL("**/backoffice");
    await page.locator(".stats-grid .stat-card").first().waitFor();
    await topScreenshot(page, "workspace-desktop");
    await page.getByRole("button", { name: "Menu du compte" }).click();
    assert(
      await page
        .getByRole("button", { name: "Mon profil", exact: true })
        .isVisible(),
    );
    await page.keyboard.press("Escape");
    assert.equal(await page.locator(".dropdown-menu").count(), 0);
    await page.getByRole("button", { name: "Réduire le menu" }).click();
    assert(await page.locator(".app-sidebar.collapsed").count());
    await page.getByRole("button", { name: "Développer le menu" }).click();
    await page
      .getByRole("searchbox", { name: "Filtrer les modules" })
      .fill("réserv");
    assert.equal(await page.locator(".sidebar-link").count(), 1);
    await page.getByRole("searchbox", { name: "Filtrer les modules" }).fill("");
    const staffRoutes = [
      "/backoffice",
      "/departs",
      "/departs/new",
      "/reservations",
      "/reservations/new",
      "/vehicules",
      "/vehicules/new",
      "/chauffeurs",
      "/gares",
      "/cooperatives",
      "/itineraires",
      "/tarifs",
      "/finance",
      "/statistiques",
      "/planning",
      "/embarquement",
      "/users",
      "/roles",
    ];
    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: 950 });
      for (const path of staffRoutes) {
        await page.goto(base + path, { waitUntil: "networkidle" });
        assert.equal(await page.locator("h1").count(), 1, path);
        await noOverflow(page, `${path}@${width}`);
      }
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base + "/backoffice", { waitUntil: "networkidle" });
    const menu = page.getByRole("button", {
      name: "Ouvrir le menu",
      exact: true,
    });
    await menu.click();
    assert(
      await page
        .locator(".dashboard-main")
        .evaluate((element) => element.inert),
    );
    await topScreenshot(page, "workspace-mobile");
    await page.keyboard.press("Shift+Tab");
    assert(
      await page
        .locator(".app-sidebar")
        .evaluate((element) => element.contains(document.activeElement)),
    );
    await page.keyboard.press("Escape");
    assert.equal(await menu.getAttribute("aria-expanded"), "false");
    assert(
      await menu.evaluate((element) => element === document.activeElement),
    );
    console.log(
      "PASS: 54 staff viewport checks, actual admin login, permissions menu, collapse, filtering, dropdown and mobile focus",
    );
    // Passenger pages use isolated, deterministic read-only fixtures.
    const passenger = await browser.newContext({
      viewport: { width: 390, height: 844 },
    });
    await passenger.addInitScript(() =>
      localStorage.setItem(
        "cooperative_access_token",
        "local-read-only-fixture",
      ),
    );
    let requestedPage = 1,
      requestedQr = 0;
    await passenger.route("**/api/v1/**", async (route) => {
      const url = new URL(route.request().url());
      const path = url.pathname;
      if (path.endsWith("/auth/me"))
        return route.fulfill({
          json: {
            id: 9999,
            name: "Test",
            first_name: "Voyageur",
            email: "test@example.invalid",
            role: "passenger",
            roles: [],
            permissions: ["RESERVATION_READ", "BILLET_READ"],
            is_active: true,
          },
        });
      if (path.endsWith("/reservations")) {
        requestedPage = Number(url.searchParams.get("page") || 1);
        return route.fulfill({
          json: pageOf(
            Array.from({ length: requestedPage === 1 ? 12 : 2 }, (_, i) => ({
              id: i + 1,
              numero_reservation: `TEST-${requestedPage}-${i}`,
              statut: "PAYEE",
              montant_total: 40000,
              montant_paye: 10000,
              montant_restant: 30000,
              montant_a_rembourser: 0,
              places: [],
              depart: {
                date_depart: "2026-12-01",
                heure_depart: "08:00:00",
                cooperative: { nom: "Coopérative de test" },
              },
            })),
            14,
            requestedPage,
          ),
        });
      }
      if (path.endsWith("/billets"))
        return route.fulfill({
          json: pageOf([
            {
              id: 91,
              numero_billet: "BILLET-TEST",
              statut: "VALIDE",
              date_depart: "2026-12-01",
              heure_depart: "08:00",
              destination_depart: "Antananarivo",
              destination_arrivee: "Antsirabe",
              numero_place: 4,
            },
          ]),
        });
      if (path.endsWith("/billets/91/qr.png")) {
        requestedQr++;
        return route.fulfill({
          contentType: "image/png",
          body: Buffer.from(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j4iUAAAAASUVORK5CYII=",
            "base64",
          ),
        });
      }
      return route.fulfill({ json: pageOf([]) });
    });
    const client = await passenger.newPage();
    client.on("pageerror", (error) => errors.push(error.message));
    for (const path of [
      "/espace-client",
      "/mes-reservations",
      "/mes-billets",
      "/mon-profil",
    ]) {
      await client.goto(base + path, { waitUntil: "networkidle" });
      await noOverflow(client, path);
      assert.equal(await client.locator(".client-navigation").count(), 1);
    }
    await client.goto(base + "/mes-reservations", { waitUntil: "networkidle" });
    assert((await client.locator("h2").first().innerText()).includes("14"));
    await client.getByRole("button", { name: "Suivant", exact: true }).click();
    await client.waitForTimeout(300);
    assert.equal(requestedPage, 2);
    assert.equal(await client.locator(".client-reservation-card").count(), 2);
    await client.goto(base + "/mes-billets", { waitUntil: "networkidle" });
    await client.getByRole("button", { name: "Afficher mon QR Code" }).click();
    await client
      .getByRole("img", { name: "QR Code du billet BILLET-TEST" })
      .waitFor();
    assert.equal(requestedQr, 1);
    assert(
      await client
        .getByRole("link", { name: "Enregistrer le QR Code" })
        .isVisible(),
    );
    await topScreenshot(client, "passenger-tickets-mobile");
    console.log(
      "PASS: passenger navigation, true totals, server pagination and authenticated QR loading (isolated fixtures)",
    );
    assert.deepEqual(errors, [], "No JavaScript page errors");
    console.log(
      "PASS: all design checks completed; no payment or business records modified",
    );
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
