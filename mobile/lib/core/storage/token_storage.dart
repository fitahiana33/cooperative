import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class TokenStorage {
  static const String _accessTokenKey = 'auth_access_token';
  static const String _refreshTokenKey = 'auth_refresh_token';
  static const String _userKey = 'auth_user_data';

  final SharedPreferences _prefs;

  TokenStorage(this._prefs);

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _prefs.setString(_accessTokenKey, accessToken);
    await _prefs.setString(_refreshTokenKey, refreshToken);
  }

  String? getAccessToken() {
    return _prefs.getString(_accessTokenKey);
  }

  String? getRefreshToken() {
    return _prefs.getString(_refreshTokenKey);
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
    await _prefs.remove(_accessTokenKey);
    await _prefs.remove(_refreshTokenKey);
    await _prefs.remove(_userKey);
  }
}
