import '../../../core/storage/token_storage.dart';
import '../../../domain/entities/user/user_entity.dart';
import '../../../domain/repositories/auth/auth_repository.dart';
import '../../datasources/auth/auth_remote_datasource.dart';
import '../../models/auth/login_request_dto.dart';
import '../../models/auth/register_request_dto.dart';
import '../../models/user/user_dto.dart';

class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource _remoteDataSource;
  final TokenStorage _tokenStorage;

  AuthRepositoryImpl({
    required AuthRemoteDataSource remoteDataSource,
    required TokenStorage tokenStorage,
  })  : _remoteDataSource = remoteDataSource,
        _tokenStorage = tokenStorage;

  @override
  Future<UserEntity> login(LoginRequestDto request) async {
    final response = await _remoteDataSource.login(request);

    await _tokenStorage.saveTokens(
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
    );

    if (response.user != null) {
      await _tokenStorage.saveUser((response.user as UserDto).toJson());
      return response.user!;
    }

    final user = await _remoteDataSource.getCurrentUser();
    await _tokenStorage.saveUser(user.toJson());
    return user;
  }

  @override
  Future<UserEntity> register(RegisterRequestDto request) async {
    final response = await _remoteDataSource.register(request);

    await _tokenStorage.saveTokens(
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
    );

    if (response.user != null) {
      await _tokenStorage.saveUser((response.user as UserDto).toJson());
      return response.user!;
    }

    final user = await _remoteDataSource.getCurrentUser();
    await _tokenStorage.saveUser(user.toJson());
    return user;
  }

  @override
  Future<String> forgotPassword(String email) async {
    return await _remoteDataSource.forgotPassword(email);
  }

  @override
  Future<String> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    return await _remoteDataSource.resetPassword(
      token: token,
      newPassword: newPassword,
    );
  }

  @override
  Future<UserEntity?> getCachedUser() async {
    final userMap = _tokenStorage.getUser();
    if (userMap != null) {
      return UserDto.fromJson(userMap);
    }
    return null;
  }

  @override
  Future<UserEntity?> fetchCurrentUser() async {
    final token = _tokenStorage.getAccessToken();
    if (token == null || token.isEmpty) return null;

    try {
      final user = await _remoteDataSource.getCurrentUser();
      await _tokenStorage.saveUser(user.toJson());
      return user;
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> logout() async {
    await _tokenStorage.clear();
  }
}
