import '../../entities/gare/gare_entity.dart';
import '../../repositories/gare/gare_repository.dart';

class GareService {
  final GareRepository _repository;

  GareService(this._repository);

  Future<List<GareEntity>> getGares() => _repository.getGares();

  Future<GareEntity> createGare({
    required String nom,
    required String ville,
    required String adresse,
    String? telephone,
    String? email,
    double? latitude,
    double? longitude,
  }) {
    return _repository.createGare(
      nom: nom,
      ville: ville,
      adresse: adresse,
      telephone: telephone,
      email: email,
      latitude: latitude,
      longitude: longitude,
    );
  }

  Future<GareEntity> toggleGareStatus(int gareId) => _repository.toggleGareStatus(gareId);
}
