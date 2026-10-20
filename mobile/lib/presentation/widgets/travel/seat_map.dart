import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../data/models/travel/travel_models.dart';

/// Seat map following the vehicle model's layout: seats beside the driver,
/// then rows of [seatsPerRow] with an aisle in the middle.
class SeatMap extends StatelessWidget {
  final List<Seat> seats;
  final Set<int> selected;
  final int seatsBesideDriver;
  final int seatsPerRow;
  final bool enabled;
  final ValueChanged<Seat> onToggle;

  const SeatMap({
    super.key,
    required this.seats,
    required this.selected,
    required this.seatsBesideDriver,
    required this.seatsPerRow,
    required this.onToggle,
    this.enabled = true,
  });

  static const free = Color(0xFF10B981);
  static const reserved = Color(0xFFF59E0B);
  static const occupied = Color(0xFFEF4444);
  static const blocked = Color(0xFF64748B);

  static const _labels = {'DISPONIBLE': 'disponible', 'RESERVEE': 'réservée', 'OCCUPEE': 'occupée', 'BLOQUEE': 'bloquée'};

  Color _color(Seat seat) {
    if (selected.contains(seat.id)) return AppTheme.primary;
    switch (seat.status) {
      case 'RESERVEE':
        return reserved;
      case 'OCCUPEE':
        return occupied;
      case 'BLOQUEE':
        return blocked;
      default:
        return free;
    }
  }

  Widget _seat(Seat seat) {
    final isSelected = selected.contains(seat.id);
    final selectable = seat.isFree || isSelected;
    final state = isSelected ? 'sélectionnée' : _labels[seat.status] ?? seat.status;
    return Semantics(
      button: selectable,
      selected: isSelected,
      enabled: enabled && selectable,
      label: 'Place ${seat.number}, $state',
      excludeSemantics: true,
      child: GestureDetector(
        onTap: enabled && selectable ? () => onToggle(seat) : null,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          width: 44,
          height: 44,
          margin: const EdgeInsets.all(3),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: _color(seat),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Colors.white.withValues(alpha: isSelected ? 0.9 : 0.3), width: isSelected ? 2 : 1),
          ),
          child: Text('${seat.number}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        ),
      ),
    );
  }

  Widget _row(List<Seat> row) {
    final aisle = (seatsPerRow / 2).ceil();
    final children = <Widget>[];
    for (var index = 0; index < row.length; index++) {
      if (index == aisle) children.add(const SizedBox(width: 18));
      children.add(_seat(row[index]));
    }
    return Row(mainAxisAlignment: MainAxisAlignment.center, children: children);
  }

  @override
  Widget build(BuildContext context) {
    final front = seats.take(seatsBesideDriver).toList();
    final back = seats.skip(seatsBesideDriver).toList();
    final rows = <List<Seat>>[];
    for (var index = 0; index < back.length; index += seatsPerRow) {
      rows.add(back.sublist(index, (index + seatsPerRow).clamp(0, back.length)));
    }
    return Column(children: [
      Wrap(alignment: WrapAlignment.center, spacing: 12, runSpacing: 6, children: [
        _legend(free, 'Disponible'),
        _legend(AppTheme.primary, 'Sélectionnée'),
        _legend(reserved, 'Réservée'),
        _legend(occupied, 'Occupée'),
        _legend(blocked, 'Bloquée'),
      ]),
      const SizedBox(height: 12),
      Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
        decoration: BoxDecoration(color: const Color(0xFF172554), borderRadius: BorderRadius.circular(18), border: Border.all(color: Colors.white12)),
        child: FittedBox(
          fit: BoxFit.scaleDown,
          child: Column(children: [
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              _driverSeat(),
              const SizedBox(width: 18),
              ...front.map(_seat),
            ]),
            const SizedBox(width: 200, child: Divider(color: Colors.white24, height: 20)),
            ...rows.map(_row),
          ]),
        ),
      ),
    ]);
  }

  Widget _legend(Color color, String label) => Row(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 12, height: 12, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3))),
        const SizedBox(width: 5),
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
      ]);

  Widget _driverSeat() => Semantics(
        label: 'Chauffeur',
        excludeSemantics: true,
        child: Container(
          width: 48,
          height: 48,
          margin: const EdgeInsets.all(3),
          alignment: Alignment.center,
          decoration: BoxDecoration(color: const Color(0xFF475569), borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.white24)),
          child: const Icon(Icons.airline_seat_recline_normal, size: 22, color: Colors.white70),
        ),
      );
}
