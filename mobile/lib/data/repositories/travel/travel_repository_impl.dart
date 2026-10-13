import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/formatters.dart';
import '../../../domain/repositories/travel/travel_repository.dart';
import '../../../presentation/controllers/auth/auth_controller.dart';
import '../../models/travel/travel_models.dart';

final travelRepositoryProvider = Provider<TravelRepository>((ref) => TravelRepositoryImpl(ref.watch(authApiClientProvider)));

class TravelRepositoryImpl implements TravelRepository {
  final ApiClient _api;

  TravelRepositoryImpl(this._api);

  @override
  Future<List<Destination>> listDestinations() async {
    final response = await _api.get('/destinations', queryParameters: {'page': 1, 'page_size': 100});
    // Cities no longer served are not offered to passengers.
    return PageResult.fromJson(response.data, Destination.fromJson).items.where((city) => city.isActive).toList()
      ..sort((a, b) => a.name.compareTo(b.name));
  }

  @override
  Future<PageResult<Departure>> searchDepartures({int? originId, int? destinationId, required DateTime date, int page = 1}) async {
    final day = Fmt.apiDate(date);
    final response = await _api.get('/departs', queryParameters: {
      'page': page,
      'page_size': 20,
      'date_from': day,
      'date_to': day,
      'reservable': true,
      'sort_by': 'heure_depart',
      'sort_order': 'asc',
      if (originId != null) 'id_destination_depart': originId,
      if (destinationId != null) 'id_destination_arrivee': destinationId,
    });
    return PageResult.fromJson(response.data, Departure.fromJson);
  }

  @override
  Future<List<Seat>> listSeats(int departureId) async {
    final response = await _api.get('/departs/$departureId/places', queryParameters: {'available_only': false});
    final items = response.data is List ? response.data as List : (response.data as Map)['items'] as List;
    return items.map((item) => Seat.fromJson(Map<String, dynamic>.from(item as Map))).toList()..sort((a, b) => a.number.compareTo(b.number));
  }

  @override
  Future<Reservation> createReservation(int departureId, List<Map<String, dynamic>> passengers) async {
    final response = await _api.post('/reservations', data: {'id_depart': departureId, 'places': passengers});
    return Reservation.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  @override
  Future<PageResult<Reservation>> listReservations({int page = 1}) async {
    final response = await _api.get('/reservations', queryParameters: {'page': page, 'page_size': 20, 'sort_by': 'created_at', 'sort_order': 'desc'});
    return PageResult.fromJson(response.data, Reservation.fromJson);
  }

  @override
  Future<Reservation> getReservation(int id) async {
    final response = await _api.get('/reservations/$id');
    return Reservation.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  @override
  Future<Reservation> cancelReservation(int id) async {
    final response = await _api.post('/reservations/$id/cancel');
    return Reservation.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  @override
  Future<PageResult<Ticket>> listTickets({int page = 1}) async {
    final response = await _api.get('/billets', queryParameters: {'page': page, 'page_size': 20});
    return PageResult.fromJson(response.data, Ticket.fromJson);
  }

  @override
  Future<Ticket> getTicket(int id) async {
    final response = await _api.get('/billets/$id');
    return Ticket.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  @override
  Future<PageResult<AppNotification>> listNotifications({int page = 1, bool unreadOnly = false}) async {
    final response = await _api.get('/notifications', queryParameters: {'page': page, 'page_size': 20, 'unread_only': unreadOnly});
    return PageResult.fromJson(response.data, AppNotification.fromJson);
  }

  @override
  Future<void> markNotificationRead(int id) => _api.patch('/notifications/$id/read');

  @override
  Future<void> markAllNotificationsRead() => _api.patch('/notifications/read-all');

  @override
  Future<PageResult<Departure>> listMyDriverDepartures({int page = 1}) async {
    final response = await _api.get('/departs/mes-departs', queryParameters: {'page': page, 'page_size': 30, 'date_from': Fmt.apiDate(DateTime.now())});
    return PageResult.fromJson(response.data, Departure.fromJson);
  }

  @override
  Future<void> driverCheckIn(int departureId, String type) => _api.post('/departs/$departureId/pointage', data: {'type': type});

  @override
  Future<List<ManifestRow>> listPassengers(int departureId) async {
    final response = await _api.get('/departs/$departureId/passagers');
    return (response.data as List).map((item) => ManifestRow.fromJson(Map<String, dynamic>.from(item as Map))).toList()
      ..sort((a, b) => a.seat.compareTo(b.seat));
  }
}
