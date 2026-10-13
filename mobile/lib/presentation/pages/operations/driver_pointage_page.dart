import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/travel/travel_models.dart';
import '../../../data/repositories/travel/travel_repository_impl.dart';
import '../../widgets/common/async_view.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/travel/status_chip.dart';

/// The driver's upcoming trips: check-in at departure and arrival, passenger list.
class DriverPointagePage extends ConsumerStatefulWidget {
  const DriverPointagePage({super.key});

  @override
  ConsumerState<DriverPointagePage> createState() => _DriverPointagePageState();
}

class _DriverPointagePageState extends ConsumerState<DriverPointagePage> {
  List<Departure> _departures = [];
  bool _loading = true;
  int? _busyId;
  String? _error;
  String? _actionError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = _departures.isEmpty; _error = null; });
    try {
      final result = await ref.read(travelRepositoryProvider).listMyDriverDepartures();
      if (mounted) setState(() => _departures = result.items);
    } catch (error) {
      if (mounted) setState(() => _error = userError(error, 'Impossible de charger vos départs.', 'DRIVER_DEPARTS_ERROR'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _checkIn(Departure departure, String type) async {
    final leaving = type == 'DEPART';
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(leaving ? 'Confirmer le départ ?' : 'Confirmer l’arrivée ?'),
        content: Text('${departure.origin} → ${departure.destination}, ${Fmt.date(departure.date)} à ${Fmt.time(departure.time)}.\n'
            '${leaving ? 'Le départ passera au statut « Parti » et l’embarquement sera fermé.' : 'Le trajet sera marqué comme terminé.'}'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Annuler')),
          ElevatedButton(onPressed: () => Navigator.pop(dialogContext, true), child: Text(leaving ? 'Pointer le départ' : 'Pointer l’arrivée')),
        ],
      ),
    );
    if (confirmed != true) return;
    setState(() { _busyId = departure.id; _actionError = null; });
    try {
      await ref.read(travelRepositoryProvider).driverCheckIn(departure.id, type);
      await _load();
    } catch (error) {
      if (mounted) setState(() => _actionError = userError(error, 'Pointage impossible.', 'DRIVER_POINTAGE_ERROR'));
    } finally {
      if (mounted) setState(() => _busyId = null);
    }
  }

  Future<void> _showPassengers(Departure departure) async {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      builder: (_) => _PassengerSheet(departure: departure),
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Mes départs')),
        body: RefreshIndicator(
          onRefresh: _load,
          child: AsyncView(
            loading: _loading,
            error: _departures.isEmpty ? _error : null,
            empty: _departures.isEmpty,
            emptyMessage: 'Aucun départ à venir ne vous est affecté.',
            emptyIcon: Icons.directions_bus_outlined,
            onRetry: _load,
            child: ListView(padding: const EdgeInsets.all(16), children: [
              if (_actionError != null) ...[ErrorBanner(message: _actionError!), const SizedBox(height: 12)],
              ..._departures.map(_card),
            ]),
          ),
        ),
      );

  Widget _card(Departure departure) {
    final canLeave = const {'PROGRAMME', 'EMBARQUEMENT', 'RETARDE'}.contains(departure.status);
    final canArrive = departure.status == 'PARTI';
    final busy = _busyId == departure.id;
    return Card(
      color: AppTheme.surface,
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Text('${departure.origin} → ${departure.destination}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17))),
            StatusChip(departure.status),
          ]),
          const SizedBox(height: 6),
          Text('${Fmt.date(departure.date)} à ${Fmt.time(departure.time)}'),
          Text('Véhicule ${departure.vehiclePlate} · ${departure.seats - departure.freeSeats} / ${departure.seats} places réservées', style: const TextStyle(color: Colors.white70)),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: ElevatedButton(onPressed: canLeave && !busy ? () => _checkIn(departure, 'DEPART') : null, child: const Text('Pointer le départ'))),
            const SizedBox(width: 8),
            Expanded(child: OutlinedButton(onPressed: canArrive && !busy ? () => _checkIn(departure, 'ARRIVEE') : null, child: const Text('Pointer l’arrivée'))),
          ]),
          TextButton.icon(onPressed: () => _showPassengers(departure), icon: const Icon(Icons.people_outline), label: const Text('Voir les passagers')),
        ]),
      ),
    );
  }
}

class _PassengerSheet extends ConsumerStatefulWidget {
  final Departure departure;

  const _PassengerSheet({required this.departure});

  @override
  ConsumerState<_PassengerSheet> createState() => _PassengerSheetState();
}

class _PassengerSheetState extends ConsumerState<_PassengerSheet> {
  List<ManifestRow>? _rows;
  String? _error;

  @override
  void initState() {
    super.initState();
    ref.read(travelRepositoryProvider).listPassengers(widget.departure.id).then((rows) {
      if (mounted) setState(() => _rows = rows);
    }).catchError((Object error) {
      if (mounted) setState(() => _error = userError(error, 'Impossible de charger les passagers.', 'DRIVER_PASSENGERS_ERROR'));
    });
  }

  @override
  Widget build(BuildContext context) {
    final rows = _rows;
    final boarded = rows?.where((row) => row.boarded).length ?? 0;
    return SafeArea(
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.7,
        child: Column(children: [
          ListTile(
            title: Text('Passagers · ${widget.departure.origin} → ${widget.departure.destination}', style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: rows == null ? null : Text('$boarded / ${rows.length} embarqués'),
          ),
          Expanded(
            child: _error != null
                ? Center(child: Text(_error!))
                : rows == null
                    ? const Center(child: CircularProgressIndicator())
                    : rows.isEmpty
                        ? const Center(child: Text('Aucun passager réservé.'))
                        : ListView(children: rows.map((row) => ListTile(
                              leading: CircleAvatar(child: Text('${row.seat}')),
                              title: Text(row.passenger),
                              subtitle: Text(row.phone.isEmpty ? '—' : row.phone),
                              trailing: Icon(row.boarded ? Icons.check_circle : Icons.radio_button_unchecked, color: row.boarded ? const Color(0xFF10B981) : Colors.white38),
                            )).toList()),
          ),
        ]),
      ),
    );
  }
}
