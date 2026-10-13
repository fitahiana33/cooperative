import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/travel/travel_models.dart';
import '../../../data/repositories/travel/travel_repository_impl.dart';
import '../../widgets/common/async_view.dart';
import '../../widgets/travel/status_chip.dart';
import 'reservation_detail_page.dart';

/// History of the passenger's reservations, newest first.
class ReservationsPage extends ConsumerStatefulWidget {
  const ReservationsPage({super.key});

  @override
  ConsumerState<ReservationsPage> createState() => _ReservationsPageState();
}

class _ReservationsPageState extends ConsumerState<ReservationsPage> {
  final List<Reservation> _items = [];
  int _page = 1;
  bool _hasMore = false;
  bool _loading = true;
  bool _loadingMore = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool more = false}) async {
    setState(() { if (more) { _loadingMore = true; } else { _loading = _items.isEmpty; } _error = null; });
    try {
      final result = await ref.read(travelRepositoryProvider).listReservations(page: more ? _page + 1 : 1);
      if (!mounted) return;
      setState(() {
        if (!more) _items.clear();
        _items.addAll(result.items);
        _page = result.page;
        _hasMore = result.hasMore;
      });
    } catch (error) {
      if (mounted) setState(() => _error = userError(error, 'Impossible de charger vos réservations.', 'MOBILE_RESERVATIONS_ERROR'));
    } finally {
      if (mounted) setState(() { _loading = false; _loadingMore = false; });
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Mes réservations')),
        body: RefreshIndicator(
          onRefresh: _load,
          child: AsyncView(
            loading: _loading,
            error: _items.isEmpty ? _error : null,
            empty: _items.isEmpty,
            emptyMessage: 'Vous n’avez encore aucune réservation.',
            emptyIcon: Icons.event_busy,
            onRetry: _load,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _items.length + (_hasMore ? 1 : 0),
              itemBuilder: (_, index) {
                if (index == _items.length) {
                  return TextButton(onPressed: _loadingMore ? null : () => _load(more: true), child: Text(_loadingMore ? 'Chargement…' : 'Voir plus'));
                }
                final item = _items[index];
                return Card(
                  color: AppTheme.surface,
                  margin: const EdgeInsets.only(bottom: 10),
                  child: ListTile(
                    title: Text('${item.origin} → ${item.destination}', style: const TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: Text('${Fmt.date(item.departureDate)} à ${Fmt.time(item.departureTime)}\n${item.passengers.length} place(s) · ${Fmt.money(item.amount)}'),
                    isThreeLine: true,
                    trailing: StatusChip(item.status),
                    onTap: () async {
                      await Navigator.push(context, MaterialPageRoute(builder: (_) => ReservationDetailPage(reservationId: item.id)));
                      if (mounted) _load();
                    },
                  ),
                );
              },
            ),
          ),
        ),
      );
}
