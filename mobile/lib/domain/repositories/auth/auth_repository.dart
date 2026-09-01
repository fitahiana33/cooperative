import '../../../data/models/auth/login_request_dto.dart';
import '../../../data/models/auth/register_request_dto.dart';
import '../../entities/user/user_entity.dart';

abstract class AuthRepository {
  Future<UserEntity> login(LoginRequestDto request);

  Future<UserEntity> register(RegisterRequestDto request);

  Future<String> forgotPassword(String email);

  Future<String> resetPassword({
    required String token,
    required String newPassword,
  });

  Future<UserEntity?> getCachedUser();

  Future<UserEntity?> fetchCurrentUser();

  Future<void> logout();
}
