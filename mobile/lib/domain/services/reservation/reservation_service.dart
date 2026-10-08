import '../../repositories/reservation/reservation_repository.dart';

class ReservationService {
  final ReservationRepository _repository;

  ReservationService(this._repository);

  Future<List<Map<String, dynamic>>> listDepartures() => _repository.listDepartures();
  Future<List<Map<String, dynamic>>> listTickets() => _repository.listTickets();
  Future<List<Map<String, dynamic>>> listAvailablePlaces(int departId) => _repository.listAvailablePlaces(departId);
  Future<Map<String, dynamic>> createReservation(int departId, List<Map<String, dynamic>> places) => _repository.createReservation(departId, places);
}
