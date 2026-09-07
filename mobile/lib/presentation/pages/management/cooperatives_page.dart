import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/error_banner.dart';

class CooperativesPage extends StatefulWidget {
  final ApiClient apiClient;
  final Set<String> permissions;
  final bool isAdmin;

  const CooperativesPage({
    super.key,
    required this.apiClient,
    this.permissions = const {},
    this.isAdmin = false,
  });

  @override
  State<CooperativesPage> createState() => _CooperativesPageState();
}

class _CooperativesPageState extends State<CooperativesPage> {
  final _search = TextEditingController();
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
        '/cooperatives',
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
        _cooperatives = result;
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
          'Impossible de charger les cooperatives.',
          'MOBILE_COOPERATIVES_LOAD_ERROR',
        );
      });
    }
  }

  Future<void> _toggle(Map<String, dynamic> item) async {
    try {
      await widget.apiClient.patch('/cooperatives/${item['id']}/toggle');
      await _load(showLoading: false);
    } catch (exception) {
      if (!mounted) return;
      setState(() => _error = userError(
            exception,
            'Impossible de modifier le statut.',
            'MOBILE_COOPERATIVE_TOGGLE_ERROR',
          ));
    }
  }

  Future<void> _delete(Map<String, dynamic> item) async {
    if (!await _confirm('Supprimer cette cooperative ?')) return;
    try {
      await widget.apiClient.delete('/cooperatives/${item['id']}');
      await _load(showLoading: false);
    } catch (exception) {
      if (!mounted) return;
      setState(() => _error = userError(
            exception,
            'Suppression impossible. Verifiez les donnees rattachees.',
            'MOBILE_COOPERATIVE_DELETE_ERROR',
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
    String? Function(String?)? validator,
    TextInputType? keyboardType,
    int maxLines = 1,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      maxLines: maxLines,
      decoration: InputDecoration(labelText: label),
      validator: validator,
    );
  }

  String _userName(dynamic user) {
    if (user is! Map) return '-';
    final name = '${user['first_name'] ?? ''} ${user['name'] ?? ''}'.trim();
    return name.isEmpty ? '-' : name;
  }

  Future<void> _form([Map<String, dynamic>? current]) async {
    List<Map<String, dynamic>> responsables = [];
    if (widget.isAdmin) {
      try {
        responsables = _items(
          (await widget.apiClient.get('/cooperatives/eligible-responsables'))
              .data,
        );
      } catch (exception) {
        if (mounted) {
          setState(() => _error = userError(
                exception,
                'Impossible de charger les responsables.',
                'MOBILE_COOPERATIVE_RESPONSABLES_ERROR',
              ));
        }
        return;
      }
    }

    final formKey = GlobalKey<FormState>();
    final fields = <String, TextEditingController>{
      'nom': TextEditingController(text: current?['nom'] as String? ?? ''),
      'sigle': TextEditingController(text: current?['sigle'] as String? ?? ''),
      'numero_agrement': TextEditingController(
          text: current?['numero_agrement'] as String? ?? ''),
      'adresse':
          TextEditingController(text: current?['adresse'] as String? ?? ''),
      'ville': TextEditingController(text: current?['ville'] as String? ?? ''),
      'telephone':
          TextEditingController(text: current?['telephone'] as String? ?? ''),
      'email': TextEditingController(text: current?['email'] as String? ?? ''),
      'description':
          TextEditingController(text: current?['description'] as String? ?? ''),
    };
    int? responsableId = current?['responsable_id'] as int?;
    bool submitting = false;
    String? formError;

    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (context, setDialogState) => AlertDialog(
            backgroundColor: AppTheme.surface,
            title: Text(current == null
                ? 'Nouvelle cooperative'
                : 'Modifier la cooperative'),
            content: SizedBox(
              width: 560,
              child: SingleChildScrollView(
                child: Form(
                  key: formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (formError != null) ErrorBanner(message: formError!),
                      _input(
                        fields['nom']!,
                        'Nom',
                        validator: (value) =>
                            value == null || value.trim().isEmpty
                                ? 'Nom obligatoire'
                                : null,
                      ),
                      _input(fields['sigle']!, 'Sigle'),
                      _input(fields['numero_agrement']!, 'Numero d agrement'),
                      _input(fields['adresse']!, 'Adresse'),
                      _input(fields['ville']!, 'Ville'),
                      _input(fields['telephone']!, 'Telephone'),
                      _input(fields['email']!, 'Email',
                          keyboardType: TextInputType.emailAddress),
                      if (widget.isAdmin) ...[
                        const SizedBox(height: 10),
                        DropdownButtonFormField<int>(
                          initialValue: responsableId,
                          decoration:
                              const InputDecoration(labelText: 'Responsable'),
                          items: responsables
                              .map(
                                (item) => DropdownMenuItem<int>(
                                  value: item['id'] as int,
                                  child: Text(_userName(item)),
                                ),
                              )
                              .toList(),
                          onChanged: submitting
                              ? null
                              : (value) =>
                                  setDialogState(() => responsableId = value),
                        ),
                      ],
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
                        setDialogState(() {
                          submitting = true;
                          formError = null;
                        });
                        try {
                          final payload = <String, dynamic>{
                            for (final entry in fields.entries)
                              entry.key: entry.value.text.trim().isEmpty
                                  ? null
                                  : entry.value.text.trim(),
                            if (widget.isAdmin) 'responsable_id': responsableId,
                          };
                          if (current == null) {
                            await widget.apiClient
                                .post('/cooperatives', data: payload);
                          } else {
                            await widget.apiClient.put(
                                '/cooperatives/${current['id']}',
                                data: payload);
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
                              'MOBILE_COOPERATIVE_SAVE_ERROR',
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

  Widget _line(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
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

  Future<void> _details(Map<String, dynamic> summary) async {
    try {
      final id = summary['id'] as int;
      final cooperative = Map<String, dynamic>.from(
        (await widget.apiClient.get('/cooperatives/$id')).data as Map,
      );
      final members = _items(
          (await widget.apiClient.get('/cooperatives/$id/members')).data);
      final gares =
          _items((await widget.apiClient.get('/cooperatives/$id/gares')).data);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: Text(cooperative['nom'] as String? ?? 'Cooperative'),
          content: SizedBox(
            width: 640,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _line('Sigle', cooperative['sigle'] as String? ?? '-'),
                  _line('Agrement',
                      cooperative['numero_agrement'] as String? ?? '-'),
                  _line('Adresse',
                      '${cooperative['adresse'] ?? '-'}, ${cooperative['ville'] ?? '-'}'),
                  _line(
                      'Telephone', cooperative['telephone'] as String? ?? '-'),
                  _line('Email', cooperative['email'] as String? ?? '-'),
                  _line('Responsable', _userName(cooperative['responsable'])),
                  _line('Statut',
                      cooperative['is_active'] == true ? 'Active' : 'Inactive'),
                  const Divider(),
                  _sectionHeader('Membres', _can('COOPERATIVE_UPDATE'),
                      () async {
                    await _addMember(id);
                    if (dialogContext.mounted) Navigator.pop(dialogContext);
                    _details(cooperative);
                  }),
                  if (members.isEmpty) const Text('Aucun membre.'),
                  for (final member in members)
                    _memberTile(id, member, dialogContext),
                  const Divider(),
                  _sectionHeader('Gares rattachees', _can('COOPERATIVE_UPDATE'),
                      () async {
                    await _attachGare(id);
                    if (dialogContext.mounted) Navigator.pop(dialogContext);
                    _details(cooperative);
                  }),
                  if (gares.isEmpty) const Text('Aucune gare rattachee.'),
                  for (final association in gares)
                    _gareAssociationTile(id, association, dialogContext),
                ],
              ),
            ),
          ),
          actions: [
            if (_can('COOPERATIVE_UPDATE'))
              TextButton(
                onPressed: () {
                  Navigator.pop(dialogContext);
                  _form(cooperative);
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
            'Impossible de charger le detail de la cooperative.',
            'MOBILE_COOPERATIVE_DETAIL_ERROR',
          ));
    }
  }

  Widget _memberTile(int cooperativeId, Map<String, dynamic> member,
      BuildContext dialogContext) {
    final user = _userName(member['user']);
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(user == '-' ? 'Utilisateur #${member['id_user']}' : user),
      subtitle: Text(
          '${member['fonction'] ?? 'Membre'} - ${member['is_active'] == true ? 'Actif' : 'Inactif'}'),
      trailing: _can('COOPERATIVE_UPDATE')
          ? IconButton(
              icon: Icon(member['is_active'] == true
                  ? Icons.toggle_on
                  : Icons.toggle_off),
              onPressed: () async {
                await widget.apiClient.put(
                  '/cooperatives/$cooperativeId/members/${member['id_user']}',
                  data: {'is_active': member['is_active'] != true},
                );
                if (dialogContext.mounted) Navigator.pop(dialogContext);
                _details({'id': cooperativeId});
              },
            )
          : null,
    );
  }

  Widget _gareAssociationTile(int cooperativeId,
      Map<String, dynamic> association, BuildContext dialogContext) {
    final gare = association['gare'];
    final name = gare is Map ? gare['nom'] as String? : null;
    final city = gare is Map ? gare['ville'] as String? : null;
    final gareId = association['id_gare'];
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(name ?? 'Gare #$gareId'),
      subtitle: Text(city ?? '-'),
      trailing: _can('COOPERATIVE_UPDATE')
          ? IconButton(
              icon: const Icon(Icons.link_off),
              onPressed: () async {
                await widget.apiClient
                    .delete('/cooperatives/$cooperativeId/attach-gare/$gareId');
                if (dialogContext.mounted) Navigator.pop(dialogContext);
                _details({'id': cooperativeId});
              },
            )
          : null,
    );
  }

  Future<void> _addMember(int cooperativeId) async {
    try {
      final users = _items(
        (await widget.apiClient
                .get('/cooperatives/$cooperativeId/eligible-members'))
            .data,
      );
      if (!mounted) return;
      int? userId;
      final function = TextEditingController(text: 'MEMBRE');
      final start = TextEditingController();
      final end = TextEditingController();
      try {
        await showDialog<void>(
          context: context,
          builder: (dialogContext) => StatefulBuilder(
            builder: (context, setDialogState) => AlertDialog(
              backgroundColor: AppTheme.surface,
              title: const Text('Ajouter un membre'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    DropdownButtonFormField<int>(
                      initialValue: userId,
                      decoration:
                          const InputDecoration(labelText: 'Utilisateur'),
                      items: users
                          .map((item) => DropdownMenuItem<int>(
                                value: item['id'] as int,
                                child: Text(_userName(item)),
                              ))
                          .toList(),
                      onChanged: (value) =>
                          setDialogState(() => userId = value),
                    ),
                    const SizedBox(height: 10),
                    TextField(
                        controller: function,
                        decoration:
                            const InputDecoration(labelText: 'Fonction')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: start,
                        decoration: const InputDecoration(
                            labelText: 'Adhesion (AAAA-MM-JJ)')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: end,
                        decoration: const InputDecoration(
                            labelText: 'Fin (optionnelle)')),
                  ],
                ),
              ),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(dialogContext),
                    child: const Text('Annuler')),
                ElevatedButton(
                  onPressed: userId == null
                      ? null
                      : () async {
                          try {
                            await widget.apiClient.post(
                              '/cooperatives/$cooperativeId/members',
                              data: {
                                'id_user': userId,
                                'fonction': function.text.trim(),
                                'date_adhesion': start.text.trim().isEmpty
                                    ? null
                                    : start.text.trim(),
                                'date_fin': end.text.trim().isEmpty
                                    ? null
                                    : end.text.trim(),
                              },
                            );
                            if (dialogContext.mounted)
                              Navigator.pop(dialogContext);
                          } catch (exception) {
                            if (mounted) {
                              setState(() => _error = userError(
                                    exception,
                                    'Impossible d ajouter le membre.',
                                    'MOBILE_MEMBER_SAVE_ERROR',
                                  ));
                            }
                          }
                        },
                  child: const Text('Ajouter'),
                ),
              ],
            ),
          ),
        );
      } finally {
        function.dispose();
        start.dispose();
        end.dispose();
      }
    } catch (exception) {
      if (!mounted) return;
      setState(() => _error = userError(
            exception,
            'Impossible de charger les utilisateurs disponibles.',
            'MOBILE_MEMBER_USERS_ERROR',
          ));
    }
  }

  Future<void> _attachGare(int cooperativeId) async {
    try {
      final gares = _items(
        (await widget.apiClient
                .get('/cooperatives/$cooperativeId/available-gares'))
            .data,
      );
      if (!mounted) return;
      int? gareId;
      final start = TextEditingController();
      final end = TextEditingController();
      try {
        await showDialog<void>(
          context: context,
          builder: (dialogContext) => StatefulBuilder(
            builder: (context, setDialogState) => AlertDialog(
              backgroundColor: AppTheme.surface,
              title: const Text('Rattacher une gare'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    DropdownButtonFormField<int>(
                      initialValue: gareId,
                      decoration: const InputDecoration(labelText: 'Gare'),
                      items: gares
                          .map((item) => DropdownMenuItem<int>(
                                value: item['id'] as int,
                                child: Text(
                                    '${item['nom']} - ${item['ville'] ?? ''}'),
                              ))
                          .toList(),
                      onChanged: (value) =>
                          setDialogState(() => gareId = value),
                    ),
                    const SizedBox(height: 10),
                    TextField(
                        controller: start,
                        decoration: const InputDecoration(
                            labelText: 'Debut (AAAA-MM-JJ)')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: end,
                        decoration: const InputDecoration(
                            labelText: 'Fin (optionnelle)')),
                  ],
                ),
              ),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(dialogContext),
                    child: const Text('Annuler')),
                ElevatedButton(
                  onPressed: gareId == null
                      ? null
                      : () async {
                          try {
                            await widget.apiClient.post(
                              '/cooperatives/$cooperativeId/attach-gare/$gareId',
                              data: {
                                'date_debut': start.text.trim().isEmpty
                                    ? null
                                    : start.text.trim(),
                                'date_fin': end.text.trim().isEmpty
                                    ? null
                                    : end.text.trim(),
                              },
                            );
                            if (dialogContext.mounted)
                              Navigator.pop(dialogContext);
                          } catch (exception) {
                            if (mounted) {
                              setState(() => _error = userError(
                                    exception,
                                    'Impossible de rattacher la gare.',
                                    'MOBILE_GARE_ATTACHMENT_ERROR',
                                  ));
                            }
                          }
                        },
                  child: const Text('Rattacher'),
                ),
              ],
            ),
          ),
        );
      } finally {
        start.dispose();
        end.dispose();
      }
    } catch (exception) {
      if (!mounted) return;
      setState(() => _error = userError(
            exception,
            'Impossible de charger les gares disponibles.',
            'MOBILE_GARE_OPTIONS_ERROR',
          ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final canCreate = _can('COOPERATIVE_CREATE');
    final canUpdate = _can('COOPERATIVE_UPDATE');
    final canDelete = widget.isAdmin;
    return Scaffold(
      appBar: AppBar(
        title: Text('Cooperatives ($_total)'),
        actions: [
          IconButton(onPressed: _load, icon: const Icon(Icons.refresh))
        ],
      ),
      floatingActionButton: canCreate
          ? FloatingActionButton.extended(
              onPressed: () => _form(),
              icon: const Icon(Icons.add),
              label: const Text('Nouvelle cooperative'),
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
                  : _cooperatives.isEmpty
                      ? const Center(
                          child: Text('Aucune cooperative enregistree.'))
                      : RefreshIndicator(
                          onRefresh: _load,
                          child: ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _cooperatives.length,
                            itemBuilder: (context, index) {
                              final item = _cooperatives[index];
                              return Card(
                                color: AppTheme.surface,
                                child: ListTile(
                                  onTap: () => _details(item),
                                  leading: CircleAvatar(
                                    child: Icon(item['is_active'] == true
                                        ? Icons.business
                                        : Icons.business_center),
                                  ),
                                  title: Text(item['nom'] as String? ?? '-'),
                                  subtitle: Text(
                                    '${item['sigle'] ?? ''} - ${item['ville'] ?? '-'}\n${item['telephone'] ?? item['email'] ?? ''}',
                                  ),
                                  isThreeLine: true,
                                  trailing: PopupMenuButton<String>(
                                    onSelected: (value) {
                                      if (value == 'toggle' && canUpdate)
                                        _toggle(item);
                                      if (value == 'edit' && canUpdate)
                                        _form(item);
                                      if (value == 'delete' && canDelete)
                                        _delete(item);
                                    },
                                    itemBuilder: (_) => [
                                      const PopupMenuItem(
                                          value: 'details',
                                          child: Text('Details')),
                                      if (canUpdate)
                                        PopupMenuItem(
                                          value: 'toggle',
                                          child: Text(item['is_active'] == true
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
