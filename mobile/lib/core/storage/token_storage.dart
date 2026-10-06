import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

final tokenStorageProvider = Provider<TokenStorage>((ref) {
  throw UnimplementedError('tokenStorageProvider must be overridden in ProviderScope');
});

class TokenStorage {
  static const String _accessTokenKey = 'auth_access_token';
  static const String _refreshTokenKey = 'auth_refresh_token';
  static const String _userKey = 'auth_user_data';

  final SharedPreferences _prefs;
  final FlutterSecureStorage _secureStorage;

  TokenStorage(this._prefs, {FlutterSecureStorage? secureStorage})
      : _secureStorage = secureStorage ?? const FlutterSecureStorage();

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _secureStorage.write(key: _accessTokenKey, value: accessToken);
    await _secureStorage.write(key: _refreshTokenKey, value: refreshToken);
  }

  Future<String?> getAccessToken() {
    return _secureStorage.read(key: _accessTokenKey);
  }

  Future<String?> getRefreshToken() {
    return _secureStorage.read(key: _refreshTokenKey);
  }

  Future<void> saveUser(Map<String, dynamic> userMap) async {
    await _prefs.setString(_userKey, jsonEncode(userMap));
  }

  Map<String, dynamic>? getUser() {
    final rawJson = _prefs.getString(_userKey);
    if (rawJson == null || rawJson.isEmpty) return null;
    try {
      return jsonDecode(rawJson) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  Future<void> clear() async {
    await _secureStorage.delete(key: _accessTokenKey);
    await _secureStorage.delete(key: _refreshTokenKey);
    await _prefs.remove(_userKey);
  }
}
