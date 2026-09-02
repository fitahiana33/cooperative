class ChauffeurEntity {
  final int id;
  final int idUser;
  final int idCooperative;
  final String numeroPermis;
  final String categoriePermis;
  final String dateExpirationPermis;
  final bool disponibilite;
  final bool isActive;
  final String createdAt;

  const ChauffeurEntity({
    required this.id,
    required this.idUser,
    required this.idCooperative,
    required this.numeroPermis,
    required this.categoriePermis,
    required this.dateExpirationPermis,
    required this.disponibilite,
    required this.isActive,
    required this.createdAt,
  });
}
