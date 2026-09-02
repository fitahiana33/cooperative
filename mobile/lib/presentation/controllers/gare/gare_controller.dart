import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../../data/datasources/gare/gare_remote_datasource.dart';
import '../../../data/repositories/gare/gare_repository_impl.dart';
import '../../../domain/entities/gare/gare_entity.dart';
import '../../../domain/services/gare/gare_service.dart';
import '../../../core/errors/user_error.dart';

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
    } catch (error) {
      state = state.copyWith(isLoading: false, error: userError(error, 'Impossible de charger les gares.', 'GARES_LOAD_ERROR'));
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
    } catch (error) {
      state = state.copyWith(isLoading: false, error: userError(error, 'Impossible d’enregistrer la gare.', 'GARE_CREATE_ERROR'));
      return false;
    }
  }

  Future<bool> toggleGareStatus(int id) async {
    try {
      await _service.toggleGareStatus(id);
      await loadGares();
      return true;
    } catch (error) {
      state = state.copyWith(error: userError(error, 'Impossible de modifier le statut de la gare.', 'GARE_TOGGLE_ERROR'));
      return false;
    }
  }
}

final gareControllerProvider = StateNotifierProvider<GareController, GareState>((ref) {
  final service = ref.watch(gareServiceProvider);
  return GareController(service);
});
