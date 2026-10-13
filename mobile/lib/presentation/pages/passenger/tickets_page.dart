import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/travel/travel_models.dart';
import '../../../data/repositories/travel/travel_repository_impl.dart';
import '../../widgets/common/async_view.dart';
import '../../widgets/travel/status_chip.dart';
import 'ticket_detail_page.dart';

class TicketsPage extends ConsumerStatefulWidget {
  const TicketsPage({super.key});

  @override
  ConsumerState<TicketsPage> createState() => _TicketsPageState();
}

class _TicketsPageState extends ConsumerState<TicketsPage> {
  final List<Ticket> _items = [];
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
      final result = await ref.read(travelRepositoryProvider).listTickets(page: more ? _page + 1 : 1);
      if (!mounted) return;
      setState(() {
        if (!more) _items.clear();
        _items.addAll(result.items);
        _page = result.page;
        _hasMore = result.hasMore;
      });
    } catch (error) {
      if (mounted) setState(() => _error = userError(error, 'Impossible de charger vos billets.', 'MOBILE_TICKETS_ERROR'));
    } finally {
      if (mounted) setState(() { _loading = false; _loadingMore = false; });
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Mes billets')),
        body: RefreshIndicator(
          onRefresh: _load,
          child: AsyncView(
            loading: _loading,
            error: _items.isEmpty ? _error : null,
            empty: _items.isEmpty,
            emptyMessage: 'Aucun billet pour le moment.\nLes billets sont émis au paiement de la réservation.',
            emptyIcon: Icons.confirmation_number_outlined,
            onRetry: _load,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _items.length + (_hasMore ? 1 : 0),
              itemBuilder: (_, index) {
                if (index == _items.length) {
                  return TextButton(onPressed: _loadingMore ? null : () => _load(more: true), child: Text(_loadingMore ? 'Chargement…' : 'Voir plus'));
                }
                final ticket = _items[index];
                return Card(
                  color: AppTheme.surface,
                  margin: const EdgeInsets.only(bottom: 10),
                  child: ListTile(
                    leading: Icon(Icons.qr_code_2, color: ticket.isValid ? AppTheme.primaryAccent : Colors.white38, size: 32),
                    title: Text('${ticket.origin} → ${ticket.destination}', style: const TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: Text('${Fmt.date(ticket.date)} à ${Fmt.time(ticket.time)} · place ${ticket.seat}\n${ticket.passenger}'),
                    isThreeLine: true,
                    trailing: StatusChip(ticket.status),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => TicketDetailPage(ticketId: ticket.id))),
                  ),
                );
              },
            ),
          ),
        ),
      );
}
