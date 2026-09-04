import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/env.dart';
import '../storage/token_storage.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(tokenStorageProvider);
  return ApiClient(tokenStorage: storage);
});

class ApiClient {
  late final Dio dio;
  final TokenStorage tokenStorage;
  final void Function()? onUnauthenticated;
  Future<bool>? _refreshInProgress;

  ApiClient({
    required this.tokenStorage,
    this.onUnauthenticated,
    String? baseUrl,
  }) {
    dio = Dio(
      BaseOptions(
        baseUrl: baseUrl ?? Env.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 10),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final token = tokenStorage.getAccessToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (DioException error, handler) async {
          if (error.response?.statusCode == 401 &&
              error.requestOptions.extra['authRetry'] != true &&
              !error.requestOptions.path.contains('/auth/login') &&
              !error.requestOptions.path.contains('/auth/refresh') &&
              !error.requestOptions.path.contains('/auth/register') &&
              !error.requestOptions.path.contains('/auth/logout')) {
            final refreshed = await _attemptRefreshToken();
            if (refreshed) {
              final newAccessToken = tokenStorage.getAccessToken();
              final opts = error.requestOptions;
              opts.extra['authRetry'] = true;
              opts.headers['Authorization'] = 'Bearer $newAccessToken';
              try {
                final response = await dio.fetch(opts);
                return handler.resolve(response);
              } catch (retryError) {
                return handler.next(error);
              }
            } else {
              await tokenStorage.clear();
              onUnauthenticated?.call();
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) =>
      dio.get<T>(path, queryParameters: queryParameters, options: options);

  Future<Response<T>> post<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) =>
      dio.post<T>(path, data: data, queryParameters: queryParameters, options: options);

  Future<Response<T>> put<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) =>
      dio.put<T>(path, data: data, queryParameters: queryParameters, options: options);

  Future<Response<T>> patch<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) =>
      dio.patch<T>(path, data: data, queryParameters: queryParameters, options: options);

  Future<Response<T>> delete<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) =>
      dio.delete<T>(path, data: data, queryParameters: queryParameters, options: options);

  Future<bool> _attemptRefreshToken() async {
    if (_refreshInProgress != null) return _refreshInProgress!;
    _refreshInProgress = _refreshTokenOnce();
    try {
      return await _refreshInProgress!;
    } finally {
      _refreshInProgress = null;
    }
  }

  Future<bool> _refreshTokenOnce() async {
    final refreshToken = tokenStorage.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      return false;
    }

    try {
      final refreshDio = Dio(
        BaseOptions(
          baseUrl: dio.options.baseUrl,
          headers: {'Content-Type': 'application/json'},
        ),
      );
      final response = await refreshDio.post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        final newAccess = data['access_token'] as String;
        final newRefresh = data['refresh_token'] as String;
        await tokenStorage.saveTokens(
          accessToken: newAccess,
          refreshToken: newRefresh,
        );
        if (data['user'] != null) {
          await tokenStorage.saveUser(data['user'] as Map<String, dynamic>);
        }
        return true;
      }
    } catch (error, stackTrace) {
      debugPrint('[REFRESH_TOKEN_ERROR] $error');
      debugPrintStack(stackTrace: stackTrace);
    }
    return false;
  }
}
