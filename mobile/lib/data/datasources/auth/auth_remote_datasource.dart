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

  Exception _handleDioError(DioException e) {
    if (e.response?.statusCode == 429) {
      return Exception('Trop de tentatives. Veuillez patienter une minute avant de réessayer.');
    }
    if (e.response != null && e.response?.data != null) {
      final data = e.response?.data;
      if (data is Map<String, dynamic>) {
        if (data.containsKey('detail')) {
          final detail = data['detail'];
          if (detail is String) return Exception(detail);
        }
        if (data.containsKey('error')) {
          return Exception('Trop de tentatives. Veuillez patienter une minute avant de réessayer.');
        }
      }
    }
    if (e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.receiveTimeout) {
      return Exception('Délai d\'attente de connexion dépassé. Vérifiez votre réseau.');
    }
    if (e.type == DioExceptionType.connectionError) {
      return Exception('Impossible de se connecter au serveur backend. Vérifiez que le serveur est démarré sur 127.0.0.1:8000.');
    }
    return Exception('Une erreur est survenue lors de la communication avec le serveur.');
  }
}
