import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/error_banner.dart';

class GaresPage extends StatefulWidget {
  final ApiClient apiClient;
  final Set<String> permissions;
  final bool isAdmin;

  const GaresPage({
    super.key,
    required this.apiClient,
    this.permissions = const {},
    this.isAdmin = false,
  });

  @override
  State<GaresPage> createState() => _GaresPageState();
}

class _GaresPageState extends State<GaresPage> {
  final _search = TextEditingController();
  List<Map<String, dynamic>> _gares = [];
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

  Future<void> _load({bool showLoading = true}) async {
    if (!mounted) return;
    setState(() {
      if (showLoading) _loading = true;
      _error = null;
    });
    try {
      final response = await widget.apiClient.get(
        '/gares',
        queryParameters: {
          'page': _page,
          'page_size': 20,
          'search': _search.text.trim().isEmpty ? null : _search.text.trim(),
          'sort_by': 'nom',
          'sort_order': 'asc',
        },
      );
      final data = response.data;
      if (!mounted) return;
      final result = _items(data);
      setState(() {
        _gares = result;
        _total = data is Map
            ? data['total'] as int? ?? result.length
            : result.length;
        _pages = data is Map ? data['pages'] as int? ?? 1 : 1;
        _loading = false;
      });
    } catch (exception) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = userError(
          exception,
          'Impossible de charger les gares.',
          'MOBILE_STATIONS_LOAD_ERROR',
        );
      });
    }
  }

  Future<void> _toggle(Map<String, dynamic> gare) async {
    try {
      await widget.apiClient.patch('/gares/${gare['id']}/toggle');
      await _load(showLoading: false);
    } catch (exception) {
      if (!mounted) return;
      setState(() => _error = userError(
            exception,
            'Impossible de modifier le statut.',
            'MOBILE_STATION_TOGGLE_ERROR',
          ));
    }
  }

  Future<void> _delete(Map<String, dynamic> gare) async {
    if (!await _confirm('Supprimer cette gare ?')) return;
    try {
      await widget.apiClient.delete('/gares/${gare['id']}');
      await _load(showLoading: false);
    } catch (exception) {
      if (!mounted) return;
      setState(() => _error = userError(
            exception,
            'Suppression impossible. Desactivez la gare si elle contient encore des donnees.',
            'MOBILE_STATION_DELETE_ERROR',
          ));
    }
  }

  Future<bool> _confirm(String message) async {
    return await showDialog<bool>(
          context: context,
          builder: (dialogContext) => AlertDialog(
            backgroundColor: AppTheme.surface,
            title: const Text('Confirmation'),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext, false),
                child: const Text('Annuler'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.pop(dialogContext, true),
                child: const Text('Confirmer'),
              ),
            ],
          ),
        ) ??
        false;
  }

  TextFormField _input(
    TextEditingController controller,
    String label, {
    bool required = false,
    int maxLines = 1,
    TextInputType? keyboardType,
  }) {
    return TextFormField(
      controller: controller,
      maxLines: maxLines,
      keyboardType: keyboardType,
      decoration: InputDecoration(labelText: label),
      validator: required
          ? (value) => value == null || value.trim().isEmpty
              ? '$label obligatoire'
              : null
          : null,
    );
  }

  double? _number(String value) =>
      value.trim().isEmpty ? null : double.tryParse(value.trim());

  Future<void> _form([Map<String, dynamic>? current]) async {
    final formKey = GlobalKey<FormState>();
    final fields = <String, TextEditingController>{
      'nom': TextEditingController(text: current?['nom'] as String? ?? ''),
      'adresse':
          TextEditingController(text: current?['adresse'] as String? ?? ''),
      'ville': TextEditingController(text: current?['ville'] as String? ?? ''),
      'region':
          TextEditingController(text: current?['region'] as String? ?? ''),
      'telephone':
          TextEditingController(text: current?['telephone'] as String? ?? ''),
      'email': TextEditingController(text: current?['email'] as String? ?? ''),
      'description':
          TextEditingController(text: current?['description'] as String? ?? ''),
      'latitude':
          TextEditingController(text: current?['latitude']?.toString() ?? ''),
      'longitude':
          TextEditingController(text: current?['longitude']?.toString() ?? ''),
    };
    bool submitting = false;
    String? formError;

    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (context, setDialogState) => AlertDialog(
            backgroundColor: AppTheme.surface,
            title: Text(current == null ? 'Nouvelle gare' : 'Modifier la gare'),
            content: SizedBox(
              width: 540,
              child: SingleChildScrollView(
                child: Form(
                  key: formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (formError != null) ErrorBanner(message: formError!),
                      _input(fields['nom']!, 'Nom', required: true),
                      _input(fields['adresse']!, 'Adresse', required: true),
                      _input(fields['ville']!, 'Ville', required: true),
                      _input(fields['region']!, 'Region'),
                      _input(fields['telephone']!, 'Telephone'),
                      _input(fields['email']!, 'Email',
                          keyboardType: TextInputType.emailAddress),
                      Row(
                        children: [
                          Expanded(
                            child: _input(
                              fields['latitude']!,
                              'Latitude',
                              keyboardType: TextInputType.number,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _input(
                              fields['longitude']!,
                              'Longitude',
                              keyboardType: TextInputType.number,
                            ),
                          ),
                        ],
                      ),
                      _input(fields['description']!, 'Description',
                          maxLines: 3),
                    ],
                  ),
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed:
                    submitting ? null : () => Navigator.pop(dialogContext),
                child: const Text('Annuler'),
              ),
              ElevatedButton(
                onPressed: submitting
                    ? null
                    : () async {
                        if (!(formKey.currentState?.validate() ?? false))
                          return;
                        final latitude = _number(fields['latitude']!.text);
                        final longitude = _number(fields['longitude']!.text);
                        if ((fields['latitude']!.text.trim().isNotEmpty &&
                                latitude == null) ||
                            (fields['longitude']!.text.trim().isNotEmpty &&
                                longitude == null)) {
                          setDialogState(
                              () => formError = 'Coordonnees GPS invalides.');
                          return;
                        }
                        setDialogState(() {
                          submitting = true;
                          formError = null;
                        });
                        try {
                          final payload = <String, dynamic>{
                            for (final entry in fields.entries)
                              if (entry.key != 'latitude' &&
                                  entry.key != 'longitude')
                                entry.key: entry.value.text.trim().isEmpty
                                    ? null
                                    : entry.value.text.trim(),
                            'latitude': latitude,
                            'longitude': longitude,
                          };
                          if (current == null) {
                            await widget.apiClient
                                .post('/gares', data: payload);
                          } else {
                            await widget.apiClient
                                .put('/gares/${current['id']}', data: payload);
                          }
                          if (dialogContext.mounted)
                            Navigator.pop(dialogContext);
                          await _load(showLoading: false);
                        } catch (exception) {
                          setDialogState(() {
                            submitting = false;
                            formError = userError(
                              exception,
                              'Enregistrement impossible.',
                              'MOBILE_STATION_SAVE_ERROR',
                            );
                          });
                        }
                      },
                child: submitting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Enregistrer'),
              ),
            ],
          ),
        ),
      );
    } finally {
      for (final controller in fields.values) {
        controller.dispose();
      }
    }
  }

  Future<void> _details(Map<String, dynamic> summary) async {
    try {
      final id = summary['id'] as int;
      final gare = Map<String, dynamic>.from(
        (await widget.apiClient.get('/gares/$id')).data as Map,
      );
      final quais =
          _items((await widget.apiClient.get('/gares/$id/quais')).data);
      final zones =
          _items((await widget.apiClient.get('/gares/$id/zones')).data);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: Text(gare['nom'] as String? ?? 'Detail de la gare'),
          content: SizedBox(
            width: 620,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _line('Adresse',
                      '${gare['adresse'] ?? '-'}, ${gare['ville'] ?? '-'}'),
                  _line('Region', gare['region'] as String? ?? '-'),
                  _line('Telephone', gare['telephone'] as String? ?? '-'),
                  _line('Email', gare['email'] as String? ?? '-'),
                  _line('Statut',
                      gare['is_active'] == true ? 'Active' : 'Inactive'),
                  const Divider(),
                  _sectionHeader('Quais', _can('GARE_UPDATE'), () async {
                    await _resourceForm(id, 'quai');
                    if (dialogContext.mounted) Navigator.pop(dialogContext);
                    _details(gare);
                  }),
                  if (quais.isEmpty) const Text('Aucun quai.'),
                  for (final quai in quais) _quaiTile(id, quai, dialogContext),
                  const Divider(),
                  _sectionHeader('Zones et emplacements', _can('GARE_UPDATE'),
                      () async {
                    await _resourceForm(id, 'zone');
                    if (dialogContext.mounted) Navigator.pop(dialogContext);
                    _details(gare);
                  }),
                  if (zones.isEmpty) const Text('Aucune zone.'),
                  for (final zone in zones) _zoneTile(id, zone, dialogContext),
                ],
              ),
            ),
          ),
          actions: [
            if (_can('GARE_UPDATE'))
              TextButton(
                onPressed: () {
                  Navigator.pop(dialogContext);
                  _form(gare);
                },
                child: const Text('Modifier'),
              ),
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Fermer'),
            ),
          ],
        ),
      );
    } catch (exception) {
      if (!mounted) return;
      setState(() => _error = userError(
            exception,
            'Impossible de charger le detail de la gare.',
            'MOBILE_STATION_DETAIL_ERROR',
          ));
    }
  }

  Widget _line(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(label, style: const TextStyle(color: Colors.white60)),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  Widget _sectionHeader(String title, bool canAdd, VoidCallback callback) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        if (canAdd)
          IconButton(onPressed: callback, icon: const Icon(Icons.add)),
      ],
    );
  }

  Widget _quaiTile(
      int gareId, Map<String, dynamic> quai, BuildContext dialogContext) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: Text('${quai['numero']} ${quai['nom'] ?? ''}'),
      subtitle: Text(quai['is_active'] == true ? 'Actif' : 'Inactif'),
      trailing: _can('GARE_UPDATE')
          ? IconButton(
              icon: Icon(quai['is_active'] == true
                  ? Icons.toggle_on
                  : Icons.toggle_off),
              onPressed: () async {
                await widget.apiClient
                    .patch('/gares/$gareId/quais/${quai['id']}/toggle');
                if (dialogContext.mounted) Navigator.pop(dialogContext);
                _details({'id': gareId});
              },
            )
          : null,
    );
  }

  Widget _zoneTile(
      int gareId, Map<String, dynamic> zone, BuildContext dialogContext) {
    final emplacements = _items(zone['emplacements']);
    return Card(
      color: AppTheme.surfaceCard,
      child: ExpansionTile(
        title: Text(zone['nom'] as String? ?? '-'),
        subtitle: Text(
            '${zone['type_zone'] ?? 'Zone'} - ${zone['is_active'] == true ? 'Active' : 'Inactive'}'),
        children: [
          if (emplacements.isEmpty)
            const ListTile(title: Text('Aucun emplacement.')),
          for (final emplacement in emplacements)
            ListTile(
              title: Text('${emplacement['code']} ${emplacement['nom'] ?? ''}'),
              subtitle: Text(emplacement['is_available'] == true
                  ? 'Disponible'
                  : 'Indisponible'),
              trailing: _can('GARE_UPDATE')
                  ? IconButton(
                      icon: Icon(emplacement['is_active'] == true
                          ? Icons.toggle_on
                          : Icons.toggle_off),
                      onPressed: () async {
                        await widget.apiClient.patch(
                            '/gares/$gareId/zones/${zone['id']}/emplacements/${emplacement['id']}/toggle');
                        if (dialogContext.mounted) Navigator.pop(dialogContext);
                        _details({'id': gareId});
                      },
                    )
                  : null,
            ),
          if (_can('GARE_UPDATE'))
            ListTile(
              leading: const Icon(Icons.add),
              title: const Text('Ajouter un emplacement'),
              onTap: () async {
                await _resourceForm(zone['id'] as int, 'emplacement');
                if (dialogContext.mounted) Navigator.pop(dialogContext);
                _details({'id': gareId});
              },
            ),
        ],
      ),
    );
  }

  Future<void> _resourceForm(int id, String type) async {
    final names = type == 'quai'
        ? ['numero', 'nom', 'description']
        : type == 'zone'
            ? ['nom', 'type_zone', 'description']
            : ['code', 'nom', 'type_emplacement', 'description'];
    final controllers = <String, TextEditingController>{
      for (final name in names) name: TextEditingController(),
    };
    final formKey = GlobalKey<FormState>();
    bool submitting = false;
    String? formError;

    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (context, setDialogState) => AlertDialog(
            backgroundColor: AppTheme.surface,
            title: Text('Nouveau $type'),
            content: Form(
              key: formKey,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (formError != null) ErrorBanner(message: formError!),
                    for (final name in names)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: TextFormField(
                          controller: controllers[name],
                          maxLines: name == 'description' ? 3 : 1,
                          decoration: InputDecoration(labelText: name),
                          validator: name == names.first
                              ? (value) => value == null || value.trim().isEmpty
                                  ? 'Champ obligatoire'
                                  : null
                              : null,
                        ),
                      ),
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed:
                    submitting ? null : () => Navigator.pop(dialogContext),
                child: const Text('Annuler'),
              ),
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
                          final payload = <String, dynamic>{
                            for (final entry in controllers.entries)
                              entry.key: entry.value.text.trim().isEmpty
                                  ? null
                                  : entry.value.text.trim(),
                          };
                          final path = type == 'quai'
                              ? '/gares/$id/quais'
                              : type == 'zone'
                                  ? '/gares/$id/zones'
                                  : '/gares/zones/$id/emplacements';
                          await widget.apiClient.post(path, data: payload);
                          if (dialogContext.mounted)
                            Navigator.pop(dialogContext);
                        } catch (exception) {
                          setDialogState(() {
                            submitting = false;
                            formError = userError(
                              exception,
                              'Impossible d enregistrer la ressource.',
                              'MOBILE_STATION_RESOURCE_ERROR',
                            );
                          });
                        }
                      },
                child: submitting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Enregistrer'),
              ),
            ],
          ),
        ),
      );
    } finally {
      for (final controller in controllers.values) {
        controller.dispose();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final canCreate = _can('GARE_CREATE');
    final canUpdate = _can('GARE_UPDATE');
    final canDelete = _can('GARE_DELETE');
    return Scaffold(
      appBar: AppBar(
        title: Text('Gares ($_total)'),
        actions: [
          IconButton(onPressed: _load, icon: const Icon(Icons.refresh))
        ],
      ),
      floatingActionButton: canCreate
          ? FloatingActionButton.extended(
              onPressed: () => _form(),
              icon: const Icon(Icons.add),
              label: const Text('Nouvelle gare'),
            )
          : null,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: _search,
                onSubmitted: (_) {
                  _page = 1;
                  _load();
                },
                decoration: InputDecoration(
                  labelText: 'Rechercher',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: IconButton(
                    onPressed: () {
                      _search.clear();
                      _page = 1;
                      _load();
                    },
                    icon: const Icon(Icons.clear),
                  ),
                ),
              ),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: ErrorBanner(message: _error!),
              ),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _gares.isEmpty
                      ? const Center(child: Text('Aucune gare enregistree.'))
                      : RefreshIndicator(
                          onRefresh: _load,
                          child: ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _gares.length,
                            itemBuilder: (context, index) {
                              final gare = _gares[index];
                              return Card(
                                color: AppTheme.surface,
                                child: ListTile(
                                  onTap: () => _details(gare),
                                  leading: CircleAvatar(
                                    child: Icon(gare['is_active'] == true
                                        ? Icons.location_city
                                        : Icons.location_off),
                                  ),
                                  title: Text(gare['nom'] as String? ?? '-'),
                                  subtitle: Text(
                                      '${gare['ville'] ?? '-'} - ${gare['adresse'] ?? '-'}'),
                                  trailing: PopupMenuButton<String>(
                                    onSelected: (value) {
                                      if (value == 'toggle' && canUpdate)
                                        _toggle(gare);
                                      if (value == 'edit' && canUpdate)
                                        _form(gare);
                                      if (value == 'delete' && canDelete)
                                        _delete(gare);
                                    },
                                    itemBuilder: (_) => [
                                      const PopupMenuItem(
                                          value: 'details',
                                          child: Text('Details')),
                                      if (canUpdate)
                                        PopupMenuItem(
                                          value: 'toggle',
                                          child: Text(gare['is_active'] == true
                                              ? 'Desactiver'
                                              : 'Activer'),
                                        ),
                                      if (canUpdate)
                                        const PopupMenuItem(
                                            value: 'edit',
                                            child: Text('Modifier')),
                                      if (canDelete)
                                        const PopupMenuItem(
                                            value: 'delete',
                                            child: Text('Supprimer')),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
            ),
            if (!_loading && _pages > 1)
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton(
                    onPressed: _page > 1
                        ? () {
                            setState(() => _page--);
                            _load();
                          }
                        : null,
                    icon: const Icon(Icons.chevron_left),
                  ),
                  Text('Page $_page / $_pages'),
                  IconButton(
                    onPressed: _page < _pages
                        ? () {
                            setState(() => _page++);
                            _load();
                          }
                        : null,
                    icon: const Icon(Icons.chevron_right),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}
