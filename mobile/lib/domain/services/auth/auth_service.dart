import '../../../data/models/auth/login_request_dto.dart';
import '../../../data/models/auth/register_request_dto.dart';
import '../../entities/user/user_entity.dart';
import '../../repositories/auth/auth_repository.dart';

class AuthService {
  final AuthRepository _repository;

  AuthService(this._repository);

  Future<UserEntity> login(LoginRequestDto request) async {
    return await _repository.login(request);
  }

  Future<UserEntity> register(RegisterRequestDto request) async {
    return await _repository.register(request);
  }

  Future<String> forgotPassword(String email) async {
    return await _repository.forgotPassword(email);
  }

  Future<String> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    return await _repository.resetPassword(
      token: token,
      newPassword: newPassword,
    );
  }

  Future<UserEntity?> getCachedUser() async {
    return await _repository.getCachedUser();
  }

  Future<UserEntity?> getCurrentUser() async {
    return await _repository.fetchCurrentUser();
  }

  Future<void> logout() async {
    await _repository.logout();
  }
}
