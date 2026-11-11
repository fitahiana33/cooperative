export type PlaceStatus = "DISPONIBLE" | "RESERVEE" | "BLOQUEE" | "OCCUPEE";
export type ReservationStatus =
  | "EN_ATTENTE"
  | "CONFIRMEE"
  | "PAYEE"
  | "ANNULEE"
  | "EXPIREE"
  | "EMBARQUEE"
  | "TERMINEE";

export interface DepartPlace {
  id: number;
  id_depart: number;
  numero_place: number;
  statut: PlaceStatus;
}

export interface ReservationPlaceInput {
  id_depart_place: number;
  nom_passager?: string;
  telephone_passager?: string;
}

export interface Reservation {
  montant_rembourse?: number;
  etat_paiement?: "NON_REGLE" | "ACOMPTE_RECU" | "REGLE" | "A_REMBOURSER" | "REMBOURSE";
  peut_annuler?: boolean;
  peut_payer?: boolean;
  minimum_a_payer?: number;
  date_limite_annulation?: string | null;
  id: number;
  numero_reservation: string;
  id_depart: number;
  id_user: number;
  nom_reservataire?: string | null;
  telephone_reservataire?: string | null;
  email_reservataire?: string | null;
  montant_total: number;
  montant_paye: number;
  montant_restant: number;
  montant_a_rembourser: number;
  statut: ReservationStatus;
  date_expiration?: string | null;
  created_at: string;
  depart?: {
    id: number;
    id_itineraire: number;
    id_cooperative: number;
    id_vehicule: number;
    date_depart: string;
    heure_depart: string;
    nombre_places: number;
    places_reservees: number;
    places_disponibles: number;
    statut: string;
    itineraire?: {
      id: number;
      destination_depart?: { id: number; nom: string } | null;
      destination_arrivee?: { id: number; nom: string } | null;
    } | null;
    cooperative?: { id: number; nom: string } | null;
    vehicule?: {
      id: number;
      immatriculation: string;
      nombre_places: number;
      places_avant?: number;
      places_par_rangee?: number;
    } | null;
  };
  places: Array<{
    id: number;
    id_depart_place: number;
    nom_passager: string;
    telephone_passager?: string;
    depart_place?: DepartPlace;
    billet?: {
      id: number;
      numero_billet: string;
      qr_code_uuid: string;
      statut: string;
    } | null;
  }>;
}

export interface PublicReservationCreate {
  cle_idempotence?: string;
  id_depart: number;
  places: ReservationPlaceInput[];
  nom_reservataire: string;
  telephone_reservataire: string;
  email_reservataire?: string;
  montant_avance: number;
  fournisseur: "MVOLA" | "ORANGE_MONEY" | "AIRTEL_MONEY";
}

export interface PublicReservationResult {
  reservation: Reservation;
  access_token: string;
  payment: import("./../finance/model").OnlinePayment | null;
  acompte_minimum: number;
}
