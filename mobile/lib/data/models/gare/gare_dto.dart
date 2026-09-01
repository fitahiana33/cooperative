import '../../../domain/entities/gare/gare_entity.dart';

class GareDto extends GareEntity {
  const GareDto({
    required super.id,
    required super.nom,
    required super.ville,
    required super.adresse,
    super.telephone,
    super.email,
    super.latitude,
    super.longitude,
    required super.isActive,
    required super.createdAt,
  });

  factory GareDto.fromJson(Map<String, dynamic> json) {
    return GareDto(
      id: json['id'] as int,
      nom: json['nom'] as String,
      ville: json['ville'] as String,
      adresse: json['adresse'] as String? ?? '',
      telephone: json['telephone'] as String?,
      email: json['email'] as String?,
      latitude: json['latitude'] != null ? (json['latitude'] as num).toDouble() : null,
      longitude: json['longitude'] != null ? (json['longitude'] as num).toDouble() : null,
      isActive: json['is_active'] as bool? ?? true,
      createdAt: json['created_at'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nom': nom,
      'ville': ville,
      'adresse': adresse,
      'telephone': telephone,
      'email': email,
      'latitude': latitude,
      'longitude': longitude,
      'is_active': isActive,
      'created_at': createdAt,
    };
  }
}
