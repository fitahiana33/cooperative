class CooperativeEntity {
  final int id;
  final String nom;
  final String? sigle;
  final String? numeroAgrement;
  final String? adresse;
  final String? ville;
  final String? telephone;
  final String? email;
  final String? logoUrl;
  final bool isActive;
  final String createdAt;

  const CooperativeEntity({
    required this.id,
    required this.nom,
    this.sigle,
    this.numeroAgrement,
    this.adresse,
    this.ville,
    this.telephone,
    this.email,
    this.logoUrl,
    required this.isActive,
    required this.createdAt,
  });
}
