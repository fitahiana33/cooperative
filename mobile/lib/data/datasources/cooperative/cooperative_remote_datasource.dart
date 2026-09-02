import '../../../core/network/api_client.dart';
import '../../models/cooperative/cooperative_dto.dart';

abstract class CooperativeRemoteDataSource {
  Future<List<CooperativeDto>> getCooperatives();
  Future<CooperativeDto> createCooperative(Map<String, dynamic> data);
  Future<CooperativeDto> toggleCooperativeStatus(int id);
}

class CooperativeRemoteDataSourceImpl implements CooperativeRemoteDataSource {
  final ApiClient _apiClient;

  CooperativeRemoteDataSourceImpl(this._apiClient);

  @override
  Future<List<CooperativeDto>> getCooperatives() async {
    final response = await _apiClient.get('/cooperatives', queryParameters: {'page': 1, 'page_size': 100});
    final List list = response.data['items'] as List;
    return list.map((json) => CooperativeDto.fromJson(json as Map<String, dynamic>)).toList();
  }

  @override
  Future<CooperativeDto> createCooperative(Map<String, dynamic> data) async {
    final response = await _apiClient.post('/cooperatives', data: data);
    return CooperativeDto.fromJson(response.data as Map<String, dynamic>);
  }

  @override
  Future<CooperativeDto> toggleCooperativeStatus(int id) async {
    final response = await _apiClient.patch('/cooperatives/$id/toggle');
    return CooperativeDto.fromJson(response.data as Map<String, dynamic>);
  }
}
