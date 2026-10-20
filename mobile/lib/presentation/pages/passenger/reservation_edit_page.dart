import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/user_error.dart';
import '../../../data/models/travel/travel_models.dart';
import '../../../data/repositories/travel/travel_repository_impl.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/travel/seat_map.dart';

class ReservationEditPage extends ConsumerStatefulWidget {
  final Reservation reservation;

  const ReservationEditPage({super.key, required this.reservation});

  @override
  ConsumerState<ReservationEditPage> createState() => _ReservationEditPageState();
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

class _ReservationEditPageState extends ConsumerState<ReservationEditPage> {
  final _formKey = GlobalKey<FormState>();
  final _reservationName = TextEditingController();
  final _selected = <Seat>[];
  final _forms = <int, _PassengerForm>{};
  List<Seat> _seats = [];
  List<Departure> _departures = [];
  Departure? _selectedDeparture;
  late DateTime _selectedDate;
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _selectedDate = DateTime.tryParse(widget.reservation.departureDate) ?? DateTime.now();
    _reservationName.text = widget.reservation.passengers.isEmpty ? '' : widget.reservation.passengers.first.name;
    _loadInitial();
  }

  @override
  void dispose() {
    _reservationName.dispose();
    for (final form in _forms.values) {
      form.dispose();
    }
    super.dispose();
  }

  Future<void> _loadSeats() async {
    try {
      final departureId = _selectedDeparture?.id ?? widget.reservation.departureId;
      final seats = await ref.read(travelRepositoryProvider).listSeats(departureId);
      final current = departureId == widget.reservation.departureId ? {for (final passenger in widget.reservation.passengers) passenger.departurePlaceId: passenger} : <int, PassengerSeat>{};
      if (!mounted) return;
      setState(() {
        _seats = seats;
        for (final seat in seats) {
          final passenger = current[seat.id];
          if (passenger != null) {
            _selected.add(seat);
            _forms[seat.id] = _PassengerForm(name: passenger.name, phone: passenger.phone ?? '');
          }
        }
        _loading = false;
      });
    } catch (error) {
      if (mounted) setState(() { _error = userError(error, 'Impossible de charger les places.', 'MOBILE_EDIT_SEATS_ERROR'); _loading = false; });
    }
  }

  Departure _currentDeparture() => Departure(
        id: widget.reservation.departureId,
        date: widget.reservation.departureDate,
        time: widget.reservation.departureTime,
        origin: widget.reservation.origin,
        destination: widget.reservation.destination,
        cooperative: widget.reservation.cooperative,
        vehiclePlate: '',
        seats: _seats.length,
        freeSeats: _seats.where((seat) => seat.isFree).length,
        price: widget.reservation.passengers.isEmpty ? 0 : widget.reservation.amount / widget.reservation.passengers.length,
        currency: 'MGA',
        status: widget.reservation.departureStatus,
      );

  Future<void> _loadInitial() async {
    await _loadSeats();
    await _loadDepartures();
  }

  Future<void> _loadDepartures() async {
    try {
      final result = await ref.read(travelRepositoryProvider).searchDepartures(date: _selectedDate);
      final items = [...result.items.where((item) => item.isBookable)];
      if (_selectedDate.toIso8601String().substring(0, 10) == widget.reservation.departureDate && !items.any((item) => item.id == widget.reservation.departureId)) {
        items.insert(0, _currentDeparture());
      }
      if (!mounted) return;
      final previousId = _selectedDeparture?.id;
      final matching = items.where((item) => item.id == (previousId ?? widget.reservation.departureId)).toList();
      setState(() {
        _departures = items;
        _selectedDeparture = matching.isNotEmpty ? matching.first : (items.isEmpty ? null : items.first);
        _error = null;
      });
      if (_selectedDeparture != null && _selectedDeparture!.id != (previousId ?? widget.reservation.departureId)) await _loadSeats();
    } catch (error) {
      if (mounted) setState(() => _error = userError(error, 'Impossible de charger les départs.', 'MOBILE_EDIT_DEPARTURES_ERROR'));
    }
  }

  Future<void> _chooseDate() async {
    final picked = await showDatePicker(context: context, firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 365)), initialDate: _selectedDate);
    if (picked == null || !mounted) return;
    setState(() {
      _selectedDate = picked;
      _selectedDeparture = null;
      _selected.clear();
      for (final form in _forms.values) {
        form.dispose();
      }
      _forms.clear();
    });
    await _loadDepartures();
  }

  Future<void> _chooseDeparture(int? id) async {
    if (id == null) return;
    final departure = _departures.firstWhere((item) => item.id == id);
    setState(() {
      _selectedDeparture = departure;
      _selected.clear();
      for (final form in _forms.values) {
        form.dispose();
      }
      _forms.clear();
    });
    await _loadSeats();
  }

  void _toggle(Seat seat) {
    setState(() {
      if (_selected.any((item) => item.id == seat.id)) {
        _selected.removeWhere((item) => item.id == seat.id);
        _forms.remove(seat.id)?.dispose();
      } else {
        _selected.add(seat);
        _forms[seat.id] = _PassengerForm();
      }
      _error = null;
    });
  }

  Future<void> _save() async {
    if (_selected.isEmpty || _reservationName.text.trim().length < 2 || !(_formKey.currentState?.validate() ?? false)) {
      setState(() => _error = 'Sélectionnez au moins une place et complétez les passagers.');
      return;
    }
    setState(() { _saving = true; _error = null; });
    try {
      final passengers = _selected.map((seat) {
        final form = _forms[seat.id]!;
        final phone = form.phone.text.trim();
        return {
          'id_depart_place': seat.id,
          'nom_passager': form.name.text.trim().isEmpty ? _reservationName.text.trim() : form.name.text.trim(),
          'telephone_passager': phone.isEmpty ? null : phone,
        };
      }).toList();
      final updated = await ref.read(travelRepositoryProvider).updateReservation(widget.reservation.id, _selectedDeparture?.id ?? widget.reservation.departureId, passengers);
      if (mounted) Navigator.pop(context, updated);
    } catch (error) {
      if (mounted) setState(() => _error = userError(error, 'La modification n’a pas pu être enregistrée.', 'MOBILE_EDIT_RESERVATION_ERROR'));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Modifier la réservation')),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : Form(
                key: _formKey,
                child: ListView(padding: const EdgeInsets.all(16), children: [
                  const Text('Choisissez les places et vérifiez les informations des passagers.'),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(onPressed: _saving ? null : _chooseDate, icon: const Icon(Icons.calendar_today_outlined), label: Text('Date : ${_selectedDate.toIso8601String().substring(0, 10)}')),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<int>(
                    value: _selectedDeparture?.id,
                    decoration: const InputDecoration(labelText: 'DÃ©part *'),
                    items: _departures.map((departure) => DropdownMenuItem<int>(value: departure.id, child: Text('${departure.time.length >= 5 ? departure.time.substring(0, 5) : departure.time} · ${departure.origin} → ${departure.destination}'))).toList(),
                    onChanged: _saving ? null : _chooseDeparture,
                  ),
                  const SizedBox(height: 8),
                  TextFormField(controller: _reservationName, textCapitalization: TextCapitalization.words, decoration: const InputDecoration(labelText: 'Nom de la personne qui réserve *', helperText: 'Ce nom sera repris pour les places sans nom individuel.'), validator: (value) => (value ?? '').trim().length < 2 ? 'Nom obligatoire.' : null),
                  const SizedBox(height: 16),
                  SeatMap(
                    seats: _seats,
                    selected: {for (final seat in _selected) seat.id},
                    seatsBesideDriver: 2,
                    seatsPerRow: 4,
                    enabled: !_saving,
                    onToggle: _toggle,
                  ),
                  const SizedBox(height: 16),
                  ..._selected.map((seat) {
                    final form = _forms[seat.id]!;
                    return Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(children: [
                      Row(children: [Text('Place ${seat.number}', style: const TextStyle(fontWeight: FontWeight.bold)), const Spacer(), IconButton(onPressed: () => _toggle(seat), icon: const Icon(Icons.close))]),
                      TextFormField(controller: form.name, decoration: const InputDecoration(labelText: 'Nom individuel (facultatif)', helperText: 'Laisser vide pour reprendre le réservataire.')),
                      TextFormField(controller: form.phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Téléphone')),
                    ])));
                  }),
                  if (_error != null) ...[const SizedBox(height: 12), ErrorBanner(message: _error!)],
                  const SizedBox(height: 16),
                  ElevatedButton.icon(onPressed: _saving ? null : _save, icon: const Icon(Icons.save_outlined), label: Text(_saving ? 'Enregistrement…' : 'Enregistrer la modification')),
                ]),
              ),
      );
}
