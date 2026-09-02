import '../../../domain/entities/vehicule/vehicule.dart';

class VehiculeDto {
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

  VehiculeDto({
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

  factory VehiculeDto.fromJson(Map<String, dynamic> json) {
    return VehiculeDto(
      id: json['id'] as int,
      idModele: json['id_modele'] as int? ?? 0,
      idCooperative: json['id_cooperative'] as int? ?? 0,
      immatriculation: json['immatriculation'] as String? ?? '',
      chevaux: json['chevaux'] as int?,
      nombrePlaces: json['nombre_places'] as int? ?? 14,
      disponibilite: json['disponibilite'] as bool? ?? true,
      etat: json['etat'] as String? ?? 'BON_ETAT',
      description: json['description'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      createdAt: json['created_at'] as String? ?? '',
    );
  }

  VehiculeEntity toEntity() {
    return VehiculeEntity(
      id: id,
      idModele: idModele,
      idCooperative: idCooperative,
      immatriculation: immatriculation,
      chevaux: chevaux,
      nombrePlaces: nombrePlaces,
      disponibilite: disponibilite,
      etat: etat,
      description: description,
      isActive: isActive,
      createdAt: createdAt,
    );
  }
}
