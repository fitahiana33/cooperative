abstract class DriverPointageRepository {
  Future<List<Map<String, dynamic>>> listMyDepartures();
  Future<void> pointage(int departId, String type);
}
