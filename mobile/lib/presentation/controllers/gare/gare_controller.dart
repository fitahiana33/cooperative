import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../../data/datasources/gare/gare_remote_datasource.dart';
import '../../../data/repositories/gare/gare_repository_impl.dart';
import '../../../domain/entities/gare/gare_entity.dart';
import '../../../domain/services/gare/gare_service.dart';

final gareServiceProvider = Provider<GareService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final datasource = GareRemoteDataSourceImpl(apiClient);
  final repository = GareRepositoryImpl(datasource);
  return GareService(repository);
});

class GareState {
  final bool isLoading;
  final List<GareEntity> gares;
  final String? error;

  const GareState({
    this.isLoading = false,
    this.gares = const [],
    this.error,
  });

  GareState copyWith({
    bool? isLoading,
    List<GareEntity>? gares,
    String? error,
  }) {
    return GareState(
      isLoading: isLoading ?? this.isLoading,
      gares: gares ?? this.gares,
      error: error,
    );
  }
}

class GareController extends StateNotifier<GareState> {
  final GareService _service;

  GareController(this._service) : super(const GareState()) {
    loadGares();
  }

  Future<void> loadGares() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final list = await _service.getGares();
      state = state.copyWith(isLoading: false, gares: list);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<bool> createGare({
    required String nom,
    required String ville,
    required String adresse,
    String? telephone,
    String? email,
    double? latitude,
    double? longitude,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      await _service.createGare(
        nom: nom,
        ville: ville,
        adresse: adresse,
        telephone: telephone,
        email: email,
        latitude: latitude,
        longitude: longitude,
      );
      await loadGares();
      return true;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      return false;
    }
  }

  Future<bool> toggleGareStatus(int id) async {
    try {
      await _service.toggleGareStatus(id);
      await loadGares();
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }
}

final gareControllerProvider = StateNotifierProvider<GareController, GareState>((ref) {
  final service = ref.watch(gareServiceProvider);
  return GareController(service);
});
