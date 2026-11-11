import 'package:cooperative_mobile/data/models/travel/travel_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('booking deposit reads the configured fractional percentage', () {
    final policy = BookingPolicy.fromJson({
      'max_seats': 6,
      'deposit_rate': 0.375,
      'minimum_deposit_amount': 300,
      'online_payment_enabled': true
    });
    expect(policy.depositRate, 0.375);
    expect(policy.minimumDepositAmount, 300);
  });
  test('an advance leaves a balance and boarding disables cancellation', () {
    final reservation = Reservation.fromJson({
      'id': 1,
      'statut': 'PAYEE',
      'montant_total': '40000',
      'montant_paye': '10000',
      'places': [
        {
          'nom_passager': 'A',
          'billet': {'statut': 'UTILISE'},
          'depart_place': {'numero_place': 1}
        },
      ],
      'depart': {'statut': 'EMBARQUEMENT'},
    });
    expect(reservation.paidAmount, 10000);
    expect(reservation.remainingAmount, 30000);
    expect(reservation.canBeCancelled, isFalse);
  });
  test('departure parsing is tolerant of missing optional fields', () {
    final departure = Departure.fromJson({
      'id': 7,
      'date_depart': '2026-10-09',
      'heure_depart': '07:00:00',
      'nombre_places': 22,
      'places_disponibles': '5',
      'statut': 'PROGRAMME',
      'tarif': {'prix': '35000.00', 'devise': 'MGA'},
    });
    expect(departure.origin, '?');
    expect(departure.freeSeats, 5);
    expect(departure.price, 35000);
    expect(departure.seatsPerRow, 4);
    expect(departure.isBookable, isTrue);
  });

  test('a full or departed trip is not bookable', () {
    Departure make(String status, int free) => Departure.fromJson(
        {'id': 1, 'statut': status, 'places_disponibles': free});
    expect(make('PROGRAMME', 0).isBookable, isFalse);
    expect(make('PARTI', 3).isBookable, isFalse);
    expect(make('RETARDE', 3).isBookable, isTrue);
  });

  test('a paid reservation can be cancelled until the bus leaves', () {
    Reservation make(String status, String departureStatus) =>
        Reservation.fromJson({
          'id': 1,
          'statut': status,
          'montant_total': '70000',
          'places': [
            {
              'nom_passager': 'B',
              'depart_place': {'numero_place': 4}
            },
            {
              'nom_passager': 'A',
              'depart_place': {'numero_place': 2}
            },
          ],
          'depart': {'statut': departureStatus},
        });
    expect(make('PAYEE', 'PROGRAMME').canBeCancelled, isTrue);
    expect(make('PAYEE', 'PARTI').canBeCancelled, isFalse);
    expect(make('ANNULEE', 'PROGRAMME').canBeCancelled, isFalse);
    expect(make('EN_ATTENTE', 'PROGRAMME').passengers.map((p) => p.seatNumber),
        [2, 4]);
  });
}
