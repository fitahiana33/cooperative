abstract class ReservationRepository {
  Future<List<Map<String, dynamic>>> listDepartures();
  Future<List<Map<String, dynamic>>> listTickets();
  Future<List<Map<String, dynamic>>> listAvailablePlaces(int departId);
  /// Creates a pending reservation. It is confirmed when it is paid.
  Future<Map<String, dynamic>> createReservation(int departId, List<Map<String, dynamic>> places);
}
