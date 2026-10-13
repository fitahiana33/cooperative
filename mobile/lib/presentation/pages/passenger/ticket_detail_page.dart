import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/travel/travel_models.dart';
import '../../../data/repositories/travel/travel_repository_impl.dart';
import '../../widgets/common/async_view.dart';
import '../../widgets/travel/status_chip.dart';

/// E-ticket shown at boarding: QR code (the ticket's unique code) and trip details.
class TicketDetailPage extends ConsumerStatefulWidget {
  final int ticketId;

  const TicketDetailPage({super.key, required this.ticketId});

  @override
  ConsumerState<TicketDetailPage> createState() => _TicketDetailPageState();
}

class _TicketDetailPageState extends ConsumerState<TicketDetailPage> {
  Ticket? _ticket;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = _ticket == null; _error = null; });
    try {
      final value = await ref.read(travelRepositoryProvider).getTicket(widget.ticketId);
      if (mounted) setState(() => _ticket = value);
    } catch (error) {
      if (mounted) setState(() => _error = userError(error, 'Impossible de charger le billet.', 'MOBILE_TICKET_ERROR'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 5),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(width: 120, child: Text(label, style: const TextStyle(color: Colors.black54))),
          Expanded(child: Text(value, style: const TextStyle(color: Colors.black87, fontWeight: FontWeight.w600))),
        ]),
      );

  @override
  Widget build(BuildContext context) {
    final ticket = _ticket;
    return Scaffold(
      appBar: AppBar(title: const Text('Mon billet')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: AsyncView(
          loading: _loading,
          error: _error,
          empty: ticket == null,
          emptyMessage: 'Billet introuvable.',
          onRetry: _load,
          child: ticket == null ? const SizedBox() : ListView(padding: const EdgeInsets.all(16), children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
              child: Column(children: [
                Text('${ticket.origin} → ${ticket.destination}', style: const TextStyle(color: Colors.black87, fontSize: 20, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
                const SizedBox(height: 4),
                Text('${Fmt.date(ticket.date)} à ${Fmt.time(ticket.time)}', style: const TextStyle(color: Colors.black54)),
                const SizedBox(height: 16),
                Semantics(
                  label: 'QR code du billet ${ticket.number}',
                  child: Opacity(
                    // A used or cancelled ticket stays visible but faded.
                    opacity: ticket.isValid ? 1 : 0.35,
                    child: QrImageView(data: ticket.qrValue, size: 220, backgroundColor: Colors.white),
                  ),
                ),
                const SizedBox(height: 8),
                StatusChip(ticket.status),
                const SizedBox(height: 4),
                Text(
                  ticket.isValid ? 'Présentez ce QR code à l’agent lors de l’embarquement.' : 'Ce billet n’est plus utilisable pour embarquer.',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.black54, fontSize: 12),
                ),
                const Divider(height: 28),
                _row('Passager', ticket.passenger),
                _row('Place', '${ticket.seat}'),
                _row('Billet', ticket.number),
                _row('Réservation', ticket.reservationNumber),
                _row('Coopérative', ticket.cooperative.isEmpty ? '—' : ticket.cooperative),
                _row('Véhicule', ticket.vehiclePlate.isEmpty ? '—' : ticket.vehiclePlate),
                _row('Montant', Fmt.money(ticket.price, ticket.currency)),
                if (ticket.usedAt != null) _row('Embarqué le', Fmt.dateTime(ticket.usedAt)),
              ]),
            ),
          ]),
        ),
      ),
    );
  }
}
