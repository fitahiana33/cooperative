import '../../repositories/driver_pointage/driver_pointage_repository.dart';

class DriverPointageService {
  final DriverPointageRepository _repository;

  DriverPointageService(this._repository);

  Future<List<Map<String, dynamic>>> listMyDepartures() => _repository.listMyDepartures();
  Future<void> pointage(int departId, String type) => _repository.pointage(departId, type);
}
