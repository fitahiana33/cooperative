import '../../../core/network/api_client.dart';
import '../../../domain/repositories/reservation/reservation_repository.dart';

class ReservationRepositoryImpl implements ReservationRepository {
  final ApiClient _apiClient;

  ReservationRepositoryImpl(this._apiClient);

  List<Map<String, dynamic>> _items(dynamic data) {
    final value = data is Map && data['items'] is List ? data['items'] : data;
    if (value is! List) return [];
    return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }

  @override
  Future<List<Map<String, dynamic>>> listDepartures() async {
    final today = DateTime.now().toIso8601String().substring(0, 10);
    final response = await _apiClient.get('/departs', queryParameters: {
      'page': 1, 'page_size': 100, 'date_from': today, 'sort_by': 'date_depart', 'sort_order': 'asc',
    });
    return _items(response.data);
  }

  @override
  Future<List<Map<String, dynamic>>> listTickets() async {
    final response = await _apiClient.get('/billets', queryParameters: {'page': 1, 'page_size': 100});
    return _items(response.data);
  }

  @override
  Future<List<Map<String, dynamic>>> listAvailablePlaces(int departId) async {
    // Load the complete vehicle layout so unavailable seats remain visible.
    final response = await _apiClient.get('/departs/$departId/places', queryParameters: {'available_only': false});
    return _items(response.data);
  }

  @override
  Future<void> createAndConfirm(int departId, List<Map<String, dynamic>> places) async {
    final response = await _apiClient.post('/reservations', data: {'id_depart': departId, 'places': places});
    final reservation = Map<String, dynamic>.from(response.data as Map);
    await _apiClient.post('/reservations/${reservation['id']}/confirm');
  }
}
