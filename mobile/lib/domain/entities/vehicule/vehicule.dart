class VehiculeEntity {
  final int id;
  final int idModele;
  final int idCooperative;
  final String immatriculation;
  final int? chevaux;
  final int nombrePlaces;
  final bool disponibilite;
  final String etat;
  final String? description;
  final bool isActive;
  final String createdAt;

  const VehiculeEntity({
    required this.id,
    required this.idModele,
    required this.idCooperative,
    required this.immatriculation,
    this.chevaux,
    required this.nombrePlaces,
    required this.disponibilite,
    required this.etat,
    this.description,
    required this.isActive,
    required this.createdAt,
  });
}
