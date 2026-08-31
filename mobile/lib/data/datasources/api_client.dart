import 'package:dio/dio.dart';
import '../../core/config/env.dart';

class ApiClient {
  ApiClient() : dio = Dio(BaseOptions(baseUrl: Env.apiBaseUrl, connectTimeout: const Duration(seconds: 10)));
  final Dio dio;
}

