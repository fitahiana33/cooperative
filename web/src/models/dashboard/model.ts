export interface DashboardDeparture {
  id: number
  id_itineraire: number
  date_depart: string
  heure_depart: string
  statut: string
  nombre_places: number
  places_reservees: number
  places_disponibles: number
  itineraire?: {
    destination_depart?: { nom: string }
    destination_arrivee?: { nom: string }
  }
  vehicule?: { immatriculation: string }
}

export interface DashboardSummary {
  date: string
  departs_du_jour: number
  reservations_du_jour: number
  places_disponibles: number
  departs_annules: number
  departs_retardes: number
  departs_complets: number
  reservations_annulees: number
  cooperatives_actives: number
  vehicules_actifs: number
  chauffeurs_actifs: number
  passagers_du_jour: number
  recettes_du_jour: number | string
  departs_imminents: DashboardDeparture[]
}

export interface DailyDepartureStatistic {
  date: string
  total: number
  places_reservees: number
  places_total: number
}

export interface DailyReservationStatistic {
  date: string
  total: number
}

export interface StatisticsComparisonMetric {
  current: number
  previous: number
}

export interface DashboardStatistics {
  date_from: string
  date_to: string
  departs: DailyDepartureStatistic[]
  reservations: DailyReservationStatistic[]
  destinations: Array<{ id_itineraire: number; reservations: number }>
  comparison: {
    previous_from: string
    previous_to: string
    departs: StatisticsComparisonMetric
    reservations: StatisticsComparisonMetric
    remplissage: StatisticsComparisonMetric
  }
}
