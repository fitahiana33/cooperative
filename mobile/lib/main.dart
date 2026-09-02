import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';
import 'core/storage/token_storage.dart' as storage;
import 'presentation/controllers/auth/auth_controller.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();

  runApp(
    ProviderScope(
      overrides: [
        authSharedPreferencesProvider.overrideWithValue(prefs),
        storage.tokenStorageProvider.overrideWithValue(storage.TokenStorage(prefs)),
      ],
      child: const CooperativeApp(),
    ),
  );
}
