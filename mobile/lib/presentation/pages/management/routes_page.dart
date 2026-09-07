import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/error_banner.dart';

class RoutesPage extends StatefulWidget {
  final ApiClient apiClient;
  final Set<String> permissions;
  final bool isAdmin;

  const RoutesPage({
    super.key,
    required this.apiClient,
    this.permissions = const {},
    this.isAdmin = false,
  });

  @override
  State<RoutesPage> createState() => _RoutesPageState();
}

class _RoutesPageState extends State<RoutesPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  final _search = TextEditingController();
  List<Map<String, dynamic>> _destinations = [];
  List<Map<String, dynamic>> _itineraires = [];
  List<Map<String, dynamic>> _tarifs = [];
  List<Map<String, dynamic>> _cooperatives = [];
  bool _loading = true;
  String? _error;
  int _page = 1;
  int _pages = 1;
  int _total = 0;

  bool _can(String permission) =>
      widget.isAdmin || widget.permissions.contains(permission);
  List<Map<String, dynamic>> _items(dynamic data) {
    final value = data is Map && data['items'] is List ? data['items'] : data;
    if (value is! List) return [];
    return value
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  List<Map<String, dynamic>> get _visibleItems {
    final query = _search.text.trim().toLowerCase();
    final source = _tabs.index == 0
        ? _destinations
        : _tabs.index == 1
            ? _itineraires
            : _tarifs;
    if (query.isEmpty) return source;
    return source.where((item) {
      final text = item.values.map((value) => '$value').join(' ').toLowerCase();
      return text.contains(query);
    }).toList();
  }

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
    _tabs.addListener(() {
      if (!_tabs.indexIsChanging) {
        _page = 1;
        _load();
      }
      setState(() {});
    });
    _load();
  }

  @override
  void dispose() {
    _tabs.dispose();
    _search.dispose();
    super.dispose();
  }

  Future<void> _load({bool showLoading = true}) async {
    if (!mounted) return;
    setState(() {
      if (showLoading) _loading = true;
      _error = null;
    });
    try {
      final path = _tabs.index == 0
          ? '/destinations'
          : _tabs.index == 1
              ? '/itineraires'
              : '/tarifs';
      final sort = _tabs.index == 0
          ? 'nom'
          : _tabs.index == 1
              ? 'created_at'
              : 'date_debut';
      final response = await widget.apiClient.get(path, queryParameters: {
        'page': _page,
        'page_size': 20,
        'search': _search.text.trim().isEmpty ? null : _search.text.trim(),
        'sort_by': sort,
        'sort_order': 'asc',
      });
      final items = _items(response.data);
      if (!mounted) return;
      setState(() {
        if (_tabs.index == 0) _destinations = items;
        if (_tabs.index == 1) _itineraires = items;
        if (_tabs.index == 2) _tarifs = items;
        final data = response.data;
        _total = data is Map ? data['total'] as int? ?? items.length : items.length;
        _pages = data is Map ? data['pages'] as int? ?? 1 : 1;
        _loading = false;
      });
      await _loadReferences();
    } catch (exception) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = userError(exception, 'Impossible de charger les donnees.', 'MOBILE_ROUTES_LOAD_ERROR');
      });
    }
  }

  Future<void> _loadReferences() async {
    try {
      final responses = await Future.wait([
        widget.apiClient.get('/destinations', queryParameters: {'page': 1, 'page_size': 100, 'sort_by': 'nom', 'sort_order': 'asc'}),
        widget.apiClient.get('/cooperatives', queryParameters: {'page': 1, 'page_size': 100, 'sort_by': 'nom', 'sort_order': 'asc'}),
      ]);
      if (!mounted) return;
      setState(() {
        _destinations = _items(responses[0].data);
        _cooperatives = _items(responses[1].data);
      });
    } catch (_) {
      // The current list remains usable if a reference list is unavailable.
    }
  }

  String _destinationName(dynamic id) =>
      _destinations.firstWhere((item) => item['id'] == id, orElse: () => {})['nom'] as String? ?? 'Destination #$id';

  String _itineraryName(Map<String, dynamic> item) {
    final depart = item['destination_depart'] is Map
        ? item['destination_depart']['nom']
        : _destinationName(item['id_destination_depart']);
    final arrivee = item['destination_arrivee'] is Map
        ? item['destination_arrivee']['nom']
        : _destinationName(item['id_destination_arrivee']);
    return '$depart - $arrivee';
  }

  Future<void> _toggle(Map<String, dynamic> item) async {
    if (!_can(_tabs.index == 0 ? 'DESTINATION_UPDATE' : _tabs.index == 1 ? 'ITINERAIRE_UPDATE' : 'TARIF_UPDATE')) return;
    try {
      final path = _tabs.index == 0
          ? '/destinations/${item['id']}/toggle'
          : _tabs.index == 1
              ? '/itineraires/${item['id']}/toggle'
              : '/tarifs/${item['id']}/toggle';
      await widget.apiClient.patch(path);
      await _load(showLoading: false);
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'Impossible de modifier le statut.', 'MOBILE_ROUTES_TOGGLE_ERROR'));
    }
  }

  Future<void> _delete(Map<String, dynamic> item) async {
    if (_tabs.index == 2 || !_can(_tabs.index == 0 ? 'DESTINATION_DELETE' : 'ITINERAIRE_DELETE')) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Confirmation'),
        content: const Text('Supprimer cet element ? Cette action est reservee aux elements non utilises.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Annuler')),
          ElevatedButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Supprimer')),
        ],
      ),
    ) ?? false;
    if (!confirmed) return;
    try {
      final path = _tabs.index == 0 ? '/destinations/${item['id']}' : '/itineraires/${item['id']}';
      await widget.apiClient.delete(path);
      await _load(showLoading: false);
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'Suppression impossible. Desactivez plutot cet element.', 'MOBILE_ROUTES_DELETE_ERROR'));
    }
  }

  Future<void> _showForm([Map<String, dynamic>? current]) async {
    await _loadReferences();
    if (!mounted) return;
    final formKey = GlobalKey<FormState>();
    final name = TextEditingController(text: current?['nom'] as String? ?? '');
    final region = TextEditingController(text: current?['region'] as String? ?? '');
    final description = TextEditingController(text: current?['description'] as String? ?? '');
    final distance = TextEditingController(text: '${current?['distance_km'] ?? ''}');
    final duration = TextEditingController(text: '${current?['duree_estimee_minutes'] ?? ''}');
    final price = TextEditingController(text: '${current?['prix'] ?? ''}');
    final currency = TextEditingController(text: current?['devise'] as String? ?? 'MGA');
    final start = TextEditingController(text: current?['date_debut'] as String? ?? '');
    final end = TextEditingController(text: current?['date_fin'] as String? ?? '');
    int? depart = current?['id_destination_depart'] as int?;
    int? arrivee = current?['id_destination_arrivee'] as int?;
    int? itineraryId = current?['id_itineraire'] as int?;
    int? cooperativeId = current?['id_cooperative'] as int?;
    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(builder: (context, setDialogState) {
          final title = current == null ? 'Ajouter' : 'Modifier';
          return AlertDialog(
            title: Text('$title ${_tabs.index == 0 ? 'une destination' : _tabs.index == 1 ? 'un itineraire' : 'un tarif'}'),
            content: SizedBox(width: 500, child: Form(key: formKey, child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
              if (_tabs.index == 0) ...[
                _input(name, 'Nom', required: true), _input(region, 'Region'), _input(description, 'Description', maxLines: 3),
              ] else if (_tabs.index == 1) ...[
                DropdownButtonFormField<int>(initialValue: depart, decoration: const InputDecoration(labelText: 'Depart'), items: _destinations.map((item) => DropdownMenuItem<int>(value: item['id'] as int, child: Text(item['nom'] as String))).toList(), onChanged: (value) => setDialogState(() => depart = value), validator: (value) => value == null ? 'Depart obligatoire' : null),
                DropdownButtonFormField<int>(initialValue: arrivee, decoration: const InputDecoration(labelText: 'Arrivee'), items: _destinations.map((item) => DropdownMenuItem<int>(value: item['id'] as int, child: Text(item['nom'] as String))).toList(), onChanged: (value) => setDialogState(() => arrivee = value), validator: (value) => value == null ? 'Arrivee obligatoire' : null),
                _input(distance, 'Distance (km)', keyboardType: TextInputType.number), _input(duration, 'Duree (minutes)', keyboardType: TextInputType.number), _input(description, 'Description', maxLines: 3),
              ] else ...[
                DropdownButtonFormField<int>(initialValue: itineraryId, decoration: const InputDecoration(labelText: 'Itineraire'), items: _itineraires.map((item) => DropdownMenuItem<int>(value: item['id'] as int, child: Text(_itineraryName(item)))).toList(), onChanged: current == null ? (value) => setDialogState(() => itineraryId = value) : null, validator: (value) => value == null ? 'Itineraire obligatoire' : null),
                DropdownButtonFormField<int?>(initialValue: cooperativeId, decoration: const InputDecoration(labelText: 'Cooperative (vide = general)'), items: [const DropdownMenuItem<int?>(value: null, child: Text('Tarif general')), ..._cooperatives.map((item) => DropdownMenuItem<int?>(value: item['id'] as int, child: Text(item['nom'] as String)))], onChanged: (value) => setDialogState(() => cooperativeId = value)),
                _input(price, 'Prix', required: true, keyboardType: TextInputType.number), _input(currency, 'Devise', required: true), _input(start, 'Date debut (AAAA-MM-JJ)'), _input(end, 'Date fin (AAAA-MM-JJ)'),
              ],
            ]))),),
            actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Annuler')), ElevatedButton(onPressed: () async {
              if (!(formKey.currentState?.validate() ?? false)) return;
              final payload = _tabs.index == 0
                  ? {'nom': name.text.trim(), 'region': region.text.trim().isEmpty ? null : region.text.trim(), 'description': description.text.trim().isEmpty ? null : description.text.trim()}
                  : _tabs.index == 1
                      ? {'id_destination_depart': depart, 'id_destination_arrivee': arrivee, 'distance_km': double.tryParse(distance.text.trim()), 'duree_estimee_minutes': int.tryParse(duration.text.trim()), 'description': description.text.trim().isEmpty ? null : description.text.trim()}
                      : {'id_itineraire': itineraryId, 'id_cooperative': cooperativeId, 'prix': double.tryParse(price.text.trim()), 'devise': currency.text.trim(), 'date_debut': start.text.trim().isEmpty ? null : start.text.trim(), 'date_fin': end.text.trim().isEmpty ? null : end.text.trim()};
              try {
                final path = _tabs.index == 0 ? '/destinations' : _tabs.index == 1 ? '/itineraires' : '/tarifs';
                if (current == null) { await widget.apiClient.post(path, data: payload); } else { await widget.apiClient.put('$path/${current['id']}', data: payload); }
                if (dialogContext.mounted) Navigator.pop(dialogContext);
                await _load(showLoading: false);
              } catch (exception) { if (mounted) setState(() => _error = userError(exception, 'Enregistrement impossible.', 'MOBILE_ROUTES_FORM_ERROR')); }
            }, child: const Text('Enregistrer'))],
          );
        }),
      );
    } finally {
      for (final controller in [name, region, description, distance, duration, price, currency, start, end]) { controller.dispose(); }
    }
  }

  Future<void> _details(Map<String, dynamic> current) async {
    if (_tabs.index == 0) {
      await showDialog<void>(context: context, builder: (_) => AlertDialog(title: Text(current['nom'] as String? ?? 'Destination'), content: Text('Region : ${current['region'] ?? '-'}\n\n${current['description'] ?? 'Aucune description.'}'), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Fermer'))]));
      return;
    }
    if (_tabs.index == 2) {
      await showDialog<void>(context: context, builder: (_) => AlertDialog(title: const Text('Detail du tarif'), content: Text('Prix : ${current['prix']} ${current['devise']}\nPortee : ${current['cooperative']?['nom'] ?? 'Generale'}\nPeriode : ${current['date_debut']} - ${current['date_fin'] ?? '-'}'), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Fermer'))]));
      return;
    }
    try {
      final response = await widget.apiClient.get('/itineraires/${current['id']}');
      final associations = _items(await widget.apiClient.get('/itineraires/${current['id']}/cooperatives').then((value) => value.data));
      if (!mounted) return;
      await showDialog<void>(context: context, builder: (_) => AlertDialog(title: Text(_itineraryName(response.data as Map<String, dynamic>)), content: SizedBox(width: 450, child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Distance : ${current['distance_km'] ?? '-'} km'), Text('Duree : ${current['duree_estimee_minutes'] ?? '-'} minutes'), const SizedBox(height: 16), const Text('Cooperatives autorisees', style: TextStyle(fontWeight: FontWeight.bold)), ...associations.map((item) => ListTile(dense: true, title: Text(item['cooperative']?['nom'] ?? 'Cooperative #${item['id_cooperative']}'), subtitle: Text(item['is_active'] == true ? 'Active' : 'Inactive')))])), actions: [if (_can('ITINERAIRE_COOPERATIVE_MANAGE')) TextButton(onPressed: () { Navigator.pop(context); _showAttach(current['id'] as int); }, child: const Text('Associer')), TextButton(onPressed: () => Navigator.pop(context), child: const Text('Fermer'))]));
    } catch (exception) { if (mounted) setState(() => _error = userError(exception, 'Impossible de charger le detail.', 'MOBILE_ROUTE_DETAIL_ERROR')); }
  }

  Future<void> _showAttach(int itineraryId) async {
    int? selected;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setStateDialog) => AlertDialog(
          title: const Text('Associer une cooperative'),
          content: DropdownButtonFormField<int>(
            initialValue: selected,
            items: _cooperatives
                .map((item) => DropdownMenuItem<int>(
                      value: item['id'] as int,
                      child: Text(item['nom'] as String),
                    ))
                .toList(),
            onChanged: (value) => setStateDialog(() => selected = value),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Annuler'),
            ),
            ElevatedButton(
              onPressed: selected == null
                  ? null
                  : () async {
                      try {
                        await widget.apiClient.post(
                          '/itineraires/$itineraryId/cooperatives/$selected',
                          data: {},
                        );
                        if (dialogContext.mounted) Navigator.pop(dialogContext);
                      } catch (exception) {
                        if (mounted) {
                          setState(() => _error = userError(
                                exception,
                                'Association impossible.',
                                'MOBILE_ROUTE_COOPERATIVE_ERROR',
                              ));
                        }
                      }
                    },
              child: const Text('Associer'),
            ),
          ],
        ),
      ),
    );
  }

  TextFormField _input(TextEditingController controller, String label, {bool required = false, int maxLines = 1, TextInputType? keyboardType}) => TextFormField(controller: controller, maxLines: maxLines, keyboardType: keyboardType, decoration: InputDecoration(labelText: label), validator: required ? (value) => value == null || value.trim().isEmpty ? '$label obligatoire' : null : null);

  @override
  Widget build(BuildContext context) {
    final items = _visibleItems;
    final canRead = _can(_tabs.index == 0 ? 'DESTINATION_READ' : _tabs.index == 1 ? 'ITINERAIRE_READ' : 'TARIF_READ');
    final canCreate = _can(_tabs.index == 0 ? 'DESTINATION_CREATE' : _tabs.index == 1 ? 'ITINERAIRE_CREATE' : 'TARIF_CREATE');
    return Scaffold(
      appBar: AppBar(title: const Text('Reseau et tarifs'), actions: [IconButton(onPressed: _load, icon: const Icon(Icons.refresh))], bottom: TabBar(controller: _tabs, tabs: const [Tab(text: 'Destinations'), Tab(text: 'Itineraires'), Tab(text: 'Tarifs')])),
      floatingActionButton: canCreate ? FloatingActionButton.extended(onPressed: () => _showForm(), icon: const Icon(Icons.add), label: Text(_tabs.index == 0 ? 'Nouvelle destination' : _tabs.index == 1 ? 'Nouvel itineraire' : 'Nouveau tarif')) : null,
      body: SafeArea(child: Column(children: [Padding(padding: const EdgeInsets.fromLTRB(16, 16, 16, 8), child: TextField(controller: _search, onChanged: (_) => setState(() {}), decoration: const InputDecoration(labelText: 'Rechercher', prefixIcon: Icon(Icons.search))),), if (_error != null) Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: ErrorBanner(message: _error!)), Expanded(child: _loading ? const Center(child: CircularProgressIndicator()) : !canRead ? const Center(child: Text('Acces non autorise.')) : items.isEmpty ? const Center(child: Text('Aucun element enregistre.')) : ListView.builder(padding: const EdgeInsets.all(16), itemCount: items.length, itemBuilder: (context, index) { final item = items[index]; final label = _tabs.index == 0 ? item['nom'] as String? ?? '-' : _tabs.index == 1 ? _itineraryName(item) : '${item['prix'] ?? '-'} ${item['devise'] ?? ''}'; final subtitle = _tabs.index == 0 ? item['region'] as String? ?? 'Destination' : _tabs.index == 1 ? '${item['distance_km'] ?? '-'} km - ${item['duree_estimee_minutes'] ?? '-'} min' : item['id_cooperative'] == null ? 'Tarif general' : 'Tarif cooperative'; return Card(color: AppTheme.surface, child: ListTile(title: Text(label), subtitle: Text(subtitle), onTap: () => _details(item), trailing: PopupMenuButton<String>(onSelected: (value) { if (value == 'edit') _showForm(item); if (value == 'toggle') _toggle(item); if (value == 'delete') _delete(item); }, itemBuilder: (_) => [if (_can(_tabs.index == 0 ? 'DESTINATION_UPDATE' : _tabs.index == 1 ? 'ITINERAIRE_UPDATE' : 'TARIF_UPDATE')) const PopupMenuItem(value: 'edit', child: Text('Modifier')), if (_can(_tabs.index == 0 ? 'DESTINATION_UPDATE' : _tabs.index == 1 ? 'ITINERAIRE_UPDATE' : 'TARIF_UPDATE')) const PopupMenuItem(value: 'toggle', child: Text('Activer / desactiver')), if (_tabs.index < 2 && _can(_tabs.index == 0 ? 'DESTINATION_DELETE' : 'ITINERAIRE_DELETE')) const PopupMenuItem(value: 'delete', child: Text('Supprimer'))]))); })), if (!_loading) Padding(padding: const EdgeInsets.all(8), child: Text('Page $_page / $_pages - $_total resultat(s)')), if (!_loading && _pages > 1) Row(mainAxisAlignment: MainAxisAlignment.center, children: [TextButton(onPressed: _page > 1 ? () { setState(() => _page--); _load(); } : null, child: const Text('Precedent')), TextButton(onPressed: _page < _pages ? () { setState(() => _page++); _load(); } : null, child: const Text('Suivant'))])])));
  }
}
