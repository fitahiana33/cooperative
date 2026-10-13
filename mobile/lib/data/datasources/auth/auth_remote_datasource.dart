import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../models/auth/login_request_dto.dart';
import '../../models/auth/register_request_dto.dart';
import '../../models/auth/token_response_dto.dart';
import '../../models/user/user_dto.dart';

class AuthRemoteDataSource {
  final ApiClient _apiClient;

  AuthRemoteDataSource(this._apiClient);

  Future<TokenResponseDto> login(LoginRequestDto request) async {
    try {
      final response = await _apiClient.dio.post(
        '/auth/login',
        data: request.toJson(),
      );
      return TokenResponseDto.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<TokenResponseDto> register(RegisterRequestDto request) async {
    try {
      final response = await _apiClient.dio.post(
        '/auth/register',
        data: request.toJson(),
      );
      return TokenResponseDto.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<TokenResponseDto> refreshToken(String refreshToken) async {
    try {
      final response = await _apiClient.dio.post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      return TokenResponseDto.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<String> forgotPassword(String email) async {
    try {
      final response = await _apiClient.dio.post(
        '/auth/forgot-password',
        data: {'email': email.trim()},
      );
      final data = response.data as Map<String, dynamic>;
      return data['message'] as String? ?? 'Email de réinitialisation envoyé.';
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<String> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    try {
      final response = await _apiClient.dio.post(
        '/auth/reset-password',
        data: {
          'token': token.trim(),
          'new_password': newPassword,
        },
      );
      final data = response.data as Map<String, dynamic>;
      return data['message'] as String? ?? 'Mot de passe réinitialisé.';
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<UserDto> getCurrentUser() async {
    try {
      final response = await _apiClient.dio.get('/auth/me');
      return UserDto.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<void> logout(String refreshToken) async {
    try {
      await _apiClient.dio.post(
        '/auth/logout',
        data: {'refresh_token': refreshToken},
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// The DioException is passed through so the UI can show the server's own
  /// explanation (see core/errors/user_error.dart).
  Exception _handleDioError(DioException e) => e;

  Future<UserDto> updateProfile(Map<String, dynamic> fields) async {
    try {
      final response = await _apiClient.put('/users/me', data: fields);
      return UserDto.fromJson(Map<String, dynamic>.from(response.data as Map));
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<void> changePassword({required String currentPassword, required String newPassword}) async {
    try {
      await _apiClient.post('/users/me/password', data: {'current_password': currentPassword, 'new_password': newPassword});
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }
}
