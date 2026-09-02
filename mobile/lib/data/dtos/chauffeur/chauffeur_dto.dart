import '../../../domain/entities/chauffeur/chauffeur.dart';

class ChauffeurDto {
  final int id;
  final int idUser;
  final int idCooperative;
  final String numeroPermis;
  final String categoriePermis;
  final String dateExpirationPermis;
  final bool disponibilite;
  final bool isActive;
  final String createdAt;

  ChauffeurDto({
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

  factory ChauffeurDto.fromJson(Map<String, dynamic> json) {
    return ChauffeurDto(
      id: json['id'] as int,
      idUser: json['id_user'] as int? ?? 0,
      idCooperative: json['id_cooperative'] as int? ?? 0,
      numeroPermis: json['numero_permis'] as String? ?? '',
      categoriePermis: json['categorie_permis'] as String? ?? '',
      dateExpirationPermis: json['date_expiration_permis'] as String? ?? '',
      disponibilite: json['disponibilite'] as bool? ?? true,
      isActive: json['is_active'] as bool? ?? true,
      createdAt: json['created_at'] as String? ?? '',
    );
  }

  ChauffeurEntity toEntity() {
    return ChauffeurEntity(
      id: id,
      idUser: idUser,
      idCooperative: idCooperative,
      numeroPermis: numeroPermis,
      categoriePermis: categoriePermis,
      dateExpirationPermis: dateExpirationPermis,
      disponibilite: disponibilite,
      isActive: isActive,
      createdAt: createdAt,
    );
  }
}
