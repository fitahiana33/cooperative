import 'package:flutter/foundation.dart';

class Env {
  static const String productionApiBaseUrl =
      'https://cooperative-api-3yuz.onrender.com/api/v1';

  static String get apiBaseUrl {
    const fromEnv = String.fromEnvironment('MOBILE_API_BASE_URL');
    if (fromEnv.isNotEmpty) {
      return fromEnv;
    }

    return productionApiBaseUrl;
  }
}
