import '../../../data/models/travel/travel_models.dart';

/// Everything the passenger and driver screens read or change through the API.
abstract class TravelRepository {
  Future<List<Destination>> listDestinations();

  Future<PageResult<Departure>> searchDepartures({int? originId, int? destinationId, required DateTime date, int page = 1});

  Future<List<Seat>> listSeats(int departureId);

  /// Books seats; the reservation stays pending until it is paid at the station.
  Future<Reservation> createReservation(int departureId, List<Map<String, dynamic>> passengers);

  Future<PageResult<Reservation>> listReservations({int page = 1});

  Future<Reservation> getReservation(int id);

  Future<Reservation> cancelReservation(int id);

  Future<PageResult<Ticket>> listTickets({int page = 1});

  Future<Ticket> getTicket(int id);

  Future<PageResult<AppNotification>> listNotifications({int page = 1, bool unreadOnly = false});

  Future<void> markNotificationRead(int id);

  Future<void> markAllNotificationsRead();

  Future<PageResult<Departure>> listMyDriverDepartures({int page = 1});

  Future<void> driverCheckIn(int departureId, String type);

  Future<List<ManifestRow>> listPassengers(int departureId);
}
