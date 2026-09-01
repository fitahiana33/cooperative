import '../../../domain/entities/cooperative/cooperative_entity.dart';

class CooperativeDto extends CooperativeEntity {
  const CooperativeDto({
    required super.id,
    required super.nom,
    super.sigle,
    super.numeroAgrement,
    super.adresse,
    super.ville,
    super.telephone,
    super.email,
    super.logoUrl,
    required super.isActive,
    required super.createdAt,
  });

  factory CooperativeDto.fromJson(Map<String, dynamic> json) {
    return CooperativeDto(
      id: json['id'] as int,
      nom: json['nom'] as String,
      sigle: json['sigle'] as String?,
      numeroAgrement: json['numero_agrement'] as String?,
      adresse: json['adresse'] as String?,
      ville: json['ville'] as String?,
      telephone: json['telephone'] as String?,
      email: json['email'] as String?,
      logoUrl: json['logo_url'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      createdAt: json['created_at'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nom': nom,
      'sigle': sigle,
      'numero_agrement': numeroAgrement,
      'adresse': adresse,
      'ville': ville,
      'telephone': telephone,
      'email': email,
      'logo_url': logoUrl,
      'is_active': isActive,
      'created_at': createdAt,
    };
  }
}
