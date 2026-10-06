import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/theme/app_theme.dart';
import '../../../domain/services/reservation/reservation_service.dart';
import '../../widgets/common/error_banner.dart';

class ReservationsPage extends StatefulWidget {
  final ReservationService reservationService;
  final String passengerName;

  const ReservationsPage({super.key, required this.reservationService, this.passengerName = ''});

  @override
  State<ReservationsPage> createState() => _ReservationsPageState();
}

class _ReservationsPageState extends State<ReservationsPage> with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  final _name = TextEditingController();
  final _phone = TextEditingController();
  List<Map<String, dynamic>> _departs = [];
  List<Map<String, dynamic>> _places = [];
  List<Map<String, dynamic>> _tickets = [];
  Map<String, dynamic>? _selectedDepart;
  final Set<int> _selectedPlaces = {};
  bool _loading = true;
  bool _loadingPlaces = false;
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
    _name.text = widget.passengerName;
    _loadDepartures();
    _loadTickets();
  }

  @override
  void dispose() {
    _tabs.dispose();
    _name.dispose();
    _phone.dispose();
    super.dispose();
  }

  Future<void> _loadDepartures() async {
    setState(() { _loading = true; _error = null; });
    try {
      final values = await widget.reservationService.listDepartures();
      if (mounted) setState(() => _departs = values);
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'Impossible de charger les départs.', 'MOBILE_RESERVATIONS_LOAD_ERROR'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadTickets() async {
    try {
      final values = await widget.reservationService.listTickets();
      if (mounted) setState(() => _tickets = values);
    } catch (exception) {
      if (mounted && _tabs.index == 1) setState(() => _error = userError(exception, 'Impossible de charger vos billets.', 'MOBILE_TICKETS_LOAD_ERROR'));
    }
  }

  Future<void> _selectDepart(Map<String, dynamic> item) async {
    setState(() { _selectedDepart = item; _selectedPlaces.clear(); _places = []; _loadingPlaces = true; _error = null; });
    try {
      final values = await widget.reservationService.listAvailablePlaces(item['id'] as int);
      if (mounted) setState(() => _places = values..sort((a, b) => (a['numero_place'] as int).compareTo(b['numero_place'] as int)));
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'Impossible de charger les places.', 'MOBILE_PLACES_LOAD_ERROR'));
    } finally {
      if (mounted) setState(() => _loadingPlaces = false);
    }
  }

  Future<void> _reserve() async {
    if (_selectedDepart == null || _selectedPlaces.isEmpty || _name.text.trim().length < 2) {
      setState(() => _error = 'Choisissez un départ, une place et renseignez le nom du passager.');
      return;
    }
    setState(() { _submitting = true; _error = null; });
    try {
      await widget.reservationService.createAndConfirm(
        _selectedDepart!['id'] as int,
        _selectedPlaces.map((id) => {
          'id_depart_place': id,
          'nom_passager': _name.text.trim(),
          'telephone_passager': _phone.text.trim().isEmpty ? null : _phone.text.trim(),
        }).toList(),
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Réservation confirmée. Vos billets sont disponibles.')));
      _selectedPlaces.clear();
      await _loadTickets();
      _tabs.animateTo(1);
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'La réservation n’a pas pu être confirmée.', 'MOBILE_RESERVATION_CREATE_ERROR'));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  String _route(Map<String, dynamic> item) {
    final itinerary = item['itineraire'] as Map<String, dynamic>?;
    return '${itinerary?['destination_depart']?['nom'] ?? '#${item['id_itineraire']}'} → ${itinerary?['destination_arrivee']?['nom'] ?? '-'}';
  }

  int get _seatColumns {
    if (_places.length <= 8) return 2;
    if (_places.length <= 12) return 3;
    return 4;
  }

  List<Map<String, dynamic>> get _frontPlaces => _places.take(2).toList();

  List<List<Map<String, dynamic>>> get _seatRows {
    final rows = <List<Map<String, dynamic>>>[];
    for (var index = 2; index < _places.length; index += _seatColumns) {
      final end = index + _seatColumns < _places.length ? index + _seatColumns : _places.length;
      rows.add(_places.sublist(index, end));
    }
    return rows;
  }

  Color _seatColor(Map<String, dynamic> place) {
    final id = place['id'] as int;
    if (_selectedPlaces.contains(id)) return AppTheme.primary;
    switch (place['statut']) {
      case 'RESERVEE': return const Color(0xFFF59E0B);
      case 'OCCUPEE': return const Color(0xFFEF4444);
      case 'BLOQUEE': return const Color(0xFF64748B);
      default: return const Color(0xFF10B981);
    }
  }

  void _togglePlace(Map<String, dynamic> place) {
    if (_submitting || place['statut'] != 'DISPONIBLE') return;
    final id = place['id'] as int;
    setState(() {
      if (_selectedPlaces.contains(id)) {
        _selectedPlaces.remove(id);
      } else {
        _selectedPlaces.add(id);
      }
    });
  }

  Widget _seat(Map<String, dynamic> place) {
    final available = place['statut'] == 'DISPONIBLE';
    return Semantics(
      button: true,
      enabled: available,
      label: 'Place ${place['numero_place']}',
      child: GestureDetector(
        onTap: available ? () => _togglePlace(place) : null,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          width: 48,
          height: 48,
          margin: const EdgeInsets.all(4),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: _seatColor(place),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Colors.white.withValues(alpha: 0.35)),
            boxShadow: _selectedPlaces.contains(place['id']) ? const [BoxShadow(color: Colors.black38, blurRadius: 5, offset: Offset(0, 2))] : null,
          ),
          child: Text('${place['numero_place']}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        ),
      ),
    );
  }

  Widget _driverSeat() => Container(
        width: 56,
        height: 56,
        margin: const EdgeInsets.all(4),
        alignment: Alignment.center,
        decoration: BoxDecoration(color: const Color(0xFF475569), borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.white24)),
        child: const Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.airline_seat_recline_normal, size: 19, color: Colors.white70), Text('CH', style: TextStyle(fontSize: 10, color: Colors.white70, fontWeight: FontWeight.bold))]),
      );

  Widget _seatRow(List<Map<String, dynamic>> places) {
    final children = <Widget>[];
    for (var index = 0; index < places.length; index++) {
      if (index == places.length ~/ 2) children.add(const SizedBox(width: 22));
      children.add(_seat(places[index]));
    }
    return Row(mainAxisAlignment: MainAxisAlignment.center, children: children);
  }

  Widget _seatLayout() => Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 8),
        decoration: BoxDecoration(color: const Color(0xFF172554), borderRadius: BorderRadius.circular(18), border: Border.all(color: Colors.white12)),
        child: Column(children: [
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [_driverSeat(), const SizedBox(width: 18), ..._frontPlaces.map(_seat)]),
          const Divider(color: Colors.white24, height: 24),
          ..._seatRows.map(_seatRow),
        ]),
      );

  Widget _legendItem(Color color, String label) => Row(mainAxisSize: MainAxisSize.min, children: [Container(width: 12, height: 12, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3))), const SizedBox(width: 5), Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12))]);

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Réservations & billets'), actions: [IconButton(onPressed: () { _loadDepartures(); _loadTickets(); }, icon: const Icon(Icons.refresh))], bottom: TabBar(controller: _tabs, tabs: const [Tab(text: 'Réserver'), Tab(text: 'Mes billets')])),
        body: TabBarView(controller: _tabs, children: [_buildReservation(), _buildTickets()]),
      );

  Widget _buildReservation() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    return SingleChildScrollView(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      if (_error != null) ErrorBanner(message: _error!),
      const Text('Rechercher un départ', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      if (_departs.isEmpty) const Text('Aucun départ disponible pour le moment.'),
      ..._departs.map((item) => Card(color: AppTheme.surface, child: ListTile(selected: _selectedDepart?['id'] == item['id'], onTap: () => _selectDepart(item), title: Text(_route(item)), subtitle: Text('${item['date_depart']} à ${item['heure_depart']} · ${item['places_disponibles']} place(s) · ${item['tarif']?['prix'] ?? '-'} ${item['tarif']?['devise'] ?? ''}'), trailing: const Icon(Icons.chevron_right)))),
      if (_selectedDepart != null) ...[
        const SizedBox(height: 18),
        const Text('Informations du passager', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        TextField(controller: _name, decoration: const InputDecoration(labelText: 'Nom complet *')),
        TextField(controller: _phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Téléphone')),
        const SizedBox(height: 18),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('Plan du véhicule', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)), Text('${_selectedPlaces.length} sélectionnée(s)', style: const TextStyle(color: AppTheme.primaryAccent))]),
        const SizedBox(height: 6),
        const Text('Sélectionnez une place verte. Les places occupées ou bloquées sont désactivées.', style: TextStyle(color: Colors.white70, fontSize: 12)),
        const SizedBox(height: 12),
        if (_loadingPlaces) const Padding(padding: EdgeInsets.all(16), child: Center(child: CircularProgressIndicator())) else if (_places.isEmpty) const Text('Aucune place disponible pour ce départ.') else Column(children: [
          Wrap(alignment: WrapAlignment.center, spacing: 14, runSpacing: 6, children: [_legendItem(const Color(0xFF10B981), 'Disponible'), _legendItem(AppTheme.primary, 'Sélectionnée'), _legendItem(const Color(0xFFF59E0B), 'Réservée'), _legendItem(const Color(0xFF64748B), 'Bloquée')]),
          const SizedBox(height: 12),
          _seatLayout(),
        ]),
        const SizedBox(height: 16),
        SizedBox(width: double.infinity, child: ElevatedButton(onPressed: _submitting ? null : _reserve, child: Text(_submitting ? 'Confirmation…' : 'Confirmer la réservation'))),
      ],
    ]));
  }

  Widget _buildTickets() {
    if (_tickets.isEmpty) return const Center(child: Text('Aucun billet enregistré.'));
    return RefreshIndicator(onRefresh: _loadTickets, child: ListView.builder(padding: const EdgeInsets.all(16), itemCount: _tickets.length, itemBuilder: (_, index) { final item = _tickets[index]; return Card(color: AppTheme.surface, child: ListTile(leading: const Icon(Icons.qr_code_2, color: Colors.blue), title: Text(item['numero_billet'] as String? ?? '-'), subtitle: Text('${item['destination_depart'] ?? '-'} → ${item['destination_arrivee'] ?? '-'}\nPlace ${item['numero_place'] ?? '-'} · ${item['date_depart'] ?? '-'} ${item['heure_depart'] ?? ''}'), isThreeLine: true, trailing: Chip(label: Text(item['statut'] as String? ?? '-')))); }));
  }
}
