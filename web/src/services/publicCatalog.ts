import { destinationService } from "./destination/service";
import { gareService } from "./gare/service";

import { allPages } from "./pagination";

export async function publicCatalog() {
  const [destinations, gares] = await Promise.all([
    allPages(destinationService.publicList),
    allPages(gareService.publicList),
  ]);
  return { destinations: destinations.items, gares: gares.items };
}
