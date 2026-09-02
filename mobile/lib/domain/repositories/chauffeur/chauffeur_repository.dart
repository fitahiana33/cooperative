import '../../entities/chauffeur/chauffeur.dart';

abstract class ChauffeurRepository {
  Future<List<ChauffeurEntity>> fetchChauffeurs({int page = 1, String? search});
  Future<ChauffeurEntity> getChauffeur(int id);
}
