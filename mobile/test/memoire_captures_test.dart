import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cooperative_mobile/core/theme/app_theme.dart';
import 'package:cooperative_mobile/data/models/travel/travel_models.dart';
import 'package:cooperative_mobile/data/repositories/travel/travel_repository_impl.dart';
import 'package:cooperative_mobile/domain/repositories/travel/travel_repository.dart';
import 'package:cooperative_mobile/domain/services/auth/auth_service.dart';
import 'package:cooperative_mobile/presentation/controllers/auth/auth_controller.dart';
import 'package:cooperative_mobile/presentation/pages/auth/login_page.dart';
import 'package:cooperative_mobile/presentation/pages/passenger/departure_page.dart';
import 'package:cooperative_mobile/presentation/pages/passenger/reservation_detail_page.dart';
import 'package:intl/date_symbol_data_local.dart';

class SansServeurAuthService implements AuthService {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}
class AuthCaptureController extends AuthController {
  AuthCaptureController() : super(SansServeurAuthService());
  @override
  Future<void> checkAuthStatus() async {}
}
class CatalogueTestRepository implements TravelRepository {
  @override
  Future<BookingPolicy> bookingPolicy() async => const BookingPolicy(maxSeats: 6, onlinePaymentEnabled: true);
  @override
  Future<List<Seat>> listSeats(int departureId) async => const [
    Seat(id: 1, number: 1, status: 'DISPONIBLE'),
    Seat(id: 2, number: 2, status: 'DISPONIBLE'),
    Seat(id: 3, number: 3, status: 'RESERVEE'),
    Seat(id: 4, number: 4, status: 'DISPONIBLE'),
  ];
  @override
  Future<Reservation> getReservation(int id) async => Reservation.fromJson({
    'id': id,
    'numero_reservation': 'DEMO-ITU-001',
    'statut': 'PAYEE',
    'montant_total': 80000,
    'montant_paye': 20000,
    'montant_restant': 60000,
    'peut_payer': true,
    'peut_annuler': true,
    'depart': {
      'date_depart': '2026-12-01',
      'heure_depart': '08:00:00',
      'statut': 'PROGRAMME',
      'itineraire': {
        'destination_depart': {'nom': 'Antananarivo'},
        'destination_arrivee': {'nom': 'Antsirabe'}
      }
    },
    'places': List.generate(2, (i) => {
      'id_depart_place': i + 1,
      'nom_passager': 'Voyageur demo ${i + 1}',
      'depart_place': {'numero_place': i + 1}
    }),
  });
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}
void main() {
  setUpAll(() async {
    await initializeDateFormatting('fr_FR');
    final p = Platform.environment['ROBOTO_FONT_PATH'];
    if (p != null && p.isNotEmpty) {
      final loader = FontLoader('Roboto');
      loader.addFont(File(p).readAsBytes());
      await loader.load();
    }
  });
  setUp(() { });
  testWidgets('Capture de la page de connexion Flutter', (tester) async {
    tester.view.physicalSize = const Size(440, 960);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(ProviderScope(
      overrides: [authControllerProvider.overrideWith((ref) => AuthCaptureController())],
      child: MaterialApp(theme: AppTheme.darkTheme, home: const LoginPage()),
    ));
    await tester.pumpAndSettle();
    await expectLater(find.byType(MaterialApp), matchesGoldenFile('goldens/login_flutter.png'));
  });
  testWidgets('Capture du choix de place Flutter', (tester) async {
    tester.view.physicalSize = const Size(440, 960);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(ProviderScope(
      overrides: [
        travelRepositoryProvider.overrideWithValue(CatalogueTestRepository()),
        authControllerProvider.overrideWith((ref) => AuthCaptureController()),
      ],
      child: MaterialApp(theme: AppTheme.darkTheme, home: DeparturePage(
        departure: Departure.fromJson({
          'id': 1,
          'date_depart': '2026-12-01',
          'heure_depart': '08:00:00',
          'statut': 'PROGRAMME',
          'nombre_places': 4,
          'places_disponibles': 3,
          'tarif': {'prix': 40000},
          'itineraire': {
            'destination_depart': {'nom': 'Antananarivo'},
            'destination_arrivee': {'nom': 'Antsirabe'}
          },
        }),
      )),
    ));
    await tester.pumpAndSettle();
    await expectLater(find.byType(MaterialApp), matchesGoldenFile('goldens/selection_places_flutter.png'));
  });
  testWidgets('Capture du detail de reservation Flutter', (tester) async {
    tester.view.physicalSize = const Size(440, 960);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(ProviderScope(
      overrides: [
        travelRepositoryProvider.overrideWithValue(CatalogueTestRepository()),
      ],
      child: MaterialApp(theme: AppTheme.darkTheme, home: const ReservationDetailPage(reservationId: 1)),
    ));
    await tester.pumpAndSettle();
    await expectLater(find.byType(MaterialApp), matchesGoldenFile('goldens/reservation_flutter.png'));
  });
}
