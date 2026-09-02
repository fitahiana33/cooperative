import '../../../core/network/api_client.dart';
import '../../../domain/entities/chauffeur/chauffeur.dart';
import '../../../domain/repositories/chauffeur/chauffeur_repository.dart';
import '../../dtos/chauffeur/chauffeur_dto.dart';

class ChauffeurRepositoryImpl implements ChauffeurRepository {
  final ApiClient apiClient;

  ChauffeurRepositoryImpl(this.apiClient);

  @override
  Future<List<ChauffeurEntity>> fetchChauffeurs({int page = 1, String? search}) async {
    final queryParams = {'page': page, if (search != null && search.isNotEmpty) 'search': search};
    final response = await apiClient.get('/chauffeurs', queryParameters: queryParams);
    final items = response.data['items'] as List;
    return items.map((json) => ChauffeurDto.fromJson(json).toEntity()).toList();
  }

  @override
  Future<ChauffeurEntity> getChauffeur(int id) async {
    final response = await apiClient.get('/chauffeurs/$id');
    return ChauffeurDto.fromJson(response.data).toEntity();
  }
}
