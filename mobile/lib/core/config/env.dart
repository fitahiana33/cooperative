import 'package:flutter/foundation.dart';

class Env {
  static String get apiBaseUrl {
    const fromEnv = String.fromEnvironment('MOBILE_API_BASE_URL');
    if (fromEnv.isNotEmpty) {
      return fromEnv;
    }
    if (kIsWeb) {
      return 'http://127.0.0.1:8000/api/v1';
    }
    return 'http://10.0.2.2:8000/api/v1';
  }
}
