import '../../../domain/entities/auth/auth_session.dart';
import '../user/user_dto.dart';

class TokenResponseDto extends AuthSession {
  const TokenResponseDto({
    required super.accessToken,
    required super.refreshToken,
    required super.tokenType,
    super.user,
  });

  factory TokenResponseDto.fromJson(Map<String, dynamic> json) {
    return TokenResponseDto(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: json['token_type'] as String? ?? 'bearer',
      user: json['user'] != null ? UserDto.fromJson(json['user'] as Map<String, dynamic>) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'token_type': tokenType,
      if (user != null) 'user': (user as UserDto).toJson(),
    };
  }
}
