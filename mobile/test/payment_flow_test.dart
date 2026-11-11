import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cooperative_mobile/core/theme/app_theme.dart';
import 'package:cooperative_mobile/data/models/travel/travel_models.dart';
import 'package:cooperative_mobile/data/repositories/travel/travel_repository_impl.dart';
import 'package:cooperative_mobile/domain/repositories/travel/travel_repository.dart';
import 'package:cooperative_mobile/presentation/pages/passenger/payment_page.dart';

class PaymentRepository implements TravelRepository {
  final completion = Completer<OnlinePayment>();
  int calls = 0;
  @override
  Future<OnlinePayment> createOnlinePayment(
      int reservationId, double amount, String provider, String paymentPhone) {
    calls++;
    return completion.future;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

Reservation reservation({bool canCancel = false}) => Reservation.fromJson({
      'id': 1,
      'numero_reservation': 'RES-TEST',
      'statut': 'PAYEE',
      'montant_total': '40000',
      'montant_paye': '10000',
      'montant_restant': '30000',
      'minimum_a_payer': '30000',
      'peut_payer': true,
      'peut_annuler': canCancel,
      'depart': {'statut': 'PROGRAMME'},
      'places': [],
      'telephone_reservataire': '0340011122',
    });

void main() {
  test('server cancellation policy takes precedence over local status', () {
    expect(reservation().canBeCancelled, isFalse);
    expect(reservation(canCancel: true).canBeCancelled, isTrue);
    expect(reservation().minimumPayment, 30000);
    expect(reservation().canPay, isTrue);
  });

  testWidgets('an uncertain payment cannot be submitted twice while processing',
      (tester) async {
    final repository = PaymentRepository();
    await tester.pumpWidget(ProviderScope(
        overrides: [travelRepositoryProvider.overrideWithValue(repository)],
        child: MaterialApp(
            theme: AppTheme.darkTheme,
            home: PaymentPage(reservation: reservation()))));
    await tester.tap(find.text('Continuer le paiement'));
    await tester.pump();
    expect(repository.calls, 1);
    expect(find.text('Préparation…'), findsOneWidget);
    await tester.tap(find.text('Préparation…'));
    expect(repository.calls, 1);
    repository.completion.complete(const OnlinePayment(
        message: 'Demande à vérifier auprès du prestataire.',
        needsVerification: true));
    await tester.pumpAndSettle();
    expect(
        find.text('Demande à vérifier auprès du prestataire.'), findsOneWidget);
    expect(find.text('Vérifier le statut du paiement'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
