import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:cooperative_mobile/core/theme/app_theme.dart';
import 'package:cooperative_mobile/data/models/travel/travel_models.dart';
import 'package:cooperative_mobile/data/repositories/travel/travel_repository_impl.dart';
import 'package:cooperative_mobile/domain/repositories/travel/travel_repository.dart';
import 'package:cooperative_mobile/domain/services/auth/auth_service.dart';
import 'package:cooperative_mobile/presentation/controllers/auth/auth_controller.dart';
import 'package:cooperative_mobile/presentation/pages/passenger/departure_page.dart';
import 'package:cooperative_mobile/presentation/pages/passenger/reservation_detail_page.dart';

class UnusedAuthService implements AuthService {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class LocalAuthController extends AuthController {
  LocalAuthController() : super(UnusedAuthService());
  @override
  Future<void> checkAuthStatus() async {}
}

class SectionRepository implements TravelRepository {
  @override
  Future<BookingPolicy> bookingPolicy() async =>
      const BookingPolicy(maxSeats: 6, onlinePaymentEnabled: true);
  @override
  Future<List<Seat>> listSeats(int departureId) async =>
      const [Seat(id: 1, number: 1, status: 'DISPONIBLE')];
  @override
  Future<Reservation> getReservation(int id) async => Reservation.fromJson({
        'id': id,
        'numero_reservation': 'RES-TABS',
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
        'places': List.generate(
            6,
            (i) => {
                  'id_depart_place': i + 1,
                  'nom_passager': 'Passager ${i + 1}',
                  'depart_place': {'numero_place': i + 1}
                }),
      });
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  setUpAll(() => initializeDateFormatting('fr_FR'));
  testWidgets(
      'booking advances one stage at a time and retains passenger input',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(ProviderScope(
        overrides: [
          travelRepositoryProvider.overrideWithValue(SectionRepository()),
          authControllerProvider.overrideWith((ref) => LocalAuthController()),
        ],
        child: MaterialApp(
            theme: AppTheme.darkTheme,
            home: DeparturePage(
                departure: Departure.fromJson({
              'id': 1,
              'date_depart': '2026-12-01',
              'heure_depart': '08:00:00',
              'statut': 'PROGRAMME',
              'nombre_places': 1,
              'places_disponibles': 1,
              'tarif': {'prix': 40000},
              'itineraire': {
                'destination_depart': {'nom': 'Antananarivo'},
                'destination_arrivee': {'nom': 'Antsirabe'}
              },
            })))));
    await tester.pumpAndSettle();
    expect(find.byType(TextFormField), findsNothing);
    await tester.tap(find.text('1'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Continuer'));
    await tester.pumpAndSettle();
    expect(find.text('Vos passagers'), findsOneWidget);
    await tester.tap(find.text('Continuer'));
    await tester.pumpAndSettle();
    expect(find.text('Nom obligatoire.'), findsOneWidget);
    await tester.enterText(find.byType(TextFormField).first, 'Voyageur Test');
    await tester.tap(find.text('Continuer'));
    await tester.pumpAndSettle();
    expect(find.text('Vérifiez votre réservation'), findsOneWidget);
    await tester.tap(find.text('Retour'));
    await tester.pumpAndSettle();
    expect(find.text('Voyageur Test'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
      'reservation tabs keep payment reachable while switching sections',
      (tester) async {
    await tester.pumpWidget(ProviderScope(
        overrides: [
          travelRepositoryProvider.overrideWithValue(SectionRepository())
        ],
        child: MaterialApp(
            theme: AppTheme.darkTheme,
            home: const ReservationDetailPage(reservationId: 1))));
    await tester.pumpAndSettle();
    expect(find.text('Trajet'), findsOneWidget);
    await tester.tap(find.text('Passagers (6)'));
    await tester.pumpAndSettle();
    expect(find.text('Passager 1').hitTestable(), findsOneWidget);
    expect(find.text('Payer par Mobile Money').hitTestable(), findsOneWidget);
    await tester.tap(find.text('Règlement'));
    await tester.pumpAndSettle();
    expect(find.text('Reste à régler').hitTestable(), findsOneWidget);
    expect(find.text('Annuler la réservation').hitTestable(), findsOneWidget);
    expect(find.text('Payer par Mobile Money').hitTestable(), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
