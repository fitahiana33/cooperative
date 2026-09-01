import '../../../domain/entities/gare/gare_entity.dart';
import '../../../domain/repositories/gare/gare_repository.dart';
import '../../datasources/gare/gare_remote_datasource.dart';

class GareRepositoryImpl implements GareRepository {
  final GareRemoteDataSource _remoteDataSource;

  GareRepositoryImpl(this._remoteDataSource);

  @override
  Future<List<GareEntity>> getGares() async {
    return await _remoteDataSource.getGares();
  }

  @override
  Future<GareEntity> createGare({
    required String nom,
    required String ville,
    required String adresse,
    String? telephone,
    String? email,
    double? latitude,
    double? longitude,
  }) async {
    final payload = {
      'nom': nom,
      'ville': ville,
      'adresse': adresse,
      if (telephone != null && telephone.isNotEmpty) 'telephone': telephone,
      if (email != null && email.isNotEmpty) 'email': email,
      if (latitude != null) 'latitude': latitude,
      if (longitude != null) 'longitude': longitude,
    };
    return await _remoteDataSource.createGare(payload);
  }

  @override
  Future<GareEntity> toggleGareStatus(int gareId) async {
    return await _remoteDataSource.toggleGareStatus(gareId);
  }
}
