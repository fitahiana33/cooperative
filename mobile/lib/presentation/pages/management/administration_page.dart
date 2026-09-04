import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/error_banner.dart';

class AdministrationPage extends StatefulWidget {
  final ApiClient apiClient;
  final Set<String> permissions;
  final bool isAdmin;

  const AdministrationPage({
    super.key,
    required this.apiClient,
    this.permissions = const {},
    this.isAdmin = false,
  });

  @override
  State<AdministrationPage> createState() => _AdministrationPageState();
}

class _AdministrationPageState extends State<AdministrationPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  final _search = TextEditingController();
  List<Map<String, dynamic>> _users = [];
  List<Map<String, dynamic>> _roles = [];
  List<Map<String, dynamic>> _permissions = [];
  bool _loading = true;
  String? _error;

  bool _can(String permission) =>
      widget.isAdmin || widget.permissions.contains(permission);

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
    _tabs.addListener(() => setState(() {}));
    _load();
  }

  @override
  void dispose() {
    _tabs.dispose();
    _search.dispose();
    super.dispose();
  }

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

  Future<void> _load() async {
    if (!mounted) return;
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final requests = <Future<dynamic>>[];
      if (_can('USER_READ')) {
        requests.add(widget.apiClient.get('/users', queryParameters: {
          'page': 1,
          'page_size': 100,
          'sort_by': 'name',
          'sort_order': 'asc',
        }));
      }
      if (_can('ROLE_MANAGE')) {
        requests.add(widget.apiClient.get('/roles', queryParameters: {
          'page': 1,
          'page_size': 100,
          'sort_by': 'libelle',
          'sort_order': 'asc',
        }));
        requests.add(widget.apiClient.get('/permissions', queryParameters: {
          'page': 1,
          'page_size': 100,
          'sort_by': 'code',
          'sort_order': 'asc',
        }));
      }

      final responses = await Future.wait(requests);
      var index = 0;
      final users = _can('USER_READ')
          ? _items(responses[index++].data)
          : <Map<String, dynamic>>[];
      final roles = _can('ROLE_MANAGE')
          ? _items(responses[index++].data)
          : <Map<String, dynamic>>[];
      final permissions = _can('ROLE_MANAGE')
          ? _items(responses[index].data)
          : <Map<String, dynamic>>[];

      if (!mounted) return;
      setState(() {
        _users = users;
        _roles = roles;
        _permissions = permissions;
        _loading = false;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = userError(
            error,
            'Impossible de charger l’administration.',
            'MOBILE_ADMIN_LOAD_ERROR',
          );
        });
      }
    }
  }

  Future<void> _showUserForm([Map<String, dynamic>? current]) async {
    final fields = <String, TextEditingController>{
      'name': TextEditingController(text: current?['name'] as String? ?? ''),
      'first_name':
          TextEditingController(text: current?['first_name'] as String? ?? ''),
      'email': TextEditingController(text: current?['email'] as String? ?? ''),
      'telephone':
          TextEditingController(text: current?['telephone'] as String? ?? ''),
      'address':
          TextEditingController(text: current?['address'] as String? ?? ''),
      'password': TextEditingController(),
    };
    final formKey = GlobalKey<FormState>();
    var role = 'passenger';
    bool submitting = false;
    String? formError;

    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: AppTheme.surface,
              title: Text(
                current == null
                    ? 'Nouvel utilisateur'
                    : 'Modifier l’utilisateur',
              ),
              content: SizedBox(
                width: 520,
                child: SingleChildScrollView(
                  child: Form(
                    key: formKey,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (formError != null) ErrorBanner(message: formError!),
                        TextFormField(
                          controller: fields['name'],
                          decoration: const InputDecoration(labelText: 'Nom'),
                          validator: (value) =>
                              value == null || value.trim().isEmpty
                                  ? 'Nom obligatoire'
                                  : null,
                        ),
                        const SizedBox(height: 10),
                        TextFormField(
                          controller: fields['first_name'],
                          decoration:
                              const InputDecoration(labelText: 'Prénom'),
                          validator: (value) =>
                              value == null || value.trim().isEmpty
                                  ? 'Prénom obligatoire'
                                  : null,
                        ),
                        const SizedBox(height: 10),
                        TextFormField(
                          controller: fields['email'],
                          decoration: const InputDecoration(labelText: 'Email'),
                          keyboardType: TextInputType.emailAddress,
                          validator: (value) =>
                              value == null || !value.contains('@')
                                  ? 'Email invalide'
                                  : null,
                        ),
                        const SizedBox(height: 10),
                        TextFormField(
                          controller: fields['telephone'],
                          decoration:
                              const InputDecoration(labelText: 'Téléphone'),
                        ),
                        const SizedBox(height: 10),
                        TextFormField(
                          controller: fields['address'],
                          decoration:
                              const InputDecoration(labelText: 'Adresse'),
                        ),
                        if (current == null) ...[
                          const SizedBox(height: 10),
                          TextFormField(
                            controller: fields['password'],
                            decoration: const InputDecoration(
                                labelText: 'Mot de passe'),
                            obscureText: true,
                            validator: (value) =>
                                value == null || value.length < 8
                                    ? '8 caractères minimum'
                                    : null,
                          ),
                          const SizedBox(height: 10),
                          DropdownButtonFormField<String>(
                            initialValue: role,
                            decoration: const InputDecoration(
                                labelText: 'Rôle initial'),
                            items: [
                              ..._roles.map(
                                (item) => DropdownMenuItem<String>(
                                  value: item['libelle'] as String,
                                  child: Text(item['libelle'] as String? ?? ''),
                                ),
                              ),
                              const DropdownMenuItem(
                                value: 'passenger',
                                child: Text('passenger'),
                              ),
                            ],
                            onChanged: submitting
                                ? null
                                : (value) => setDialogState(
                                      () => role = value ?? 'passenger',
                                    ),
                          ),
                        ],
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
                                if (entry.key != 'password' ||
                                    entry.value.text.trim().isNotEmpty)
                                  entry.key: entry.value.text.trim(),
                              if (current == null) 'role': role,
                            };
                            if (current == null) {
                              await widget.apiClient
                                  .post('/users', data: payload);
                            } else {
                              await widget.apiClient.put(
                                '/users/${current['id']}',
                                data: payload,
                              );
                            }
                            if (dialogContext.mounted) {
                              Navigator.pop(dialogContext);
                            }
                            await _load();
                          } catch (error) {
                            setDialogState(() {
                              submitting = false;
                              formError = userError(
                                error,
                                'Enregistrement impossible.',
                                'MOBILE_USER_SAVE_ERROR',
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
            );
          },
        ),
      );
    } finally {
      for (final controller in fields.values) {
        controller.dispose();
      }
    }
  }

  Future<void> _showRoleForm([Map<String, dynamic>? current]) async {
    final label =
        TextEditingController(text: current?['libelle'] as String? ?? '');
    final description =
        TextEditingController(text: current?['description'] as String? ?? '');
    final formKey = GlobalKey<FormState>();
    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: Text(current == null ? 'Nouveau rôle' : 'Modifier le rôle'),
          content: Form(
            key: formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  controller: label,
                  decoration: const InputDecoration(labelText: 'Libellé'),
                  validator: (value) => value == null || value.trim().length < 2
                      ? 'Libellé obligatoire'
                      : null,
                ),
                const SizedBox(height: 10),
                TextFormField(
                  controller: description,
                  decoration: const InputDecoration(labelText: 'Description'),
                  maxLines: 3,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Annuler'),
            ),
            ElevatedButton(
              onPressed: () async {
                if (!(formKey.currentState?.validate() ?? false)) return;
                try {
                  final payload = {
                    'libelle': label.text.trim(),
                    'description': description.text.trim().isEmpty
                        ? null
                        : description.text.trim(),
                  };
                  if (current == null) {
                    await widget.apiClient.post('/roles', data: payload);
                  } else {
                    await widget.apiClient.put(
                      '/roles/${current['id']}',
                      data: payload,
                    );
                  }
                  if (dialogContext.mounted) Navigator.pop(dialogContext);
                  await _load();
                } catch (error) {
                  if (mounted) {
                    setState(() => _error = userError(
                          error,
                          'Enregistrement du rôle impossible.',
                          'MOBILE_ROLE_SAVE_ERROR',
                        ));
                  }
                }
              },
              child: const Text('Enregistrer'),
            ),
          ],
        ),
      );
    } finally {
      label.dispose();
      description.dispose();
    }
  }

  Future<void> _showPermissionForm([Map<String, dynamic>? current]) async {
    final fields = {
      'code': TextEditingController(text: current?['code'] as String? ?? ''),
      'libelle':
          TextEditingController(text: current?['libelle'] as String? ?? ''),
      'module':
          TextEditingController(text: current?['module'] as String? ?? ''),
      'description':
          TextEditingController(text: current?['description'] as String? ?? ''),
    };
    final formKey = GlobalKey<FormState>();
    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: Text(
            current == null ? 'Nouvelle permission' : 'Modifier la permission',
          ),
          content: Form(
            key: formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                for (final entry in fields.entries)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: TextFormField(
                      controller: entry.value,
                      decoration: InputDecoration(labelText: entry.key),
                      validator: entry.key == 'description'
                          ? null
                          : (value) => value == null || value.trim().length < 2
                              ? 'Champ obligatoire'
                              : null,
                    ),
                  ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Annuler'),
            ),
            ElevatedButton(
              onPressed: () async {
                if (!(formKey.currentState?.validate() ?? false)) return;
                try {
                  final payload = {
                    for (final entry in fields.entries)
                      entry.key: entry.value.text.trim().isEmpty
                          ? null
                          : entry.value.text.trim(),
                  };
                  if (current == null) {
                    await widget.apiClient.post('/permissions', data: payload);
                  } else {
                    await widget.apiClient.put(
                      '/permissions/${current['id']}',
                      data: payload,
                    );
                  }
                  if (dialogContext.mounted) Navigator.pop(dialogContext);
                  await _load();
                } catch (error) {
                  if (mounted) {
                    setState(() => _error = userError(
                          error,
                          'Enregistrement de la permission impossible.',
                          'MOBILE_PERMISSION_SAVE_ERROR',
                        ));
                  }
                }
              },
              child: const Text('Enregistrer'),
            ),
          ],
        ),
      );
    } finally {
      for (final controller in fields.values) {
        controller.dispose();
      }
    }
  }

  Future<void> _toggle(String endpoint, Map<String, dynamic> item) async {
    try {
      await widget.apiClient.patch('/$endpoint/${item['id']}/toggle');
      await _load();
    } catch (error) {
      if (mounted) {
        setState(() => _error = userError(
              error,
              'Impossible de modifier le statut.',
              'MOBILE_ADMIN_TOGGLE_ERROR',
            ));
      }
    }
  }

  Future<void> _delete(String endpoint, Map<String, dynamic> item) async {
    if (!await _confirm('Supprimer cet élément ?')) return;
    try {
      await widget.apiClient.delete('/$endpoint/${item['id']}');
      await _load();
    } catch (error) {
      if (mounted) {
        setState(() => _error = userError(
              error,
              'Suppression impossible. Vérifiez les rattachements.',
              'MOBILE_ADMIN_DELETE_ERROR',
            ));
      }
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

  Future<void> _showUserDetails(Map<String, dynamic> user) async {
    final roles = user['roles'] is List
        ? (user['roles'] as List)
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList()
        : <Map<String, dynamic>>[];
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: Text('${user['first_name'] ?? ''} ${user['name'] ?? ''}'.trim()),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _line('Email', user['email'] as String? ?? '-'),
              _line('Téléphone', user['telephone'] as String? ?? '-'),
              _line('Adresse', user['address'] as String? ?? '-'),
              const Divider(),
              const Text('Rôles',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              if (roles.isEmpty) const Text('Aucun rôle.'),
              for (final role in roles)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(role['libelle'] as String? ?? '-'),
                  trailing: _can('ROLE_MANAGE')
                      ? IconButton(
                          icon: const Icon(Icons.remove_circle_outline),
                          onPressed: () async {
                            await widget.apiClient.delete(
                              '/users/${user['id']}/roles/${role['id']}',
                            );
                            if (dialogContext.mounted) {
                              Navigator.pop(dialogContext);
                            }
                            _showUserDetails(user);
                          },
                        )
                      : null,
                ),
              if (_can('ROLE_MANAGE'))
                TextButton.icon(
                  onPressed: () async {
                    await _assignRole(user);
                    if (dialogContext.mounted) Navigator.pop(dialogContext);
                    _showUserDetails(user);
                  },
                  icon: const Icon(Icons.add),
                  label: const Text('Attribuer un rôle'),
                ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
  }

  Future<void> _assignRole(Map<String, dynamic> user) async {
    int? roleId;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: const Text('Attribuer un rôle'),
          content: DropdownButtonFormField<int>(
            initialValue: roleId,
            items: _roles
                .map(
                  (item) => DropdownMenuItem<int>(
                    value: item['id'] as int,
                    child: Text(item['libelle'] as String? ?? ''),
                  ),
                )
                .toList(),
            onChanged: (value) => setDialogState(() => roleId = value),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Annuler'),
            ),
            ElevatedButton(
              onPressed: roleId == null
                  ? null
                  : () async {
                      try {
                        await widget.apiClient.post(
                          '/users/${user['id']}/roles/$roleId',
                        );
                        if (dialogContext.mounted) Navigator.pop(dialogContext);
                      } catch (error) {
                        if (mounted) {
                          setState(() => _error = userError(
                                error,
                                'Attribution du rôle impossible.',
                                'MOBILE_USER_ROLE_ERROR',
                              ));
                        }
                      }
                    },
              child: const Text('Attribuer'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showRoleDetails(Map<String, dynamic> role) async {
    List<Map<String, dynamic>> assigned = [];
    try {
      assigned = _items(
        (await widget.apiClient.get('/roles/${role['id']}/permissions')).data,
      );
    } catch (_) {}

    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: Text(role['libelle'] as String? ?? 'Rôle'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(role['description'] as String? ?? 'Aucune description.'),
              const Divider(),
              const Text('Permissions',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              if (assigned.isEmpty) const Text('Aucune permission.'),
              for (final permission in assigned)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(permission['code'] as String? ?? '-'),
                  trailing: IconButton(
                    icon: const Icon(Icons.remove_circle_outline),
                    onPressed: () async {
                      await widget.apiClient.delete(
                        '/roles/${role['id']}/permissions/${permission['id']}',
                      );
                      if (dialogContext.mounted) Navigator.pop(dialogContext);
                      _showRoleDetails(role);
                    },
                  ),
                ),
              TextButton.icon(
                onPressed: () async {
                  await _assignPermission(role);
                  if (dialogContext.mounted) Navigator.pop(dialogContext);
                  _showRoleDetails(role);
                },
                icon: const Icon(Icons.add),
                label: const Text('Rattacher une permission'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
  }

  Future<void> _assignPermission(Map<String, dynamic> role) async {
    int? permissionId;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: const Text('Rattacher une permission'),
          content: DropdownButtonFormField<int>(
            initialValue: permissionId,
            items: _permissions
                .map(
                  (item) => DropdownMenuItem<int>(
                    value: item['id'] as int,
                    child: Text(item['code'] as String? ?? ''),
                  ),
                )
                .toList(),
            onChanged: (value) => setDialogState(() => permissionId = value),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Annuler'),
            ),
            ElevatedButton(
              onPressed: permissionId == null
                  ? null
                  : () async {
                      try {
                        await widget.apiClient.post(
                          '/roles/${role['id']}/permissions/$permissionId',
                        );
                        if (dialogContext.mounted) Navigator.pop(dialogContext);
                      } catch (error) {
                        if (mounted) {
                          setState(() => _error = userError(
                                error,
                                'Rattachement impossible.',
                                'MOBILE_ROLE_PERMISSION_ERROR',
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
  }

  Widget _line(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(
          children: [
            SizedBox(
              width: 95,
              child: Text(label, style: const TextStyle(color: Colors.white60)),
            ),
            Expanded(child: Text(value)),
          ],
        ),
      );

  Widget _usersTab() {
    final query = _search.text.trim().toLowerCase();
    final values = _users.where((item) {
      final text = '${item['name']} ${item['first_name']} ${item['email']}'
          .toLowerCase();
      return text.contains(query);
    }).toList();
    return _list(
      values,
      (item) => ListTile(
        onTap: () => _showUserDetails(item),
        leading: const CircleAvatar(child: Icon(Icons.person)),
        title: Text('${item['first_name'] ?? ''} ${item['name'] ?? ''}'.trim()),
        subtitle: Text('${item['email'] ?? '-'} · ${item['role'] ?? '-'}'),
        trailing: PopupMenuButton<String>(
          onSelected: (value) {
            if (value == 'edit') _showUserForm(item);
            if (value == 'toggle') _toggle('users', item);
            if (value == 'delete') _delete('users', item);
          },
          itemBuilder: (_) => const [
            PopupMenuItem(value: 'edit', child: Text('Modifier')),
            PopupMenuItem(value: 'toggle', child: Text('Activer / désactiver')),
            PopupMenuItem(value: 'delete', child: Text('Supprimer')),
          ],
        ),
      ),
    );
  }

  Widget _rolesTab() => _list(
        _roles,
        (item) => ListTile(
          onTap: () => _showRoleDetails(item),
          leading: const CircleAvatar(child: Icon(Icons.shield)),
          title: Text(item['libelle'] as String? ?? '-'),
          subtitle: Text(item['description'] as String? ?? '-'),
          trailing: PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'edit') _showRoleForm(item);
              if (value == 'toggle') _toggle('roles', item);
              if (value == 'delete') _delete('roles', item);
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'edit', child: Text('Modifier')),
              PopupMenuItem(
                  value: 'toggle', child: Text('Activer / désactiver')),
              PopupMenuItem(value: 'delete', child: Text('Supprimer')),
            ],
          ),
        ),
      );

  Widget _permissionsTab() => _list(
        _permissions,
        (item) => ListTile(
          leading: const CircleAvatar(child: Icon(Icons.key)),
          title: Text(item['code'] as String? ?? '-'),
          subtitle: Text('${item['module'] ?? '-'} · ${item['libelle'] ?? ''}'),
          trailing: PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'edit') _showPermissionForm(item);
              if (value == 'toggle') _toggle('permissions', item);
              if (value == 'delete') _delete('permissions', item);
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'edit', child: Text('Modifier')),
              PopupMenuItem(
                  value: 'toggle', child: Text('Activer / désactiver')),
              PopupMenuItem(value: 'delete', child: Text('Supprimer')),
            ],
          ),
        ),
      );

  Widget _list(
    List<Map<String, dynamic>> values,
    Widget Function(Map<String, dynamic>) builder,
  ) {
    if (values.isEmpty) {
      return const Center(child: Text('Aucun élément enregistré.'));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: values.length,
      itemBuilder: (context, index) => Card(
        color: AppTheme.surface,
        child: builder(values[index]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tab = _tabs.index;
    final canUsers = _can('USER_READ');
    final canManage = _can('ROLE_MANAGE');
    final canCreate = tab == 0 ? _can('USER_CREATE') : canManage;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Administration'),
        actions: [
          IconButton(onPressed: _load, icon: const Icon(Icons.refresh))
        ],
        bottom: TabBar(
          controller: _tabs,
          tabs: const [
            Tab(text: 'Utilisateurs'),
            Tab(text: 'Rôles'),
            Tab(text: 'Permissions'),
          ],
        ),
      ),
      floatingActionButton: canCreate
          ? FloatingActionButton.extended(
              onPressed: () {
                if (tab == 0) _showUserForm();
                if (tab == 1) _showRoleForm();
                if (tab == 2) _showPermissionForm();
              },
              icon: const Icon(Icons.add),
              label: const Text('Nouveau'),
            )
          : null,
      body: Column(
        children: [
          if ((tab == 0 && canUsers) || (tab > 0 && canManage))
            Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: _search,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  labelText: 'Rechercher',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: IconButton(
                    onPressed: () {
                      _search.clear();
                      setState(() {});
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
                : TabBarView(
                    controller: _tabs,
                    children: [
                      canUsers
                          ? _usersTab()
                          : const Center(
                              child: Text('Accès utilisateurs non autorisé.'),
                            ),
                      canManage
                          ? _rolesTab()
                          : const Center(
                              child: Text('Accès rôles non autorisé.'),
                            ),
                      canManage
                          ? _permissionsTab()
                          : const Center(
                              child: Text('Accès permissions non autorisé.'),
                            ),
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}
