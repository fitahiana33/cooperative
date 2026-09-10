import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/error_banner.dart';

class ReservationsPage extends StatefulWidget {
  final ApiClient apiClient;
  final String passengerName;

  const ReservationsPage({super.key, required this.apiClient, this.passengerName = ''});

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

  List<Map<String, dynamic>> _items(dynamic data) {
    final value = data is Map && data['items'] is List ? data['items'] : data;
    if (value is! List) return [];
    return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }

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
      final today = DateTime.now().toIso8601String().substring(0, 10);
      final response = await widget.apiClient.get('/departs', queryParameters: {'page': 1, 'page_size': 100, 'date_from': today, 'sort_by': 'date_depart', 'sort_order': 'asc'});
      if (mounted) setState(() => _departs = _items(response.data));
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'Impossible de charger les départs.', 'MOBILE_RESERVATIONS_LOAD_ERROR'));
    } finally { if (mounted) setState(() => _loading = false); }
  }

  Future<void> _loadTickets() async {
    try {
      final response = await widget.apiClient.get('/billets', queryParameters: {'page': 1, 'page_size': 100});
      if (mounted) setState(() => _tickets = _items(response.data));
    } catch (exception) {
      if (mounted && _tabs.index == 1) setState(() => _error = userError(exception, 'Impossible de charger vos billets.', 'MOBILE_TICKETS_LOAD_ERROR'));
    }
  }

  Future<void> _selectDepart(Map<String, dynamic> item) async {
    setState(() { _selectedDepart = item; _selectedPlaces.clear(); _places = []; _loadingPlaces = true; _error = null; });
    try {
      final response = await widget.apiClient.get('/departs/${item['id']}/places', queryParameters: {'available_only': true});
      if (mounted) setState(() => _places = _items(response.data));
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'Impossible de charger les places.', 'MOBILE_PLACES_LOAD_ERROR'));
    } finally { if (mounted) setState(() => _loadingPlaces = false); }
  }

  Future<void> _reserve() async {
    if (_selectedDepart == null || _selectedPlaces.isEmpty || _name.text.trim().length < 2) {
      setState(() => _error = 'Choisissez un départ, une place et renseignez le nom du passager.');
      return;
    }
    setState(() { _submitting = true; _error = null; });
    try {
      final response = await widget.apiClient.post('/reservations', data: {'id_depart': _selectedDepart!['id'], 'places': _selectedPlaces.map((id) => {'id_depart_place': id, 'nom_passager': _name.text.trim(), 'telephone_passager': _phone.text.trim().isEmpty ? null : _phone.text.trim()}).toList()});
      final reservation = response.data as Map<String, dynamic>;
      await widget.apiClient.post('/reservations/${reservation['id']}/confirm');
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Réservation confirmée. Vos billets sont disponibles.')));
      _selectedPlaces.clear();
      await _loadTickets();
      _tabs.animateTo(1);
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'La réservation n’a pas pu être confirmée.', 'MOBILE_RESERVATION_CREATE_ERROR'));
    } finally { if (mounted) setState(() => _submitting = false); }
  }

  String _route(Map<String, dynamic> item) {
    final itinerary = item['itineraire'] as Map<String, dynamic>?;
    return '${itinerary?['destination_depart']?['nom'] ?? '#${item['id_itineraire']}'} → ${itinerary?['destination_arrivee']?['nom'] ?? '-'}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Réservations & billets'), actions: [IconButton(onPressed: () { _loadDepartures(); _loadTickets(); }, icon: const Icon(Icons.refresh))], bottom: TabBar(controller: _tabs, tabs: const [Tab(text: 'Réserver'), Tab(text: 'Mes billets')])),
      body: TabBarView(controller: _tabs, children: [_buildReservation(), _buildTickets()]),
    );
  }

  Widget _buildReservation() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    return SingleChildScrollView(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      if (_error != null) ErrorBanner(message: _error!),
      const Text('Rechercher un départ', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      if (_departs.isEmpty) const Text('Aucun départ disponible pour le moment.'),
      ..._departs.map((item) => Card(color: AppTheme.surface, child: ListTile(selected: _selectedDepart?['id'] == item['id'], onTap: () => _selectDepart(item), title: Text(_route(item)), subtitle: Text('${item['date_depart']} à ${item['heure_depart']} · ${item['places_disponibles']} place(s) · ${item['tarif']?['prix'] ?? '-'} ${item['tarif']?['devise'] ?? ''}'), trailing: const Icon(Icons.chevron_right)))),
      if (_selectedDepart != null) ...[
        const SizedBox(height: 18), const Text('Informations du passager', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        TextField(controller: _name, decoration: const InputDecoration(labelText: 'Nom complet *')), TextField(controller: _phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Téléphone')),
        const SizedBox(height: 14), const Text('Choisissez les places disponibles', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        if (_loadingPlaces) const Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()) else Wrap(spacing: 8, runSpacing: 8, children: _places.map((place) { final id = place['id'] as int; final selected = _selectedPlaces.contains(id); return ChoiceChip(label: Text('${place['numero_place']}'), selected: selected, onSelected: (_) => setState(() { if (selected) _selectedPlaces.remove(id); else _selectedPlaces.add(id); })); }).toList()),
        const SizedBox(height: 16), SizedBox(width: double.infinity, child: ElevatedButton(onPressed: _submitting ? null : _reserve, child: Text(_submitting ? 'Confirmation…' : 'Confirmer la réservation'))),
      ],
    ]));
  }

  Widget _buildTickets() {
    if (_tickets.isEmpty) return const Center(child: Text('Aucun billet enregistré.'));
    return RefreshIndicator(onRefresh: _loadTickets, child: ListView.builder(padding: const EdgeInsets.all(16), itemCount: _tickets.length, itemBuilder: (_, index) { final item = _tickets[index]; return Card(color: AppTheme.surface, child: ListTile(leading: const Icon(Icons.qr_code_2, color: Colors.blue), title: Text(item['numero_billet'] as String? ?? '-'), subtitle: Text('${item['destination_depart'] ?? '-'} → ${item['destination_arrivee'] ?? '-'}\nPlace ${item['numero_place'] ?? '-'} · ${item['date_depart'] ?? '-'} ${item['heure_depart'] ?? ''}'), isThreeLine: true, trailing: Chip(label: Text(item['statut'] as String? ?? '-')))); }));
  }
}
