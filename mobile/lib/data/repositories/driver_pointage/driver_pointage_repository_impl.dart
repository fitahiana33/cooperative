import '../../../core/network/api_client.dart';
import '../../../domain/repositories/driver_pointage/driver_pointage_repository.dart';

class DriverPointageRepositoryImpl implements DriverPointageRepository {
  final ApiClient _apiClient;

  DriverPointageRepositoryImpl(this._apiClient);

  @override
  Future<List<Map<String, dynamic>>> listMyDepartures() async {
    final response = await _apiClient.get('/departs/mes-departs', queryParameters: {'page': 1, 'page_size': 50});
    final data = Map<String, dynamic>.from(response.data as Map);
    return (data['items'] as List? ?? const []).whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }

  @override
  Future<void> pointage(int departId, String type) async {
    await _apiClient.post('/departs/$departId/pointage', data: {'type': type});
  }
}
