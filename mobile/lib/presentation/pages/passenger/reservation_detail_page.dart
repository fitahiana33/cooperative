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
import 'ticket_detail_page.dart';
import 'payment_page.dart';
import 'reservation_edit_page.dart';

class ReservationDetailPage extends ConsumerStatefulWidget {
  final int reservationId;

  const ReservationDetailPage({super.key, required this.reservationId});

  @override
  ConsumerState<ReservationDetailPage> createState() =>
      _ReservationDetailPageState();
}

class _ReservationDetailPageState extends ConsumerState<ReservationDetailPage> {
  Reservation? _reservation;
  bool _loading = true;
  bool _cancelling = false;
  String? _error;
  String? _actionError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = _reservation == null;
      _error = null;
    });
    try {
      final value = await ref
          .read(travelRepositoryProvider)
          .getReservation(widget.reservationId);
      if (mounted) setState(() => _reservation = value);
    } catch (error) {
      if (mounted) {
        setState(() => _error = userError(
            error,
            'Impossible de charger la réservation.',
            'MOBILE_RESERVATION_ERROR'));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _cancel() async {
    final reservation = _reservation!;
    final paid = reservation.status == 'PAYEE';
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Annuler la réservation ?'),
        content: Text(paid
            ? 'Les places seront libérées. Le montant déjà versé (${Fmt.money(reservation.paidAmount)}) sera traité au guichet selon les règles de la gare.'
            : 'Les places seront libérées pour d’autres voyageurs.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Garder')),
          ElevatedButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Annuler la réservation')),
        ],
      ),
    );
    if (confirmed != true) return;
    setState(() {
      _cancelling = true;
      _actionError = null;
    });
    try {
      final updated = await ref
          .read(travelRepositoryProvider)
          .cancelReservation(reservation.id);
      if (!mounted) return;
      setState(() => _reservation = updated);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(paid
            ? 'Réservation annulée. Présentez-vous au guichet pour le remboursement.'
            : 'Réservation annulée.'),
      ));
    } catch (error) {
      // The server explains why (e.g. less than 2 h before departure).
      if (mounted) {
        setState(() => _actionError =
            userError(error, 'L’annulation a échoué.', 'MOBILE_CANCEL_ERROR'));
      }
    } finally {
      if (mounted) setState(() => _cancelling = false);
    }
  }

  Future<void> _pay() async {
    final updated = await Navigator.push<Reservation>(
        context,
        MaterialPageRoute(
            builder: (_) => PaymentPage(reservation: _reservation!)));
    if (!mounted) return;
    if (updated != null) setState(() => _reservation = updated);
    await _load();
  }

  Future<void> _edit() async {
    final updated = await Navigator.push<Reservation>(
        context,
        MaterialPageRoute(
            builder: (_) => ReservationEditPage(reservation: _reservation!)));
    if (mounted && updated != null) setState(() => _reservation = updated);
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(
              width: 120,
              child:
                  Text(label, style: const TextStyle(color: Colors.white60))),
          Expanded(
              child: Text(value,
                  style: const TextStyle(fontWeight: FontWeight.w600))),
        ]),
      );

  Widget _section(String name, List<Widget> children) => RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          key: PageStorageKey('reservation-${widget.reservationId}-$name'),
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: children,
        ),
      );

  Widget _card(List<Widget> children) => Card(
        color: AppTheme.surface,
        child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(children: children)),
      );

  @override
  Widget build(BuildContext context) {
    final reservation = _reservation;
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(title: const Text('Ma réservation')),
        bottomNavigationBar: reservation?.canPay == true
            ? SafeArea(
                child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
                    child: FilledButton.icon(
                        onPressed: _cancelling ? null : _pay,
                        icon: const Icon(Icons.payments_outlined),
                        label: const Text('Payer par Mobile Money'))))
            : null,
        body: AsyncView(
          loading: _loading,
          error: _error,
          empty: reservation == null,
          emptyMessage: 'Réservation introuvable.',
          onRetry: _load,
          child: reservation == null
              ? const SizedBox()
              : Column(children: [
                  Padding(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                      child: Row(children: [
                        Expanded(
                            child: Text(reservation.number,
                                style: const TextStyle(
                                    fontWeight: FontWeight.bold))),
                        StatusChip(reservation.status),
                      ])),
                  if (_actionError != null)
                    Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: ErrorBanner(message: _actionError!)),
                  TabBar(
                      isScrollable: true,
                      tabAlignment: TabAlignment.start,
                      tabs: [
                        const Tab(text: 'Voyage'),
                        Tab(
                            text:
                                'Passagers (${reservation.passengers.length})'),
                        const Tab(text: 'Règlement'),
                      ]),
                  Expanded(
                      child: TabBarView(children: [
                    _section('trip', [
                      _card([
                        _row('Trajet',
                            '${reservation.origin} → ${reservation.destination}'),
                        _row('Départ',
                            '${Fmt.date(reservation.departureDate)} à ${Fmt.time(reservation.departureTime)}'),
                        if (reservation.cooperative.isNotEmpty)
                          _row('Coopérative', reservation.cooperative),
                        _row('État du départ',
                            Fmt.status(reservation.departureStatus)),
                        _row(
                            'Réservée le', Fmt.dateTime(reservation.createdAt)),
                      ])
                    ]),
                    _section('passengers', [
                      if (reservation.passengers.isEmpty)
                        const Text('Aucun passager renseigné.'),
                      ...reservation.passengers.map((passenger) => Card(
                            color: AppTheme.surface,
                            child: ListTile(
                              leading: CircleAvatar(
                                  child: Text('${passenger.seatNumber}')),
                              title: Text(passenger.name),
                              subtitle: Text(passenger.ticketNumber == null
                                  ? 'Billet émis au paiement'
                                  : 'Billet ${Fmt.status(passenger.ticketStatus)}'),
                              trailing: passenger.ticketId == null
                                  ? null
                                  : const Icon(Icons.qr_code_2),
                              onTap: passenger.ticketId == null
                                  ? null
                                  : () => Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                          builder: (_) => TicketDetailPage(
                                              ticketId: passenger.ticketId!))),
                            ),
                          )),
                      if (reservation.isPending)
                        OutlinedButton.icon(
                            onPressed: _cancelling ? null : _edit,
                            icon: const Icon(Icons.edit_outlined),
                            label: const Text('Modifier les places')),
                    ]),
                    _section('payment', [
                      _card([
                        _row('Montant', Fmt.money(reservation.amount)),
                        _row('Déjà réglé', Fmt.money(reservation.paidAmount)),
                        _row('Reste à régler',
                            Fmt.money(reservation.remainingAmount)),
                        if (reservation.refundPendingAmount > 0)
                          _row('À rembourser',
                              Fmt.money(reservation.refundPendingAmount)),
                      ]),
                      if (reservation.isPending)
                        Padding(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            child: Text(
                              'À régler avant ${Fmt.dateTime(reservation.expiresAt)}. Les places seront libérées après ce délai.',
                              style: const TextStyle(color: Color(0xFFFDE68A)),
                            )),
                      if (reservation.canBeCancelled)
                        OutlinedButton.icon(
                          onPressed: _cancelling ? null : _cancel,
                          icon: const Icon(Icons.cancel_outlined,
                              color: Color(0xFFF87171)),
                          label: Text(_cancelling
                              ? 'Annulation…'
                              : 'Annuler la réservation'),
                        ),
                    ]),
                  ])),
                ]),
        ),
      ),
    );
  }
}
