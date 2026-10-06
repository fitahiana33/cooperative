import 'package:flutter/foundation.dart';

class Env {
  static const String productionApiBaseUrl =
      'https://cooperative-api-3yuz.onrender.com/api/v1';

  static String get apiBaseUrl {
    const fromEnv = String.fromEnvironment('MOBILE_API_BASE_URL');
    if (fromEnv.isNotEmpty) {
      return fromEnv;
    }

    if (kReleaseMode) return productionApiBaseUrl;
    if (kIsWeb) return 'http://127.0.0.1:8000/api/v1';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    return 'http://127.0.0.1:8000/api/v1';
  }
}
