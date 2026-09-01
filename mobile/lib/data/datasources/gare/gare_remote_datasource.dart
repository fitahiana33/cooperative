import '../../../core/network/api_client.dart';
import '../../models/gare/gare_dto.dart';

abstract class GareRemoteDataSource {
  Future<List<GareDto>> getGares();
  Future<GareDto> createGare(Map<String, dynamic> data);
  Future<GareDto> toggleGareStatus(int gareId);
}

class GareRemoteDataSourceImpl implements GareRemoteDataSource {
  final ApiClient _apiClient;

  GareRemoteDataSourceImpl(this._apiClient);

  @override
  Future<List<GareDto>> getGares() async {
    final response = await _apiClient.get('/management/gares');
    final List list = response.data as List;
    return list.map((json) => GareDto.fromJson(json as Map<String, dynamic>)).toList();
  }

  @override
  Future<GareDto> createGare(Map<String, dynamic> data) async {
    final response = await _apiClient.post('/management/gares', data: data);
    return GareDto.fromJson(response.data as Map<String, dynamic>);
  }

  @override
  Future<GareDto> toggleGareStatus(int gareId) async {
    final response = await _apiClient.patch('/management/gares/$gareId/toggle');
    return GareDto.fromJson(response.data as Map<String, dynamic>);
  }
}
