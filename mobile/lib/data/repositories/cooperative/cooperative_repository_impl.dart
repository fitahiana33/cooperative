import '../../../domain/entities/cooperative/cooperative_entity.dart';
import '../../../domain/repositories/cooperative/cooperative_repository.dart';
import '../../datasources/cooperative/cooperative_remote_datasource.dart';

class CooperativeRepositoryImpl implements CooperativeRepository {
  final CooperativeRemoteDataSource _remoteDataSource;

  CooperativeRepositoryImpl(this._remoteDataSource);

  @override
  Future<List<CooperativeEntity>> getCooperatives() async {
    return await _remoteDataSource.getCooperatives();
  }

  @override
  Future<CooperativeEntity> createCooperative({
    required String nom,
    String? sigle,
    String? numeroAgrement,
    String? adresse,
    String? ville,
    String? telephone,
    String? email,
    String? logoUrl,
  }) async {
    final payload = {
      'nom': nom,
      if (sigle != null && sigle.isNotEmpty) 'sigle': sigle,
      if (numeroAgrement != null && numeroAgrement.isNotEmpty) 'numero_agrement': numeroAgrement,
      if (adresse != null && adresse.isNotEmpty) 'adresse': adresse,
      if (ville != null && ville.isNotEmpty) 'ville': ville,
      if (telephone != null && telephone.isNotEmpty) 'telephone': telephone,
      if (email != null && email.isNotEmpty) 'email': email,
      if (logoUrl != null && logoUrl.isNotEmpty) 'logo_url': logoUrl,
    };
    return await _remoteDataSource.createCooperative(payload);
  }

  @override
  Future<CooperativeEntity> toggleCooperativeStatus(int id) async {
    return await _remoteDataSource.toggleCooperativeStatus(id);
  }
}
