import '../user/user_entity.dart';

class AuthSession {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final UserEntity? user;

  const AuthSession({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    this.user,
  });
}
