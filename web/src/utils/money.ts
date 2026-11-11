/** A common display convention for fares and receipts; calculations stay server-side. */
export function formatMoney(
  value: number | string | null | undefined,
  currency = "MGA",
): string {
  if (value === null || value === undefined || !Number.isFinite(Number(value)))
    return "—";
  const unit = currency.toUpperCase() === "MGA" ? "Ar" : currency;
  return `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(Number(value))} ${unit}`;
}
