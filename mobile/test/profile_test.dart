import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cooperative_mobile/core/theme/app_theme.dart';
import 'package:cooperative_mobile/data/models/user/user_dto.dart';
import 'package:cooperative_mobile/domain/entities/user/user_entity.dart';
import 'package:cooperative_mobile/domain/services/auth/auth_service.dart';
import 'package:cooperative_mobile/presentation/controllers/auth/auth_controller.dart';
import 'package:cooperative_mobile/presentation/controllers/auth/auth_state.dart';
import 'package:cooperative_mobile/presentation/pages/passenger/profile_page.dart';

const account = UserDto(
    id: 7,
    name: 'Rabe',
    firstName: 'Miora',
    email: 'miora@example.com',
    role: 'agent_gare',
    isActive: true,
    createdAt: '2026-01-01');

class ProfileService implements AuthService {
  Map<String, dynamic>? saved;
  bool passwordChanged = false;
  bool photoRemoved = false;
  @override
  Future<UserEntity> updateProfile(Map<String, dynamic> fields) async {
    saved = fields;
    return UserDto.fromJson({...account.toJson(), ...fields});
  }

  @override
  Future<void> changePassword(
      {required String currentPassword, required String newPassword}) async {
    passwordChanged = true;
  }

  @override
  Future<UserEntity> removePhoto() async {
    photoRemoved = true;
    return account;
  }

  @override
  Future<Uint8List> profilePhoto() async => base64Decode(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII=');
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class ProfileController extends AuthController {
  ProfileController(super.service, {UserEntity user = account}) {
    state = AuthState(status: AuthStatus.authenticated, user: user);
  }
  @override
  Future<void> checkAuthStatus() async {}
}

Widget application(ProfileService service, {UserEntity user = account}) =>
    ProviderScope(
        overrides: [
          authServiceProvider.overrideWithValue(service),
          authControllerProvider
              .overrideWith((ref) => ProfileController(service, user: user)),
        ],
        child:
            MaterialApp(theme: AppTheme.darkTheme, home: const ProfilePage()));

void main() {
  test(
      'photo version survives account caching and older responses remain compatible',
      () {
    final withPhoto =
        UserDto.fromJson({...account.toJson(), 'photo_version': 'a' * 32});
    expect(
        UserDto.fromJson(jsonDecode(jsonEncode(withPhoto.toJson()))
                as Map<String, dynamic>)
            .photoVersion,
        'a' * 32);
    final legacy = account.toJson()..remove('photo_version');
    expect(UserDto.fromJson(legacy).photoVersion, isNull);
  });

  testWidgets('profile tabs retain edits and saving updates the account',
      (tester) async {
    final service = ProfileService();
    await tester.pumpWidget(application(service));
    await tester.pumpAndSettle();
    final firstName = find.byType(TextFormField).first;
    await tester.ensureVisible(firstName);
    await tester.enterText(firstName, 'Hanitra');
    await tester.tap(find.text('Sécurité'));
    await tester.pumpAndSettle();
    expect(find.text('Changer mon mot de passe'), findsOneWidget);
    await tester.tap(find.text('Informations'));
    await tester.pumpAndSettle();
    expect(find.text('Hanitra'), findsOneWidget);
    await tester.ensureVisible(find.text('Enregistrer les modifications'));
    await tester.tap(find.text('Enregistrer les modifications'));
    await tester.pumpAndSettle();
    expect(service.saved?['first_name'], 'Hanitra');
    expect(service.saved?['telephone'], isNull);
    expect(find.text('Profil enregistré.'), findsOneWidget);
  });

  testWidgets(
      'password confirmation blocks a mismatch before changing the password',
      (tester) async {
    final service = ProfileService();
    await tester.pumpWidget(application(service));
    await tester.tap(find.text('Sécurité'));
    await tester.pumpAndSettle();
    final fields = find.byType(TextFormField);
    await tester.enterText(fields.at(0), 'Actuel123');
    await tester.enterText(fields.at(1), 'Nouveau123');
    await tester.enterText(fields.at(2), 'Different123');
    await tester.ensureVisible(find.text('Modifier le mot de passe'));
    await tester.tap(find.text('Modifier le mot de passe'));
    await tester.pumpAndSettle();
    expect(find.text('Les mots de passe doivent être identiques.'),
        findsOneWidget);
    expect(service.passwordChanged, isFalse);
  });

  testWidgets('removing a photo updates the account and returns to initials',
      (tester) async {
    final service = ProfileService();
    final user =
        UserDto.fromJson({...account.toJson(), 'photo_version': 'a' * 32});
    await tester.pumpWidget(application(service, user: user));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Supprimer la photo'));
    await tester.pumpAndSettle();
    expect(service.photoRemoved, isTrue);
    expect(find.text('Supprimer la photo'), findsNothing);
    expect(find.text('Ajouter une photo'), findsOneWidget);
    expect(find.text('MR'), findsOneWidget);
  });
}
