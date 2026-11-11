import { localIsoDate } from "./date";

export interface TravelSearch {
  from: string;
  to: string;
  date: string;
  dateTo: string;
  passengers: string;
}

/** Shared client checks; the API remains authoritative for availability. */
export function validateTravelSearch(
  filters: TravelSearch,
  requireCities = false,
): string {
  if (requireCities && (!filters.from || !filters.to))
    return "Choisissez une ville de départ et une destination.";
  if (filters.from && filters.from === filters.to)
    return "Le départ et la destination doivent être différents.";
  const validDate = (date: string) =>
    /^\d{4}-\d{2}-\d{2}$/.test(date) &&
    !Number.isNaN(Date.parse(`${date}T00:00:00`)) &&
    localIsoDate(new Date(`${date}T00:00:00`)) === date;
  if (!validDate(filters.date) || filters.date < localIsoDate())
    return "Choisissez une date de départ à partir d’aujourd’hui.";
  if (
    filters.dateTo &&
    (!validDate(filters.dateTo) || filters.dateTo < filters.date)
  )
    return "La date de fin doit suivre la date de départ.";
  const passengers = Number(filters.passengers);
  if (!Number.isInteger(passengers) || passengers < 1 || passengers > 10)
    return "Choisissez entre 1 et 10 passagers.";
  return "";
}
