class GareEntity {
  final int id;
  final String nom;
  final String ville;
  final String adresse;
  final String? telephone;
  final String? email;
  final double? latitude;
  final double? longitude;
  final bool isActive;
  final String createdAt;

  const GareEntity({
    required this.id,
    required this.nom,
    required this.ville,
    required this.adresse,
    this.telephone,
    this.email,
    this.latitude,
    this.longitude,
    required this.isActive,
    required this.createdAt,
  });
}
