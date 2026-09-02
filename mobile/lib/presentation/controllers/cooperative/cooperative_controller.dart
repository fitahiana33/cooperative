import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../../data/datasources/cooperative/cooperative_remote_datasource.dart';
import '../../../data/repositories/cooperative/cooperative_repository_impl.dart';
import '../../../domain/entities/cooperative/cooperative_entity.dart';
import '../../../domain/services/cooperative/cooperative_service.dart';
import '../../../core/errors/user_error.dart';

final cooperativeServiceProvider = Provider<CooperativeService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final datasource = CooperativeRemoteDataSourceImpl(apiClient);
  final repository = CooperativeRepositoryImpl(datasource);
  return CooperativeService(repository);
});

class CooperativeState {
  final bool isLoading;
  final List<CooperativeEntity> cooperatives;
  final String? error;

  const CooperativeState({
    this.isLoading = false,
    this.cooperatives = const [],
    this.error,
  });

  CooperativeState copyWith({
    bool? isLoading,
    List<CooperativeEntity>? cooperatives,
    String? error,
  }) {
    return CooperativeState(
      isLoading: isLoading ?? this.isLoading,
      cooperatives: cooperatives ?? this.cooperatives,
      error: error,
    );
  }
}

class CooperativeController extends StateNotifier<CooperativeState> {
  final CooperativeService _service;

  CooperativeController(this._service) : super(const CooperativeState()) {
    loadCooperatives();
  }

  Future<void> loadCooperatives() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final list = await _service.getCooperatives();
      state = state.copyWith(isLoading: false, cooperatives: list);
    } catch (error) {
      state = state.copyWith(isLoading: false, error: userError(error, 'Impossible de charger les coopératives.', 'COOPERATIVES_LOAD_ERROR'));
    }
  }

  Future<bool> createCooperative({
    required String nom,
    String? sigle,
    String? numeroAgrement,
    String? adresse,
    String? ville,
    String? telephone,
    String? email,
    String? logoUrl,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      await _service.createCooperative(
        nom: nom,
        sigle: sigle,
        numeroAgrement: numeroAgrement,
        adresse: adresse,
        ville: ville,
        telephone: telephone,
        email: email,
        logoUrl: logoUrl,
      );
      await loadCooperatives();
      return true;
    } catch (error) {
      state = state.copyWith(isLoading: false, error: userError(error, 'Impossible d’enregistrer la coopérative.', 'COOPERATIVE_CREATE_ERROR'));
      return false;
    }
  }

  Future<bool> toggleCooperativeStatus(int id) async {
    try {
      await _service.toggleCooperativeStatus(id);
      await loadCooperatives();
      return true;
    } catch (error) {
      state = state.copyWith(error: userError(error, 'Impossible de modifier le statut de la coopérative.', 'COOPERATIVE_TOGGLE_ERROR'));
      return false;
    }
  }
}

final cooperativeControllerProvider = StateNotifierProvider<CooperativeController, CooperativeState>((ref) {
  final service = ref.watch(cooperativeServiceProvider);
  return CooperativeController(service);
});
