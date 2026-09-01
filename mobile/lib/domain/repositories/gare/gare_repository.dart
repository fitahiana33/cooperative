import '../../entities/gare/gare_entity.dart';

abstract class GareRepository {
  Future<List<GareEntity>> getGares();
  Future<GareEntity> createGare({
    required String nom,
    required String ville,
    required String adresse,
    String? telephone,
    String? email,
    double? latitude,
    double? longitude,
  });
  Future<GareEntity> toggleGareStatus(int gareId);
}
