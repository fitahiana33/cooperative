import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/error_banner.dart';

class DepartsPage extends StatefulWidget {
  final ApiClient apiClient;

  const DepartsPage({super.key, required this.apiClient});

  @override
  State<DepartsPage> createState() => _DepartsPageState();
}

class _DepartsPageState extends State<DepartsPage> {
  final _search = TextEditingController();
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;
  String? _error;
  int _page = 1;
  int _pages = 1;
  int _total = 0;

  List<Map<String, dynamic>> _readItems(dynamic data) {
    final value = data is Map && data['items'] is List ? data['items'] : data;
    if (value is! List) return [];
    return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }

  String _routeName(Map<String, dynamic> item) {
    final itinerary = item['itineraire'] as Map<String, dynamic>?;
    final departure = itinerary?['destination_depart']?['nom'] ?? '#${item['id_itineraire']}';
    final arrival = itinerary?['destination_arrivee']?['nom'] ?? '-';
    return '$departure → $arrival';
  }

  String _statusLabel(String value) => {
        'PROGRAMME': 'Programmé',
        'EMBARQUEMENT': 'Embarquement',
        'RETARDE': 'Retardé',
        'PARTI': 'Parti',
        'TERMINE': 'Terminé',
        'ANNULE': 'Annulé',
      }[value] ?? value;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (!mounted) return;
    setState(() { _loading = true; _error = null; });
    try {
      final response = await widget.apiClient.get('/departs', queryParameters: {
        'page': _page,
        'page_size': 20,
        'search': _search.text.trim().isEmpty ? null : _search.text.trim(),
        'sort_by': 'date_depart',
        'sort_order': 'asc',
      });
      final data = response.data;
      final meta = data is Map<String, dynamic> ? data : <String, dynamic>{};
      if (mounted) {
        setState(() {
          _items = _readItems(data);
          _total = meta['total'] as int? ?? _items.length;
          _pages = meta['pages'] as int? ?? 1;
        });
      }
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'Impossible de charger les départs.', 'MOBILE_DEPARTS_LOAD_ERROR'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _details(Map<String, dynamic> item) async {
    final vehicle = item['vehicule']?['immatriculation'] ?? '#${item['id_vehicule']}';
    final cooperative = item['cooperative']?['nom'] ?? '#${item['id_cooperative']}';
    await showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(_routeName(item)),
        content: Text(
          'Date : ${item['date_depart']}\n'
          'Heure : ${item['heure_depart']}\n'
          'Coopérative : $cooperative\n'
          'Véhicule : $vehicle\n'
          'Places disponibles : ${item['places_disponibles']} / ${item['nombre_places']}\n'
          'Tarif : ${item['tarif']?['prix'] ?? '-'} ${item['tarif']?['devise'] ?? ''}\n'
          'Statut : ${_statusLabel(item['statut'] as String? ?? '')}',
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Fermer'))],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Départs et planning'), actions: [IconButton(onPressed: _load, icon: const Icon(Icons.refresh))]),
      body: Column(children: [
        Padding(padding: const EdgeInsets.all(16), child: TextField(controller: _search, onSubmitted: (_) { _page = 1; _load(); }, decoration: const InputDecoration(labelText: 'Rechercher', prefixIcon: Icon(Icons.search)))),
        if (_error != null) Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: ErrorBanner(message: _error!)),
        Expanded(child: _loading ? const Center(child: CircularProgressIndicator()) : _items.isEmpty ? const Center(child: Text('Aucun départ enregistré.')) : ListView.builder(padding: const EdgeInsets.all(16), itemCount: _items.length, itemBuilder: (context, index) {
          final item = _items[index];
          final status = item['statut'] as String? ?? '';
          return Card(color: AppTheme.surface, child: ListTile(onTap: () => _details(item), leading: const Icon(Icons.departure_board, color: Colors.blue), title: Text(_routeName(item)), subtitle: Text('${item['date_depart']} à ${item['heure_depart']}\n${item['places_disponibles']} place(s) disponible(s)'), isThreeLine: true, trailing: Chip(label: Text(_statusLabel(status)), backgroundColor: status == 'ANNULE' ? Colors.red.shade100 : Colors.blue.shade100)));
        })),
        if (!_loading) Padding(padding: const EdgeInsets.all(8), child: Text('Page $_page / $_pages — $_total départ(s)')),
        if (!_loading && _pages > 1) Row(mainAxisAlignment: MainAxisAlignment.center, children: [TextButton(onPressed: _page > 1 ? () { setState(() => _page--); _load(); } : null, child: const Text('Précédent')), TextButton(onPressed: _page < _pages ? () { setState(() => _page++); _load(); } : null, child: const Text('Suivant'))]),
      ]),
    );
  }
}
