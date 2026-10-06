abstract class ReservationRepository {
  Future<List<Map<String, dynamic>>> listDepartures();
  Future<List<Map<String, dynamic>>> listTickets();
  Future<List<Map<String, dynamic>>> listAvailablePlaces(int departId);
  Future<void> createAndConfirm(int departId, List<Map<String, dynamic>> places);
}
