import '../../entities/cooperative/cooperative_entity.dart';
import '../../repositories/cooperative/cooperative_repository.dart';

class CooperativeService {
  final CooperativeRepository _repository;

  CooperativeService(this._repository);

  Future<List<CooperativeEntity>> getCooperatives() => _repository.getCooperatives();

  Future<CooperativeEntity> createCooperative({
    required String nom,
    String? sigle,
    String? numeroAgrement,
    String? adresse,
    String? ville,
    String? telephone,
    String? email,
    String? logoUrl,
  }) {
    return _repository.createCooperative(
      nom: nom,
      sigle: sigle,
      numeroAgrement: numeroAgrement,
      adresse: adresse,
      ville: ville,
      telephone: telephone,
      email: email,
      logoUrl: logoUrl,
    );
  }

  Future<CooperativeEntity> toggleCooperativeStatus(int id) => _repository.toggleCooperativeStatus(id);
}
