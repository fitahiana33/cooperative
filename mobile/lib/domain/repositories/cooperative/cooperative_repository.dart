import '../../entities/cooperative/cooperative_entity.dart';

abstract class CooperativeRepository {
  Future<List<CooperativeEntity>> getCooperatives();
  Future<CooperativeEntity> createCooperative({
    required String nom,
    String? sigle,
    String? numeroAgrement,
    String? adresse,
    String? ville,
    String? telephone,
    String? email,
    String? logoUrl,
  });
  Future<CooperativeEntity> toggleCooperativeStatus(int id);
}
