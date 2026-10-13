import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/travel/travel_models.dart';
import '../../../data/repositories/travel/travel_repository_impl.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/travel/status_chip.dart';
import 'departure_page.dart';

/// Search a trip by origin, destination and date; only bookable departures are listed.
class TripSearchPage extends ConsumerStatefulWidget {
  const TripSearchPage({super.key});

  @override
  ConsumerState<TripSearchPage> createState() => _TripSearchPageState();
}

class _TripSearchPageState extends ConsumerState<TripSearchPage> {
  List<Destination> _destinations = [];
  int? _originId;
  int? _destinationId;
  DateTime _date = DateTime.now();
  final List<Departure> _results = [];
  int _page = 1;
  bool _hasMore = false;
  bool _searched = false;
  bool _loading = false;
  bool _loadingDestinations = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDestinations();
  }

  Future<void> _loadDestinations() async {
    setState(() { _loadingDestinations = true; _error = null; });
    try {
      final values = await ref.read(travelRepositoryProvider).listDestinations();
      if (mounted) setState(() => _destinations = values);
    } catch (error) {
      if (mounted) setState(() => _error = userError(error, 'Impossible de charger les villes.', 'MOBILE_DESTINATIONS_ERROR'));
    } finally {
      if (mounted) setState(() => _loadingDestinations = false);
    }
  }

  Future<void> _search({bool more = false}) async {
    if (_loading) return;
    setState(() { _loading = true; _error = null; if (!more) { _page = 1; _results.clear(); } });
    try {
      final result = await ref.read(travelRepositoryProvider).searchDepartures(
            originId: _originId,
            destinationId: _destinationId,
            date: _date,
            page: more ? _page + 1 : 1,
          );
      if (!mounted) return;
      setState(() {
        _results.addAll(result.items);
        _page = result.page;
        _hasMore = result.hasMore;
        _searched = true;
      });
    } catch (error) {
      if (mounted) setState(() => _error = userError(error, 'La recherche a échoué.', 'MOBILE_SEARCH_ERROR'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _pickDate() async {
    final today = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(today.year, today.month, today.day),
      lastDate: today.add(const Duration(days: 90)),
      locale: const Locale('fr', 'FR'),
    );
    if (picked != null) setState(() => _date = picked);
  }

  void _swap() => setState(() {
        final origin = _originId;
        _originId = _destinationId;
        _destinationId = origin;
      });

  Widget _cityField(String label, int? value, ValueChanged<int?> onChanged) => DropdownButtonFormField<int?>(
        initialValue: value,
        isExpanded: true,
        decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
        items: [
          const DropdownMenuItem<int?>(value: null, child: Text('Toutes les villes')),
          ..._destinations.map((city) => DropdownMenuItem<int?>(value: city.id, child: Text(city.name))),
        ],
        onChanged: onChanged,
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Rechercher un voyage')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          if (_loadingDestinations) const LinearProgressIndicator(),
          Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
            Expanded(child: Column(children: [
              _cityField('Départ', _originId, (value) => setState(() => _originId = value)),
              const SizedBox(height: 12),
              _cityField('Arrivée', _destinationId, (value) => setState(() => _destinationId = value)),
            ])),
            IconButton(tooltip: 'Inverser départ et arrivée', onPressed: _swap, icon: const Icon(Icons.swap_vert)),
          ]),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _pickDate,
            icon: const Icon(Icons.calendar_today),
            label: Text('Date : ${Fmt.date(Fmt.apiDate(_date))}'),
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: _loading ? null : () => _search(),
            icon: const Icon(Icons.search),
            label: Text(_loading && _results.isEmpty ? 'Recherche…' : 'Rechercher'),
          ),
          const SizedBox(height: 16),
          if (_error != null) ...[ErrorBanner(message: _error!), const SizedBox(height: 12)],
          if (_searched && _results.isEmpty && !_loading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Text('Aucun départ réservable pour ces critères. Essayez une autre date.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white70)),
            ),
          ..._results.map(_departureCard),
          if (_hasMore)
            TextButton(onPressed: _loading ? null : () => _search(more: true), child: Text(_loading ? 'Chargement…' : 'Voir plus de départs')),
        ]),
      );

  Widget _departureCard(Departure departure) => Card(
        color: AppTheme.surface,
        margin: const EdgeInsets.only(bottom: 12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () async {
            await Navigator.push(context, MaterialPageRoute(builder: (_) => DeparturePage(departure: departure)));
            if (mounted) _search();
          },
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Text(Fmt.time(departure.time), style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                const SizedBox(width: 12),
                Expanded(child: Text('${departure.origin} → ${departure.destination}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600))),
                StatusChip(departure.status),
              ]),
              const SizedBox(height: 8),
              Text('${departure.cooperative} · ${departure.vehiclePlate}', style: const TextStyle(color: Colors.white70)),
              const SizedBox(height: 6),
              Row(children: [
                const Icon(Icons.event_seat, size: 16, color: Colors.white54),
                const SizedBox(width: 4),
                Text('${departure.freeSeats} / ${departure.seats} places libres', style: const TextStyle(color: Colors.white70)),
                const Spacer(),
                Text(Fmt.money(departure.price, departure.currency), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.primaryAccent)),
              ]),
            ]),
          ),
        ),
      );
}
