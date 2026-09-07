import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/error_banner.dart';

class ChauffeursPage extends StatefulWidget {
  final ApiClient apiClient;
  final Set<String> permissions;
  final bool isAdmin;

  const ChauffeursPage({
    super.key,
    required this.apiClient,
    this.permissions = const {},
    this.isAdmin = false,
  });

  @override
  State<ChauffeursPage> createState() => _ChauffeursPageState();
}

class _ChauffeursPageState extends State<ChauffeursPage> {
  List<Map<String, dynamic>> _chauffeurs = [];
  List<Map<String, dynamic>> _cooperatives = [];
  bool _isLoading = true;
  String? _error;
  int _page = 1;
  int _pages = 1;
  int _total = 0;
  final _searchController = TextEditingController();

  bool _can(String permission) =>
      widget.isAdmin || widget.permissions.contains(permission);

  List<Map<String, dynamic>> _items(dynamic data) {
    if (data is Map && data['items'] is List) {
      return (data['items'] as List)
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    }
    if (data is List)
      return data
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    return [];
  }

  Map<String, dynamic>? _findById(
      List<Map<String, dynamic>> values, dynamic id) {
    for (final value in values) {
      if (value['id'] == id) return value;
    }
    return null;
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

  Future<void> _load({bool showLoading = true}) async {
    if (!mounted) return;
    setState(() {
      if (showLoading) _isLoading = true;
      _error = null;
    });
    try {
      final requests = <Future<dynamic>>[
        widget.apiClient.get('/chauffeurs', queryParameters: {
          'page': _page,
          'page_size': 20,
          'search': _searchController.text.trim().isEmpty
              ? null
              : _searchController.text.trim(),
          'sort_by': 'created_at',
          'sort_order': 'desc'
        }),
      ];
      if (_can('COOPERATIVE_READ'))
        requests.add(widget.apiClient.get('/cooperatives', queryParameters: {
          'page': 1,
          'page_size': 100,
          'sort_by': 'nom',
          'sort_order': 'asc'
        }));
      final responses = await Future.wait(requests);
      final payload = responses.first.data;
      if (!mounted) return;
      setState(() {
        _chauffeurs = _items(payload);
        _total = payload is Map
            ? (payload['total'] as int? ?? _chauffeurs.length)
            : _chauffeurs.length;
        _pages = payload is Map ? (payload['pages'] as int? ?? 1) : 1;
        _cooperatives = responses.length > 1 ? _items(responses[1].data) : [];
        _isLoading = false;
      });
    } catch (error) {
      if (mounted)
        setState(() {
          _error = userError(error, 'Impossible de charger les chauffeurs.',
              'MOBILE_DRIVERS_LOAD_ERROR');
          _isLoading = false;
        });
    }
  }

  String _cooperativeLabel(int? id) {
    final value = _findById(_cooperatives, id);
    return value?['nom'] as String? ??
        (id == null ? 'Cooperative non definie' : 'Cooperative #$id');
  }

  Future<List<Map<String, dynamic>>> _eligibleUsers(int cooperativeId) async {
    final response = await widget.apiClient
        .get('/cooperatives/$cooperativeId/eligible-chauffeur-users');
    return _items(response.data);
  }

  Future<void> _toggle(Map<String, dynamic> item) async {
    try {
      await widget.apiClient.patch('/chauffeurs/${item['id']}/toggle');
      await _load(showLoading: false);
    } catch (error) {
      if (mounted)
        setState(() => _error = userError(error,
            'Impossible de modifier le statut.', 'MOBILE_DRIVER_TOGGLE_ERROR'));
    }
  }

  Future<void> _delete(Map<String, dynamic> item) async {
    if (!await _confirm('Supprimer ce chauffeur ?')) return;
    try {
      await widget.apiClient.delete('/chauffeurs/${item['id']}');
      await _load(showLoading: false);
    } catch (error) {
      if (mounted)
        setState(() => _error = userError(
            error,
            'Impossible de supprimer le chauffeur.',
            'MOBILE_DRIVER_DELETE_ERROR'));
    }
  }

  Future<bool> _confirm(String message) async =>
      await showDialog<bool>(
          context: context,
          builder: (dialogContext) => AlertDialog(
                  backgroundColor: AppTheme.surface,
                  title: const Text('Confirmation'),
                  content: Text(message),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(dialogContext, false),
                        child: const Text('Annuler')),
                    ElevatedButton(
                        onPressed: () => Navigator.pop(dialogContext, true),
                        child: const Text('Confirmer'))
                  ])) ??
      false;

  Future<void> _showForm([Map<String, dynamic>? current]) async {
    if (_cooperatives.isEmpty) {
      setState(
          () => _error = 'Aucune cooperative disponible pour ce chauffeur.');
      return;
    }
    final formKey = GlobalKey<FormState>();
    final permit =
        TextEditingController(text: current?['numero_permis'] as String? ?? '');
    final category = TextEditingController(
        text: current?['categorie_permis'] as String? ?? 'B');
    final expiration = TextEditingController(
        text: current?['date_expiration_permis'] as String? ?? '');
    int? cooperativeId =
        current?['id_cooperative'] as int? ?? _cooperatives.first['id'] as int;
    int? userId = current?['id_user'] as int?;
    List<Map<String, dynamic>> users = [];
    bool available = current?['disponibilite'] as bool? ?? true;
    bool submitting = false;
    String? formError;
    try {
      users = await _eligibleUsers(cooperativeId);
      if (!mounted) return;
      final currentUser = current?['user'];
      if (userId != null &&
          currentUser is Map &&
          !users.any((item) => item['id'] == userId))
        users.insert(0, Map<String, dynamic>.from(currentUser));
      await showDialog<void>(
          context: context,
          builder: (dialogContext) => StatefulBuilder(
              builder: (context, setDialogState) => AlertDialog(
                      backgroundColor: AppTheme.surface,
                      title: Text(current == null
                          ? 'Nouveau chauffeur'
                          : 'Modifier le chauffeur'),
                      content: SizedBox(
                          width: 520,
                          child: SingleChildScrollView(
                              child: Form(
                                  key: formKey,
                                  child: Column(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        if (formError != null)
                                          ErrorBanner(message: formError!),
                                        DropdownButtonFormField<int>(
                                            initialValue: cooperativeId,
                                            decoration: const InputDecoration(
                                                labelText: 'Cooperative'),
                                            items: _cooperatives
                                                .map((item) => DropdownMenuItem(
                                                    value: item['id'] as int,
                                                    child: Text(item['nom']
                                                            as String? ??
                                                        '')))
                                                .toList(),
                                            onChanged: current != null ||
                                                    submitting
                                                ? null
                                                : (value) async {
                                                    if (value == null) return;
                                                    setDialogState(() {
                                                      cooperativeId = value;
                                                      userId = null;
                                                      users = [];
                                                    });
                                                    try {
                                                      final result =
                                                          await _eligibleUsers(
                                                              value);
                                                      setDialogState(
                                                          () => users = result);
                                                    } catch (error) {
                                                      setDialogState(() =>
                                                          formError = userError(
                                                              error,
                                                              'Impossible de charger les utilisateurs.',
                                                              'MOBILE_DRIVER_USERS_ERROR'));
                                                    }
                                                  },
                                            validator: (value) => value == null
                                                ? 'Cooperative requise'
                                                : null),
                                        const SizedBox(height: 12),
                                        DropdownButtonFormField<int>(
                                            initialValue: userId,
                                            decoration: const InputDecoration(
                                                labelText: 'Utilisateur'),
                                            items: users
                                                .map((item) => DropdownMenuItem(
                                                    value: item['id'] as int,
                                                    child: Text(
                                                        '${item['first_name'] ?? ''} ${item['name'] ?? ''}'
                                                            .trim())))
                                                .toList(),
                                            onChanged: submitting
                                                ? null
                                                : (value) => setDialogState(
                                                    () => userId = value),
                                            validator: (value) => value == null
                                                ? 'Utilisateur requis'
                                                : null),
                                        const SizedBox(height: 12),
                                        TextFormField(
                                            controller: permit,
                                            decoration: const InputDecoration(
                                                labelText: 'Numero de permis'),
                                            validator: (value) =>
                                                value == null ||
                                                        value.trim().length < 2
                                                    ? 'Numero requis'
                                                    : null),
                                        const SizedBox(height: 12),
                                        TextFormField(
                                            controller: category,
                                            decoration: const InputDecoration(
                                                labelText:
                                                    'Categorie du permis'),
                                            validator: (value) =>
                                                value == null ||
                                                        value.trim().isEmpty
                                                    ? 'Categorie requise'
                                                    : null),
                                        const SizedBox(height: 12),
                                        TextFormField(
                                            controller: expiration,
                                            decoration: const InputDecoration(
                                                labelText:
                                                    'Expiration (AAAA-MM-JJ)'),
                                            validator: (value) =>
                                                value == null ||
                                                        DateTime.tryParse(
                                                                value.trim()) ==
                                                            null
                                                    ? 'Date invalide'
                                                    : null),
                                        SwitchListTile(
                                            title: const Text('Disponible'),
                                            value: available,
                                            onChanged: submitting
                                                ? null
                                                : (value) => setDialogState(
                                                    () => available = value),
                                            contentPadding: EdgeInsets.zero),
                                      ])))),
                      actions: [
                        TextButton(
                            onPressed: submitting
                                ? null
                                : () => Navigator.pop(dialogContext),
                            child: const Text('Annuler')),
                        ElevatedButton(
                            onPressed: submitting
                                ? null
                                : () async {
                                    if (!(formKey.currentState?.validate() ??
                                        false)) return;
                                    setDialogState(() {
                                      submitting = true;
                                      formError = null;
                                    });
                                    try {
                                      final payload = {
                                        'id_user': userId,
                                        'id_cooperative': cooperativeId,
                                        'numero_permis': permit.text.trim(),
                                        'categorie_permis':
                                            category.text.trim(),
                                        'date_expiration_permis':
                                            expiration.text.trim(),
                                        'disponibilite': available
                                      };
                                      if (current == null) {
                                        await widget.apiClient
                                            .post('/chauffeurs', data: payload);
                                      } else {
                                        payload.remove('id_user');
                                        await widget.apiClient.put(
                                            '/chauffeurs/${current['id']}',
                                            data: payload);
                                      }
                                      if (dialogContext.mounted)
                                        Navigator.pop(dialogContext);
                                      await _load(showLoading: false);
                                    } catch (error) {
                                      setDialogState(() {
                                        submitting = false;
                                        formError = userError(
                                            error,
                                            'Enregistrement impossible.',
                                            'MOBILE_DRIVER_SAVE_ERROR');
                                      });
                                    }
                                  },
                            child: submitting
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2))
                                : const Text('Enregistrer'))
                      ])));
    } finally {
      permit.dispose();
      category.dispose();
      expiration.dispose();
    }
  }

  Future<void> _showDetails(Map<String, dynamic> item) async {
    List<Map<String, dynamic>> assignments = [];
    try {
      assignments = _items(
          (await widget.apiClient.get('/chauffeurs/${item['id']}/vehicules'))
              .data);
    } catch (_) {}
    if (!mounted) return;
    await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
                backgroundColor: AppTheme.surface,
                title: Text(
                    '${item['user']?['first_name'] ?? ''} ${item['user']?['name'] ?? ''}'
                        .trim()),
                content: SizedBox(
                    width: 540,
                    child: SingleChildScrollView(
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                          Text('Permis : ${item['numero_permis'] ?? '-'}'),
                          Text(
                              'Categorie : ${item['categorie_permis'] ?? '-'}'),
                          Text(
                              'Expiration : ${item['date_expiration_permis'] ?? '-'}'),
                          Text(
                              'Cooperative : ${item['cooperative']?['nom'] ?? _cooperativeLabel(item['id_cooperative'] as int?)}'),
                          const Divider(),
                          const Text('Affectations',
                              style: TextStyle(
                                  fontWeight: FontWeight.bold, fontSize: 18)),
                          if (assignments.isEmpty)
                            const Text('Aucune affectation.'),
                          ...assignments.map((assignment) => ListTile(
                              contentPadding: EdgeInsets.zero,
                              title: Text(
                                  'Vehicule #${assignment['id_vehicule']}'),
                              subtitle: Text(
                                  '${assignment['date_debut']} -> ${assignment['date_fin'] ?? 'en cours'}'),
                              trailing: assignment['is_active'] == true
                                  ? const Chip(label: Text('Active'))
                                  : null)),
                        ]))),
                actions: [
                  if (_can('CHAUFFEUR_UPDATE'))
                    TextButton(
                        onPressed: () {
                          Navigator.pop(dialogContext);
                          _showAssignmentForm(item);
                        },
                        child: const Text('Affecter')),
                  TextButton(
                      onPressed: () => Navigator.pop(dialogContext),
                      child: const Text('Fermer'))
                ]));
  }

  Future<void> _showAssignmentForm(Map<String, dynamic> driver) async {
    final vehicleResponse =
        await widget.apiClient.get('/vehicules', queryParameters: {
      'page': 1,
      'page_size': 100,
      'id_cooperative': driver['id_cooperative'],
      'sort_by': 'immatriculation',
      'sort_order': 'asc'
    });
    final vehicles = _items(vehicleResponse.data);
    if (!mounted) return;
    int? vehicleId;
    final start = TextEditingController(
        text: DateTime.now().toIso8601String().substring(0, 10));
    final end = TextEditingController();
    bool submitting = false;
    String? formError;
    try {
      await showDialog<void>(
          context: context,
          builder: (dialogContext) => StatefulBuilder(
              builder: (context, setDialogState) => AlertDialog(
                      backgroundColor: AppTheme.surface,
                      title: const Text('Affecter un vehicule'),
                      content: SizedBox(
                          width: 480,
                          child:
                              Column(mainAxisSize: MainAxisSize.min, children: [
                            if (formError != null)
                              ErrorBanner(message: formError!),
                            DropdownButtonFormField<int>(
                                initialValue: vehicleId,
                                decoration: const InputDecoration(
                                    labelText: 'Vehicule'),
                                items: vehicles
                                    .map((item) => DropdownMenuItem(
                                        value: item['id'] as int,
                                        child: Text(
                                            '${item['immatriculation']} - ${item['etat']}')))
                                    .toList(),
                                onChanged: submitting
                                    ? null
                                    : (value) => setDialogState(
                                        () => vehicleId = value)),
                            const SizedBox(height: 12),
                            TextField(
                                controller: start,
                                decoration: const InputDecoration(
                                    labelText: 'Date de debut (AAAA-MM-JJ)')),
                            const SizedBox(height: 12),
                            TextField(
                                controller: end,
                                decoration: const InputDecoration(
                                    labelText: 'Date de fin (optionnelle)'))
                          ])),
                      actions: [
                        TextButton(
                            onPressed: submitting
                                ? null
                                : () => Navigator.pop(dialogContext),
                            child: const Text('Annuler')),
                        ElevatedButton(
                            onPressed: submitting
                                ? null
                                : () async {
                                    if (vehicleId == null ||
                                        DateTime.tryParse(start.text.trim()) ==
                                            null) {
                                      setDialogState(() => formError =
                                          'Vehicule et date de debut obligatoires.');
                                      return;
                                    }
                                    setDialogState(() => submitting = true);
                                    try {
                                      await widget.apiClient.post(
                                          '/chauffeurs/${driver['id']}/assign-vehicule',
                                          data: {
                                            'id_vehicule': vehicleId,
                                            'date_debut': start.text.trim(),
                                            'date_fin': end.text.trim().isEmpty
                                                ? null
                                                : end.text.trim()
                                          });
                                      if (dialogContext.mounted)
                                        Navigator.pop(dialogContext);
                                    } catch (error) {
                                      setDialogState(() {
                                        submitting = false;
                                        formError = userError(
                                            error,
                                            'Affectation impossible.',
                                            'MOBILE_ASSIGNMENT_ERROR');
                                      });
                                    }
                                  },
                            child: submitting
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2))
                                : const Text('Affecter'))
                      ])));
    } finally {
      start.dispose();
      end.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    final canCreate = _can('CHAUFFEUR_CREATE');
    final canUpdate = _can('CHAUFFEUR_UPDATE');
    final canDelete = _can('CHAUFFEUR_DELETE');
    return Scaffold(
        appBar: AppBar(title: Text('Chauffeurs ($_total)'), actions: [
          IconButton(onPressed: _load, icon: const Icon(Icons.refresh))
        ]),
        floatingActionButton: canCreate
            ? FloatingActionButton.extended(
                onPressed: () => _showForm(),
                icon: const Icon(Icons.add),
                label: const Text('Nouveau'))
            : null,
        body: SafeArea(
            child: Column(children: [
          Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                  controller: _searchController,
                  onSubmitted: (_) {
                    _page = 1;
                    _load();
                  },
                  decoration: InputDecoration(
                      labelText: 'Rechercher',
                      prefixIcon: const Icon(Icons.search),
                      suffixIcon: IconButton(
                          onPressed: () {
                            _searchController.clear();
                            _page = 1;
                            _load();
                          },
                          icon: const Icon(Icons.clear))))),
          if (_error != null)
            Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: ErrorBanner(message: _error!)),
          Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _chauffeurs.isEmpty
                      ? const Center(child: Text('Aucun chauffeur enregistre.'))
                      : RefreshIndicator(
                          onRefresh: _load,
                          child: ListView.builder(
                              padding: const EdgeInsets.all(16),
                              itemCount: _chauffeurs.length,
                              itemBuilder: (context, index) {
                                final item = _chauffeurs[index];
                                final user = item['user'] is Map
                                    ? item['user'] as Map
                                    : null;
                                return Card(
                                    color: AppTheme.surface,
                                    child: ListTile(
                                        onTap: () => _showDetails(item),
                                        leading: const CircleAvatar(
                                            child: Icon(Icons.badge)),
                                        title: Text(
                                            '${user?['first_name'] ?? ''} ${user?['name'] ?? ''}'
                                                    .trim()
                                                    .isEmpty
                                                ? 'Utilisateur #${item['id_user']}'
                                                : '${user?['first_name'] ?? ''} ${user?['name'] ?? ''}'
                                                    .trim()),
                                        subtitle: Text(
                                            'Permis ${item['numero_permis'] ?? '-'} - Exp. ${item['date_expiration_permis'] ?? '-'}\n${_cooperativeLabel(item['id_cooperative'] as int?)}'),
                                        isThreeLine: true,
                                        trailing: PopupMenuButton<String>(
                                            onSelected: (value) {
                                              if (value == 'toggle')
                                                _toggle(item);
                                              if (value == 'edit')
                                                _showForm(item);
                                              if (value == 'delete')
                                                _delete(item);
                                            },
                                            itemBuilder: (_) => [
                                                  const PopupMenuItem(
                                                      value: 'details',
                                                      child: Text('Details')),
                                                  if (canUpdate)
                                                    PopupMenuItem(
                                                        value: 'toggle',
                                                        child: Text(
                                                            item['is_active'] ==
                                                                    true
                                                                ? 'Desactiver'
                                                                : 'Activer')),
                                                  if (canUpdate)
                                                    const PopupMenuItem(
                                                        value: 'edit',
                                                        child:
                                                            Text('Modifier')),
                                                  if (canDelete)
                                                    const PopupMenuItem(
                                                        value: 'delete',
                                                        child:
                                                            Text('Supprimer'))
                                                ])));
                              }))),
          if (!_isLoading && _pages > 1)
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              IconButton(
                  onPressed: _page > 1
                      ? () {
                          setState(() => _page--);
                          _load();
                        }
                      : null,
                  icon: const Icon(Icons.chevron_left)),
              Text('Page $_page / $_pages'),
              IconButton(
                  onPressed: _page < _pages
                      ? () {
                          setState(() => _page++);
                          _load();
                        }
                      : null,
                  icon: const Icon(Icons.chevron_right))
            ])
        ])));
  }
}
