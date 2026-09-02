import '../../entities/vehicule/vehicule.dart';
import '../../entities/vehicule/vehicule_reference.dart';

abstract class VehiculeRepository {
  Future<List<VehiculeEntity>> fetchVehicules({int page = 1, String? search});
  Future<VehiculeEntity> getVehicule(int id);
  Future<List<MarqueOption>> fetchMarques();
  Future<List<ModeleOption>> fetchModeles();
  Future<List<CooperativeOption>> fetchCooperatives();
  Future<VehiculeEntity> createVehicule(Map<String, dynamic> data);
  Future<VehiculeEntity> updateVehicule(int id, Map<String, dynamic> data);
  Future<VehiculeEntity> toggleVehicule(int id);
  Future<void> deleteVehicule(int id);
}
