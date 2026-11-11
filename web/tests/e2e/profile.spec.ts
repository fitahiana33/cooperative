import { expect, test } from "playwright/test";

const person = {
  id: 42,
  name: "Rabe",
  first_name: "Miora",
  email: "miora@example.com",
  role: "agent_gare",
  roles: [],
  permissions: [],
  is_active: true,
  created_at: "2026-01-01",
  photo_version: null as string | null,
};
const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII=",
  "base64",
);

for (const role of ["agent_gare", "admin", "passenger"]) {
  test(`${role} has a personal profile without accessing global user records`, async ({
    page,
  }) => {
    const user = { ...person, role };
    const globalReads: string[] = [];
    await page.addInitScript(() =>
      localStorage.setItem("cooperative_access_token", "profile-session"),
    );
    await page.route("**/api/v1/**", (route) => {
      if (/\/users\/\d+(?:\?|$)/.test(route.request().url()))
        globalReads.push(route.request().url());
      return route.fulfill({ json: { items: [], total: 0 } });
    });
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ json: user }),
    );
    await page.goto("/profil");
    await expect(page).toHaveURL(
      role === "passenger" ? /\/mon-profil$/ : /\/profil$/,
    );
    await expect(
      page.getByRole("heading", { name: "Mon profil", exact: true }).last(),
    ).toBeVisible();
    await expect(page.getByLabel("Prénom", { exact: true })).toHaveValue(
      "Miora",
    );
    expect(globalReads).toEqual([]);
  });
}

test("account menu, tabs and profile save work for staff without USER_READ", async ({
  page,
}) => {
  let user = { ...person };
  await page.addInitScript(() =>
    localStorage.setItem("cooperative_access_token", "profile-session"),
  );
  await page.route("**/api/v1/**", (route) =>
    route.fulfill({ json: { items: [], total: 0 } }),
  );
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ json: user }),
  );
  await page.route("**/api/v1/users/me", (route) => {
    user = { ...user, ...route.request().postDataJSON() };
    return route.fulfill({ json: user });
  });
  await page.goto("/backoffice");
  await page.getByRole("button", { name: "Menu du compte" }).click();
  await page.getByRole("button", { name: "Mon profil", exact: true }).click();
  await expect(page).toHaveURL(/\/profil$/);
  await page.getByLabel("Prénom", { exact: true }).fill("Hanitra");
  await page.getByRole("tab", { name: "Sécurité" }).click();
  await expect(page.getByLabel("Prénom", { exact: true })).toBeHidden();
  await page.getByRole("tab", { name: "Informations", exact: true }).click();
  await expect(page.getByLabel("Prénom", { exact: true })).toHaveValue(
    "Hanitra",
  );
  await page
    .getByRole("button", { name: "Enregistrer les modifications" })
    .click();
  await expect(
    page.getByRole("status").filter({ hasText: "enregistrées" }),
  ).toBeVisible();
  await expect(page.locator(".header-user-copy")).toContainText("Hanitra");
});

for (const [role, width] of [
  ["agent_gare", 390],
  ["agent_gare", 1280],
  ["passenger", 390],
  ["passenger", 1280],
] as const) {
  test(`${role} photo upload and removal synchronize avatar at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    let user = { ...person, role };
    let uploads = 0;
    await page.addInitScript(() =>
      localStorage.setItem("cooperative_access_token", "profile-session"),
    );
    await page.route("**/api/v1/**", (route) =>
      route.fulfill({ json: { items: [], total: 0 } }),
    );
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ json: user }),
    );
    await page.route("**/api/v1/users/me/photo", (route) => {
      expect(route.request().headers().authorization).toBe(
        "Bearer profile-session",
      );
      if (route.request().method() === "GET")
        return route.fulfill({ body: png, contentType: "image/png" });
      if (route.request().method() === "PUT") {
        uploads++;
        expect(route.request().headers()["content-type"]).toContain(
          "multipart/form-data; boundary=",
        );
        user = { ...user, photo_version: "a".repeat(32) };
      } else user = { ...user, photo_version: null };
      return route.fulfill({ json: user });
    });
    await page.goto("/profil");
    await page.getByLabel("Choisir une photo de profil").setInputFiles({
      name: "portrait.png",
      mimeType: "image/png",
      buffer: png,
    });
    await expect(page.locator(".personal-identity img")).toBeVisible();
    await expect(
      page.locator(
        role === "passenger"
          ? ".public-header .account-avatar img"
          : ".app-header .account-avatar img",
      ),
    ).toBeVisible();
    expect(uploads).toBe(1);
    expect(
      await page
        .locator(".personal-identity img")
        .evaluate((el: HTMLImageElement) => el.complete && el.naturalWidth > 0),
    ).toBe(true);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await page.getByRole("button", { name: "Supprimer la photo" }).click();
    await expect(page.locator(".personal-identity img")).toHaveCount(0);
    await expect(
      page.locator(
        role === "passenger"
          ? ".public-header .account-avatar img"
          : ".app-header .account-avatar img",
      ),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Ajouter une photo" }),
    ).toBeVisible();
  });
}

test("invalid files and password confirmation are checked before requests; password change ends session", async ({
  page,
}) => {
  let changes = 0;
  await page.addInitScript(() =>
    localStorage.setItem("cooperative_access_token", "profile-session"),
  );
  await page.route("**/api/v1/**", (route) =>
    route.fulfill({ json: { items: [], total: 0 } }),
  );
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ json: person }),
  );
  await page.route("**/api/v1/users/me/photo", () => {
    throw new Error("Invalid file reached API");
  });
  await page.route("**/api/v1/users/me/password", (route) => {
    changes++;
    return route.fulfill({ status: 204 });
  });
  await page.goto("/profil");
  await page.getByLabel("Choisir une photo de profil").setInputFiles({
    name: "fake.svg",
    mimeType: "image/svg+xml",
    buffer: Buffer.from("<svg/>"),
  });
  await expect(page.getByRole("alert")).toContainText("JPEG");
  await page.getByRole("tab", { name: "Sécurité" }).click();
  await page
    .getByLabel("Mot de passe actuel", { exact: true })
    .fill("Actuel123");
  await page
    .getByLabel("Nouveau mot de passe", { exact: true })
    .fill("Nouveau123");
  await page
    .getByLabel("Confirmer le nouveau mot de passe", { exact: true })
    .fill("Different123");
  await page.getByRole("button", { name: "Modifier le mot de passe" }).click();
  await expect(page.getByRole("alert")).toContainText("identiques");
  expect(changes).toBe(0);
  await page
    .getByLabel("Confirmer le nouveau mot de passe", { exact: true })
    .fill("Nouveau123");
  await page.getByRole("button", { name: "Modifier le mot de passe" }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect(changes).toBe(1);
  expect(
    await page.evaluate(() => localStorage.getItem("cooperative_access_token")),
  ).toBeNull();
});
