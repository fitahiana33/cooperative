export interface Caisse {
  id: number
  id_gare: number
  id_agent: number
  date_ouverture: string
  montant_ouverture: number
  date_cloture?: string | null
  montant_cloture?: number | null
  statut: string
  total_recettes: number
  total_depenses: number
  total_commissions: number
  solde: number
}

export interface Paiement {
  id: number
  id_reservation: number
  montant: number
  methode: string
  reference_paiement?: string | null
  statut: string
  date_paiement: string
  id_agent?: number | null
}
