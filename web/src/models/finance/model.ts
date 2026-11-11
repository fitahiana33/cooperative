export interface Caisse {
  id: number
  id_gare: number
  id_agent: number
  date_ouverture: string
  montant_ouverture: number
  date_cloture?: string | null
  montant_cloture?: number | null
  ecart_cloture?: number | null
  statut: string
  total_recettes: number
  total_depenses: number
  total_commissions: number
  solde: number
}

export interface Paiement {
  verification_requise?: boolean;
  date_validation?: string | null;
  date_remboursement?: string | null;
  methode_remboursement?: string | null;
  reference_remboursement?: string | null;
  id: number
  id_reservation: number
  numero_reservation?: string | null
  montant: number
  methode: string
  reference_paiement?: string | null
  statut: string
  date_paiement: string
  id_agent?: number | null
  remboursement_demande_le?: string | null
}

export interface OnlinePayment {
  verification_requise?: boolean;
  id_paiement: number
  statut: string
  fournisseur: string
  reference_paiement: string
  montant: number
  message: string
  checkout_url?: string | null
  acompte_minimum?: number | null
  montant_restant?: number | null
}
