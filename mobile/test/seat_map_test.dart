import 'package:cooperative_mobile/data/models/travel/travel_models.dart';
import 'package:cooperative_mobile/presentation/widgets/travel/seat_map.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final seats = [
    const Seat(id: 1, number: 1, status: 'DISPONIBLE'),
    const Seat(id: 2, number: 2, status: 'OCCUPEE'),
    const Seat(id: 3, number: 3, status: 'RESERVEE'),
    const Seat(id: 4, number: 4, status: 'BLOQUEE'),
    const Seat(id: 5, number: 5, status: 'DISPONIBLE'),
  ];

  Future<List<int>> pump(WidgetTester tester, {Set<int> selected = const {}}) async {
    final toggled = <int>[];
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: SeatMap(seats: seats, selected: selected, seatsBesideDriver: 1, seatsPerRow: 4, onToggle: (seat) => toggled.add(seat.number)),
        ),
      ),
    ));
    return toggled;
  }

  testWidgets('legend shows all seat states', (tester) async {
    await pump(tester);
    for (final label in ['Disponible', 'Sélectionnée', 'Réservée', 'Occupée', 'Bloquée']) {
      expect(find.text(label), findsOneWidget);
    }
  });

  testWidgets('only free seats can be selected', (tester) async {
    final toggled = await pump(tester);
    await tester.tap(find.text('1'));
    await tester.tap(find.text('2'));
    await tester.tap(find.text('3'));
    await tester.tap(find.text('5'));
    expect(toggled, [1, 5]);
  });

  testWidgets('each seat announces its state to screen readers', (tester) async {
    final handle = tester.ensureSemantics();
    await pump(tester, selected: {5});
    expect(find.bySemanticsLabel('Place 2, occupée'), findsOneWidget);
    expect(find.bySemanticsLabel('Place 5, sélectionnée'), findsOneWidget);
    handle.dispose();
  });
}
