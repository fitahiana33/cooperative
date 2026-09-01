import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/token_storage.dart';
import '../../../data/datasources/auth/auth_remote_datasource.dart';
import '../../../data/models/auth/login_request_dto.dart';
import '../../../data/models/auth/register_request_dto.dart';
import '../../../data/repositories/auth/auth_repository_impl.dart';
import '../../../domain/repositories/auth/auth_repository.dart';
import '../../../domain/services/auth/auth_service.dart';
import 'auth_state.dart';

final Provider<SharedPreferences> sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('SharedPreferences non initialisé.');
});

final Provider<TokenStorage> tokenStorageProvider = Provider<TokenStorage>((ref) {
  final prefs = ref.watch(sharedPreferencesProvider);
  return TokenStorage(prefs);
});

final Provider<ApiClient> apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(tokenStorageProvider);
  return ApiClient(
    tokenStorage: storage,
    onUnauthenticated: () {
      ref.read(authControllerProvider.notifier).handleUnauthenticated();
    },
  );
});

final Provider<AuthRemoteDataSource> authRemoteDataSourceProvider = Provider<AuthRemoteDataSource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthRemoteDataSource(apiClient);
});

final Provider<AuthRepository> authRepositoryProvider = Provider<AuthRepository>((ref) {
  final remote = ref.watch(authRemoteDataSourceProvider);
  final storage = ref.watch(tokenStorageProvider);
  return AuthRepositoryImpl(
    remoteDataSource: remote,
    tokenStorage: storage,
  );
});

final Provider<AuthService> authServiceProvider = Provider<AuthService>((ref) {
  final repo = ref.watch(authRepositoryProvider);
  return AuthService(repo);
});

class AuthController extends StateNotifier<AuthState> {
  final AuthService _authService;

  AuthController(this._authService) : super(const AuthState()) {
    checkAuthStatus();
  }

  Future<void> checkAuthStatus() async {
    state = state.copyWith(status: AuthStatus.loading, clearError: true);
    try {
      final cachedUser = await _authService.getCachedUser();
      if (cachedUser != null) {
        state = state.copyWith(
          status: AuthStatus.authenticated,
          user: cachedUser,
        );
        final freshUser = await _authService.getCurrentUser();
        if (freshUser != null) {
          state = state.copyWith(user: freshUser);
        }
      } else {
        final freshUser = await _authService.getCurrentUser();
        if (freshUser != null) {
          state = state.copyWith(
            status: AuthStatus.authenticated,
            user: freshUser,
          );
        } else {
          state = state.copyWith(status: AuthStatus.unauthenticated);
        }
      }
    } catch (_) {
      state = state.copyWith(status: AuthStatus.unauthenticated);
    }
  }

  Future<bool> login({
    required String email,
    required String password,
  }) async {
    state = state.copyWith(
      status: AuthStatus.loading,
      clearError: true,
      clearInfo: true,
    );
    try {
      final request = LoginRequestDto(email: email, password: password);
      final user = await _authService.login(request);
      state = state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.unauthenticated,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
      return false;
    }
  }

  Future<bool> register({
    required String name,
    required String firstName,
    required String email,
    String? telephone,
    String? address,
    required String password,
  }) async {
    state = state.copyWith(
      status: AuthStatus.loading,
      clearError: true,
      clearInfo: true,
    );
    try {
      final request = RegisterRequestDto(
        name: name,
        firstName: firstName,
        email: email,
        telephone: telephone,
        address: address,
        password: password,
      );
      final user = await _authService.register(request);
      state = state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
        infoMessage: 'Inscription réussie! Vous êtes connecté.',
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.unauthenticated,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
      return false;
    }
  }

  Future<bool> forgotPassword(String email) async {
    state = state.copyWith(clearError: true, clearInfo: true);
    try {
      final message = await _authService.forgotPassword(email);
      state = state.copyWith(infoMessage: message);
      return true;
    } catch (e) {
      state = state.copyWith(
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
      return false;
    }
  }

  Future<bool> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    state = state.copyWith(clearError: true, clearInfo: true);
    try {
      final message = await _authService.resetPassword(
        token: token,
        newPassword: newPassword,
      );
      state = state.copyWith(infoMessage: message);
      return true;
    } catch (e) {
      state = state.copyWith(
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
      return false;
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  void handleUnauthenticated() {
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  void clearMessages() {
    state = state.copyWith(clearError: true, clearInfo: true);
  }
}

final StateNotifierProvider<AuthController, AuthState> authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  final service = ref.watch(authServiceProvider);
  return AuthController(service);
});
