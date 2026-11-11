import { expect, test } from "playwright/test";

const pageResult = (items: unknown[]) => ({
  items,
  total: items.length,
  page: 1,
  pages: items.length ? 1 : 0,
  page_size: 100,
});

test("le remboursement s’ouvre dans une modale et utilise la caisse choisie", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("cooperative_access_token", "admin-session"),
  );

  const cashDesk = {
    id: 17,
    id_gare: 4,
    id_agent: 1,
    date_ouverture: "2026-11-11T08:00:00Z",
    montant_ouverture: 100000,
    statut: "OUVERTE",
    total_recettes: 50000,
    total_depenses: 0,
    total_commissions: 0,
    solde: 150000,
  };
  const payment = {
    id: 71,
    id_reservation: 9,
    numero_reservation: "RES-REMBOURSEMENT",
    montant: 25000,
    methode: "MOBILE_MONEY",
    reference_paiement: "PAY-71",
    statut: "VALIDE",
    date_paiement: "2026-11-10T09:00:00Z",
    remboursement_demande_le: "2026-11-11T07:30:00Z",
  };
  let refundRequest: { url: string; body: unknown } | null = null;

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    if (path.endsWith("/auth/me")) {
      await route.fulfill({
        json: {
          id: 1,
          name: "Admin",
          first_name: "Système",
          email: "admin@example.com",
          role: "admin",
          roles: [{ id: 1, libelle: "admin" }],
          permissions: ["PAIEMENT_REFUND"],
          is_active: true,
        },
      });
      return;
    }
    if (path.endsWith("/caisses")) {
      await route.fulfill({ json: pageResult([cashDesk]) });
      return;
    }
    if (path.endsWith("/gares")) {
      await route.fulfill({
        json: pageResult([
          { id: 4, nom: "Gare centrale", ville: "Antananarivo" },
        ]),
      });
      return;
    }
    if (path.endsWith("/paiements/71/rembourser")) {
      refundRequest = { url: request.url(), body: request.postDataJSON() };
      await route.fulfill({
        json: {
          ...payment,
          statut: "REMBOURSE",
          methode_remboursement: "ESPECES",
        },
      });
      return;
    }
    if (path.endsWith("/paiements")) {
      const refundable = url.searchParams.get("a_rembourser") === "true";
      await route.fulfill({ json: pageResult(refundable ? [payment] : []) });
      return;
    }
    await route.fulfill({ json: pageResult([]) });
  });

  await page.goto("/finance");
  await page.getByRole("tab", { name: /Remboursements/ }).click();
  await page
    .getByLabel("Choisir une caisse ouverte")
    .selectOption(String(cashDesk.id));
  await page.getByRole("button", { name: "Rembourser" }).click();

  const dialog = page.getByRole("dialog", { name: /Rembourser/ });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByLabel("Caisse qui rend les espèces")).toHaveValue(
    String(cashDesk.id),
  );
  await dialog
    .getByRole("button", { name: "Confirmer le remboursement" })
    .click();

  await expect.poll(() => refundRequest).not.toBeNull();
  expect(refundRequest!.url).toContain("id_caisse=17");
  expect(refundRequest!.body).toEqual({ methode: "ESPECES" });
  await expect(page.getByText("Remboursement enregistré.")).toBeVisible();
});

test("un remboursement Mobile Money exige une référence externe", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("cooperative_access_token", "admin-session"),
  );
  const payment = {
    id: 72,
    id_reservation: 10,
    numero_reservation: "RES-EXTERNE",
    montant: 15000,
    methode: "MOBILE_MONEY",
    reference_paiement: "PAY-72",
    statut: "VALIDE",
    date_paiement: "2026-11-10T09:00:00Z",
  };
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    if (path.endsWith("/auth/me")) {
      await route.fulfill({
        json: {
          id: 1,
          name: "Admin",
          first_name: "Système",
          email: "admin@example.com",
          role: "admin",
          roles: [],
          permissions: ["PAIEMENT_REFUND"],
          is_active: true,
        },
      });
      return;
    }
    if (path.endsWith("/paiements")) {
      const recent = url.searchParams.get("a_rembourser") !== "true";
      await route.fulfill({ json: pageResult(recent ? [payment] : []) });
      return;
    }
    await route.fulfill({ json: pageResult([]) });
  });

  await page.goto("/finance");
  await page.getByRole("tab", { name: /Paiements récents/ }).click();
  await page.getByRole("button", { name: "Rembourser" }).click();
  const dialog = page.getByRole("dialog", { name: /Rembourser/ });
  await dialog.getByLabel("Mode de remboursement").selectOption("MOBILE_MONEY");
  await expect(
    dialog.getByText(/ne déclenche pas elle-même le transfert/),
  ).toBeVisible();
  await dialog
    .getByRole("button", { name: "Confirmer le remboursement" })
    .click();
  await expect(dialog.getByRole("alert")).toContainText("référence");
});
