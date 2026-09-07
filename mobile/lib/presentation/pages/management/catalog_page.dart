import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/error_banner.dart';

class CatalogPage extends StatefulWidget {
  final ApiClient apiClient;
  final Set<String> permissions;
  final bool isAdmin;

  const CatalogPage({
    super.key,
    required this.apiClient,
    this.permissions = const {},
    this.isAdmin = false,
  });

  @override
  State<CatalogPage> createState() => _CatalogPageState();
}

class _CatalogPageState extends State<CatalogPage> {
  final _searchController = TextEditingController();
  int _tab = 0;
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _marques = [];
  List<Map<String, dynamic>> _modeles = [];

  bool get _canRead =>
      widget.isAdmin || widget.permissions.contains('VEHICULE_READ');
  bool get _canWrite =>
      widget.isAdmin || widget.permissions.contains('VEHICULE_CREATE');
  bool get _canUpdate =>
      widget.isAdmin || widget.permissions.contains('VEHICULE_UPDATE');
  bool get _canDelete =>
      widget.isAdmin || widget.permissions.contains('VEHICULE_DELETE');

  List<Map<String, dynamic>> _items(dynamic data) {
    if (data is Map && data['items'] is List) {
      return (data['items'] as List)
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    }
    return data is List
        ? data
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList()
        : [];
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (!mounted) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final responses = await Future.wait([
        widget.apiClient.get('/marques', queryParameters: {
          'page': 1,
          'page_size': 100,
          'sort_by': 'nom',
          'sort_order': 'asc'
        }),
        widget.apiClient.get('/modeles', queryParameters: {
          'page': 1,
          'page_size': 100,
          'sort_by': 'nom',
          'sort_order': 'asc'
        }),
      ]);
      if (!mounted) return;
      setState(() {
        _marques = _items(responses[0].data);
        _modeles = _items(responses[1].data);
        _loading = false;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = userError(error, 'Impossible de charger le catalogue.',
              'MOBILE_CATALOG_LOAD_ERROR');
        });
      }
    }
  }

  List<Map<String, dynamic>> get _visibleItems {
    final query = _searchController.text.trim().toLowerCase();
    final values = _tab == 0 ? _marques : _modeles;
    if (query.isEmpty) return values;
    return values.where((item) {
      final name = '${item['nom'] ?? ''}'.toLowerCase();
      if (_tab == 0) return name.contains(query);
      final brand = _brandName(item['id_marque'] as int?);
      return name.contains(query) || brand.toLowerCase().contains(query);
    }).toList();
  }

  String _brandName(int? id) {
    for (final item in _marques) {
      if (item['id'] == id) return item['nom'] as String? ?? 'Marque #$id';
    }
    return id == null ? 'Marque non définie' : 'Marque #$id';
  }

  Future<void> _toggle(Map<String, dynamic> item) async {
    try {
      final endpoint = _tab == 0 ? 'marques' : 'modeles';
      await widget.apiClient.patch('/$endpoint/${item['id']}/toggle');
      await _load();
    } catch (error) {
      if (mounted)
        setState(() => _error = userError(
            error,
            'Impossible de modifier le statut.',
            'MOBILE_CATALOG_TOGGLE_ERROR'));
    }
  }

  Future<void> _delete(Map<String, dynamic> item) async {
    final confirmed = await showDialog<bool>(
          context: context,
          builder: (dialogContext) => AlertDialog(
            backgroundColor: AppTheme.surface,
            title: const Text('Confirmation'),
            content: Text('Supprimer ${item['nom'] ?? 'cet élément'} ?'),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(dialogContext, false),
                  child: const Text('Annuler')),
              ElevatedButton(
                  onPressed: () => Navigator.pop(dialogContext, true),
                  child: const Text('Supprimer')),
            ],
          ),
        ) ??
        false;
    if (!confirmed) return;
    try {
      final endpoint = _tab == 0 ? 'marques' : 'modeles';
      await widget.apiClient.delete('/$endpoint/${item['id']}');
      await _load();
    } catch (error) {
      if (mounted)
        setState(() => _error = userError(
            error,
            'Suppression impossible. Vérifiez les dépendances.',
            'MOBILE_CATALOG_DELETE_ERROR'));
    }
  }

  Future<void> _showForm([Map<String, dynamic>? current]) async {
    final formKey = GlobalKey<FormState>();
    final name = TextEditingController(text: current?['nom'] as String? ?? '');
    final description =
        TextEditingController(text: current?['description'] as String? ?? '');
    int? brandId = current?['id_marque'] as int?;
    bool submitting = false;
    String? formError;
    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (context, setDialogState) => AlertDialog(
            backgroundColor: AppTheme.surface,
            title: Text(current == null
                ? (_tab == 0 ? 'Nouvelle marque' : 'Nouveau modèle')
                : (_tab == 0 ? 'Modifier la marque' : 'Modifier le modèle')),
            content: SizedBox(
              width: 480,
              child: Form(
                key: formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (formError != null) ErrorBanner(message: formError!),
                    TextFormField(
                      controller: name,
                      decoration: InputDecoration(
                          labelText:
                              _tab == 0 ? 'Nom de la marque' : 'Nom du modèle'),
                      validator: (value) =>
                          value == null || value.trim().isEmpty
                              ? 'Nom obligatoire'
                              : null,
                    ),
                    if (_tab == 1) ...[
                      const SizedBox(height: 12),
                      DropdownButtonFormField<int>(
                        initialValue: brandId,
                        decoration: const InputDecoration(labelText: 'Marque'),
                        items: _marques
                            .map((item) => DropdownMenuItem<int>(
                                value: item['id'] as int,
                                child: Text(item['nom'] as String? ?? '')))
                            .toList(),
                        onChanged: current != null || submitting
                            ? null
                            : (value) => setDialogState(() => brandId = value),
                        validator: (value) =>
                            value == null ? 'Marque obligatoire' : null,
                      ),
                    ],
                    const SizedBox(height: 12),
                    TextFormField(
                        controller: description,
                        maxLines: 3,
                        decoration: const InputDecoration(
                            labelText: 'Description (optionnelle)')),
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                  onPressed:
                      submitting ? null : () => Navigator.pop(dialogContext),
                  child: const Text('Annuler')),
              ElevatedButton(
                onPressed: submitting
                    ? null
                    : () async {
                        if (!(formKey.currentState?.validate() ?? false))
                          return;
                        setDialogState(() {
                          submitting = true;
                          formError = null;
                        });
                        try {
                          final payload = {
                            'nom': name.text.trim(),
                            'description': description.text.trim().isEmpty
                                ? null
                                : description.text.trim(),
                            if (_tab == 1) 'id_marque': brandId,
                          };
                          final endpoint = _tab == 0 ? 'marques' : 'modeles';
                          if (current == null) {
                            await widget.apiClient
                                .post('/$endpoint', data: payload);
                          } else {
                            await widget.apiClient.put(
                                '/$endpoint/${current['id']}',
                                data: payload);
                          }
                          if (dialogContext.mounted)
                            Navigator.pop(dialogContext);
                          await _load();
                        } catch (error) {
                          setDialogState(() {
                            submitting = false;
                            formError = userError(
                                error,
                                'Enregistrement impossible.',
                                'MOBILE_CATALOG_SAVE_ERROR');
                          });
                        }
                      },
                child: submitting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Enregistrer'),
              ),
            ],
          ),
        ),
      );
    } finally {
      name.dispose();
      description.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    final values = _visibleItems;
    return Scaffold(
      appBar: AppBar(title: const Text('Marques et modèles'), actions: [
        IconButton(onPressed: _load, icon: const Icon(Icons.refresh))
      ]),
      floatingActionButton: _canWrite
          ? FloatingActionButton.extended(
              onPressed: () => _showForm(),
              icon: const Icon(Icons.add),
              label: Text(_tab == 0 ? 'Nouvelle marque' : 'Nouveau modèle'))
          : null,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: TextField(
                controller: _searchController,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                    labelText: 'Rechercher',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: IconButton(
                        onPressed: () {
                          _searchController.clear();
                          setState(() {});
                        },
                        icon: const Icon(Icons.clear))),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: SegmentedButton<int>(
                  segments: const [
                    ButtonSegment(value: 0, label: Text('Marques')),
                    ButtonSegment(value: 1, label: Text('Modèles'))
                  ],
                  selected: {
                    _tab
                  },
                  onSelectionChanged: (selection) =>
                      setState(() => _tab = selection.first)),
            ),
            if (_error != null)
              Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: ErrorBanner(message: _error!)),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : !_canRead
                      ? const Center(
                          child: Text('Vous n’avez pas accès au catalogue.'))
                      : values.isEmpty
                          ? Center(
                              child: Text(_tab == 0
                                  ? 'Aucune marque enregistrée.'
                                  : 'Aucun modèle enregistré.'))
                          : ListView.builder(
                              padding: const EdgeInsets.all(16),
                              itemCount: values.length,
                              itemBuilder: (context, index) {
                                final item = values[index];
                                return Card(
                                  color: AppTheme.surface,
                                  child: ListTile(
                                    leading: CircleAvatar(
                                        child: Icon(_tab == 0
                                            ? Icons.branding_watermark
                                            : Icons.directions_car)),
                                    title: Text(item['nom'] as String? ?? '-'),
                                    subtitle: Text(_tab == 0
                                        ? (item['description'] as String? ??
                                            'Marque')
                                        : 'Marque : ${_brandName(item['id_marque'] as int?)}'),
                                    trailing: PopupMenuButton<String>(
                                      onSelected: (value) {
                                        if (value == 'toggle' && _canUpdate)
                                          _toggle(item);
                                        if (value == 'edit' && _canUpdate)
                                          _showForm(item);
                                        if (value == 'delete' && _canDelete)
                                          _delete(item);
                                      },
                                      itemBuilder: (_) => [
                                        if (_canUpdate)
                                          PopupMenuItem(
                                              value: 'toggle',
                                              child: Text(
                                                  item['is_active'] == true
                                                      ? 'Désactiver'
                                                      : 'Activer')),
                                        if (_canUpdate)
                                          const PopupMenuItem(
                                              value: 'edit',
                                              child: Text('Modifier')),
                                        if (_canDelete)
                                          const PopupMenuItem(
                                              value: 'delete',
                                              child: Text('Supprimer'))
                                      ],
                                    ),
                                  ),
                                );
                              },
                            ),
            ),
          ],
        ),
      ),
    );
  }
}
