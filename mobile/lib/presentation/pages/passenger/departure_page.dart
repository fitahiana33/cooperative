import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/travel/travel_models.dart';
import '../../../data/repositories/travel/travel_repository_impl.dart';
import '../../controllers/auth/auth_controller.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/travel/seat_map.dart';
import 'reservation_detail_page.dart';

/// Departure details, seat choice, one form per passenger, summary, booking.
class DeparturePage extends ConsumerStatefulWidget {
  final Departure departure;

  const DeparturePage({super.key, required this.departure});

  @override
  ConsumerState<DeparturePage> createState() => _DeparturePageState();
}

class _PassengerForm {
  final TextEditingController name;
  final TextEditingController phone;

  _PassengerForm({String name = '', String phone = ''})
      : name = TextEditingController(text: name),
        phone = TextEditingController(text: phone);

  void dispose() {
    name.dispose();
    phone.dispose();
  }
}

class _DeparturePageState extends ConsumerState<DeparturePage> {
  static const _maxSeats = 6;
  final _formKey = GlobalKey<FormState>();
  List<Seat> _seats = [];
  final List<Seat> _selected = [];
  final Map<int, _PassengerForm> _forms = {};
  bool _loading = true;
  bool _booking = false;
  String? _error;
  int _loadVersion = 0;

  Departure get _departure => widget.departure;

  @override
  void initState() {
    super.initState();
    _loadSeats();
  }

  @override
  void dispose() {
    for (final form in _forms.values) {
      form.dispose();
    }
    super.dispose();
  }

  Future<void> _loadSeats() async {
    // Only the latest request may update the map (a slow earlier answer is ignored).
    final version = ++_loadVersion;
    setState(() => _loading = true);
    try {
      final seats = await ref.read(travelRepositoryProvider).listSeats(_departure.id);
      if (!mounted || version != _loadVersion) return;
      setState(() {
        _seats = seats;
        // Drop selected seats that someone else took in the meantime.
        final free = {for (final seat in seats.where((s) => s.isFree)) seat.id};
        _selected.removeWhere((seat) => !free.contains(seat.id));
        _forms.keys.where((id) => !free.contains(id)).toList().forEach((id) => _forms.remove(id)?.dispose());
      });
    } catch (error) {
      if (mounted && version == _loadVersion) setState(() => _error = userError(error, 'Impossible de charger les places.', 'MOBILE_SEATS_ERROR'));
    } finally {
      if (mounted && version == _loadVersion) setState(() => _loading = false);
    }
  }

  void _toggle(Seat seat) {
    setState(() {
      _error = null;
      if (_selected.any((item) => item.id == seat.id)) {
        _selected.removeWhere((item) => item.id == seat.id);
        _forms.remove(seat.id)?.dispose();
        return;
      }
      if (_selected.length >= _maxSeats) {
        _error = 'Vous pouvez réserver au maximum $_maxSeats places à la fois.';
        return;
      }
      _selected.add(seat);
      final user = ref.read(authControllerProvider).user;
      // The first passenger is usually the account holder.
      _forms[seat.id] = _forms.isEmpty && user != null ? _PassengerForm(name: user.fullName, phone: user.telephone ?? '') : _PassengerForm();
    });
  }

  double get _total => _departure.price * _selected.length;

  Future<void> _book() async {
    if (_selected.isEmpty) {
      setState(() => _error = 'Choisissez au moins une place.');
      return;
    }
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() { _booking = true; _error = null; });
    try {
      final passengers = _selected.map((seat) {
        final form = _forms[seat.id]!;
        final phone = form.phone.text.trim();
        return {'id_depart_place': seat.id, 'nom_passager': form.name.text.trim(), 'telephone_passager': phone.isEmpty ? null : phone};
      }).toList();
      final reservation = await ref.read(travelRepositoryProvider).createReservation(_departure.id, passengers);
      if (!mounted) return;
      await _showPaymentInstructions(reservation);
      if (!mounted) return;
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => ReservationDetailPage(reservationId: reservation.id)));
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = userError(error, 'La réservation n’a pas pu être enregistrée.', 'MOBILE_BOOKING_ERROR'));
      // A seat taken meanwhile: show the current map so the passenger can choose again.
      if (error is DioException && error.response?.statusCode == 409) await _loadSeats();
    } finally {
      if (mounted) setState(() => _booking = false);
    }
  }

  Future<void> _showPaymentInstructions(Reservation reservation) {
    final deadline = reservation.expiresAt == null ? 'le délai indiqué' : Fmt.time(Fmt.dateTime(reservation.expiresAt).split(' ').last);
    return showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Réservation enregistrée'),
        content: Text(
          'Réservation ${reservation.number}\n'
          'Montant à payer : ${Fmt.money(reservation.amount)}\n\n'
          'Vos places sont retenues jusqu’à $deadline. Payez au guichet de la gare avant cette heure pour recevoir vos billets ; '
          'passé ce délai, les places seront libérées.',
        ),
        actions: [TextButton(onPressed: () => Navigator.of(dialogContext).pop(), child: const Text('Voir ma réservation'))],
      ),
    );
  }

  Widget _info(IconData icon, String text) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Row(children: [Icon(icon, size: 18, color: Colors.white54), const SizedBox(width: 8), Expanded(child: Text(text))]),
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text('${_departure.origin} → ${_departure.destination}')),
        body: RefreshIndicator(
          onRefresh: _loadSeats,
          child: Form(
            key: _formKey,
            child: ListView(padding: const EdgeInsets.all(16), children: [
              Card(
                color: AppTheme.surface,
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    _info(Icons.event, '${Fmt.date(_departure.date)} à ${Fmt.time(_departure.time)}'),
                    _info(Icons.groups, _departure.cooperative),
                    _info(Icons.directions_bus, 'Véhicule ${_departure.vehiclePlate} · ${_departure.seats} places'),
                    _info(Icons.payments_outlined, '${Fmt.money(_departure.price, _departure.currency)} par place'),
                    _info(Icons.info_outline, 'Statut : ${Fmt.status(_departure.status)}'),
                  ]),
                ),
              ),
              const SizedBox(height: 16),
              Row(children: [
                const Expanded(child: Text('Choisissez vos places', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold))),
                Text('${_selected.length} sélectionnée(s)', style: const TextStyle(color: AppTheme.primaryAccent)),
              ]),
              const SizedBox(height: 12),
              if (_loading && _seats.isEmpty)
                const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()))
              else
                SeatMap(
                  seats: _seats,
                  selected: {for (final seat in _selected) seat.id},
                  seatsBesideDriver: _departure.seatsBesideDriver,
                  seatsPerRow: _departure.seatsPerRow,
                  enabled: !_booking,
                  onToggle: _toggle,
                ),
              if (_selected.isNotEmpty) ...[
                const SizedBox(height: 20),
                const Text('Passagers', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                ..._selected.map(_passengerCard),
                const SizedBox(height: 8),
                Card(
                  color: const Color(0xFF172554),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text('Récapitulatif', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const SizedBox(height: 8),
                      Text('${_selected.length} place(s) × ${Fmt.money(_departure.price, _departure.currency)}'),
                      Text('Places : ${(_selected.map((s) => s.number).toList()..sort()).join(', ')}'),
                      const Divider(),
                      Row(children: [
                        const Expanded(child: Text('Total à payer', style: TextStyle(fontWeight: FontWeight.bold))),
                        Text(Fmt.money(_total, _departure.currency), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.primaryAccent)),
                      ]),
                      const SizedBox(height: 6),
                      const Text('Le paiement se fait au guichet de la gare, avant l’expiration de la réservation.', style: TextStyle(color: Colors.white70, fontSize: 12)),
                    ]),
                  ),
                ),
              ],
              if (_error != null) ...[const SizedBox(height: 12), ErrorBanner(message: _error!)],
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _booking || _selected.isEmpty ? null : _book,
                child: Text(_booking ? 'Réservation en cours…' : 'Réserver ${_selected.isEmpty ? '' : '(${Fmt.money(_total, _departure.currency)})'}'),
              ),
              const SizedBox(height: 24),
            ]),
          ),
        ),
      );

  Widget _passengerCard(Seat seat) {
    final form = _forms[seat.id]!;
    return Card(
      color: AppTheme.surface,
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          Row(children: [
            Text('Place ${seat.number}', style: const TextStyle(fontWeight: FontWeight.bold)),
            const Spacer(),
            IconButton(tooltip: 'Retirer la place ${seat.number}', onPressed: () => _toggle(seat), icon: const Icon(Icons.close, size: 18)),
          ]),
          TextFormField(
            controller: form.name,
            textCapitalization: TextCapitalization.words,
            decoration: InputDecoration(labelText: 'Nom du passager (place ${seat.number}) *'),
            validator: (value) => (value ?? '').trim().length < 2 ? 'Saisissez le nom du passager.' : null,
          ),
          TextFormField(
            controller: form.phone,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(labelText: 'Téléphone'),
          ),
        ]),
      ),
    );
  }
}
