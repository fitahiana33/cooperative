import '../../../core/network/api_client.dart';
import '../../../domain/entities/vehicule/vehicule.dart';
import '../../../domain/entities/vehicule/vehicule_reference.dart';
import '../../../domain/repositories/vehicule/vehicule_repository.dart';
import '../../dtos/vehicule/vehicule_dto.dart';

class VehiculeRepositoryImpl implements VehiculeRepository {
  final ApiClient apiClient;

  VehiculeRepositoryImpl(this.apiClient);

  @override
  Future<List<VehiculeEntity>> fetchVehicules({int page = 1, String? search}) async {
    final queryParams = {'page': page, if (search != null && search.isNotEmpty) 'search': search};
    final response = await apiClient.get('/vehicules', queryParameters: queryParams);
    final items = response.data['items'] as List;
    return items.map((json) => VehiculeDto.fromJson(json).toEntity()).toList();
  }

  @override
  Future<VehiculeEntity> getVehicule(int id) async {
    final response = await apiClient.get('/vehicules/$id');
    return VehiculeDto.fromJson(response.data).toEntity();
  }

  Future<List<dynamic>> _fetchItems(String path) async {
    final response = await apiClient.get(path, queryParameters: {'page': 1, 'page_size': 100});
    final items = response.data['items'] as List;
    return items;
  }

  @override
  Future<List<MarqueOption>> fetchMarques() async {
    final items = await _fetchItems('/marques');
    return items.map((json) => MarqueOption.fromJson(json as Map<String, dynamic>)).toList();
  }

  @override
  Future<List<ModeleOption>> fetchModeles() async {
    final items = await _fetchItems('/modeles');
    return items.map((json) => ModeleOption.fromJson(json as Map<String, dynamic>)).toList();
  }

  @override
  Future<List<CooperativeOption>> fetchCooperatives() async {
    final items = await _fetchItems('/cooperatives');
    return items.map((json) => CooperativeOption.fromJson(json as Map<String, dynamic>)).toList();
  }

  @override
  Future<VehiculeEntity> createVehicule(Map<String, dynamic> data) async {
    final response = await apiClient.post('/vehicules', data: data);
    return VehiculeDto.fromJson(response.data).toEntity();
  }

  @override
  Future<VehiculeEntity> updateVehicule(int id, Map<String, dynamic> data) async {
    final response = await apiClient.put('/vehicules/$id', data: data);
    return VehiculeDto.fromJson(response.data).toEntity();
  }

  @override
  Future<VehiculeEntity> toggleVehicule(int id) async {
    final response = await apiClient.patch('/vehicules/$id/toggle');
    return VehiculeDto.fromJson(response.data).toEntity();
  }

  @override
  Future<void> deleteVehicule(int id) async {
    await apiClient.delete('/vehicules/$id');
  }
}
