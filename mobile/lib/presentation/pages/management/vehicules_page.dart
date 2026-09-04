import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/error_banner.dart';

class _DocumentDraft {
  String type = 'CARTE_GRISE';
  final number = TextEditingController();
  final delivery = TextEditingController();
  final expiration = TextEditingController();
  PlatformFile? file;
  bool isValid = true;

  bool get isEmpty =>
      number.text.trim().isEmpty &&
      delivery.text.trim().isEmpty &&
      expiration.text.trim().isEmpty &&
      file == null;

  void dispose() {
    number.dispose();
    delivery.dispose();
    expiration.dispose();
  }
}

class VehiculesPage extends StatefulWidget {
  final ApiClient apiClient;
  final Set<String> permissions;
  final bool isAdmin;

  const VehiculesPage({
    super.key,
    required this.apiClient,
    this.permissions = const {},
    this.isAdmin = false,
  });

  @override
  State<VehiculesPage> createState() => _VehiculesPageState();
}

class _VehiculesPageState extends State<VehiculesPage> {
  final _searchController = TextEditingController();
  List<Map<String, dynamic>> _vehicules = [];
  List<Map<String, dynamic>> _modeles = [];
  List<Map<String, dynamic>> _marques = [];
  List<Map<String, dynamic>> _cooperatives = [];
  bool _isLoading = true;
  String? _error;
  int _page = 1;
  int _pages = 1;
  int _total = 0;

  bool _can(String permission) =>
      widget.isAdmin || widget.permissions.contains(permission);

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

  List<Map<String, dynamic>> _items(dynamic data) {
    if (data is Map && data['items'] is List) {
      return (data['items'] as List)
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    }
    if (data is List) {
      return data
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    }
    return [];
  }

  Map<String, dynamic>? _findById(
      List<Map<String, dynamic>> values, dynamic id) {
    for (final value in values) {
      if (value['id'] == id) return value;
    }
    return null;
  }

  Future<void> _load({bool showLoading = true}) async {
    if (!mounted) return;
    setState(() {
      if (showLoading) _isLoading = true;
      _error = null;
    });
    try {
      final response = await widget.apiClient.get(
        '/vehicules',
        queryParameters: {
          'page': _page,
          'page_size': 20,
          'search': _searchController.text.trim().isEmpty
              ? null
              : _searchController.text.trim(),
          'sort_by': 'immatriculation',
          'sort_order': 'asc',
        },
      );
      final payload = response.data;
      final references = <Future<Response>>[
        widget.apiClient.get('/modeles', queryParameters: {
          'page': 1,
          'page_size': 100,
          'sort_by': 'nom',
          'sort_order': 'asc'
        }),
        widget.apiClient.get('/marques', queryParameters: {
          'page': 1,
          'page_size': 100,
          'sort_by': 'nom',
          'sort_order': 'asc'
        }),
      ];
      if (_can('COOPERATIVE_READ')) {
        references.add(widget.apiClient.get('/cooperatives', queryParameters: {
          'page': 1,
          'page_size': 100,
          'sort_by': 'nom',
          'sort_order': 'asc'
        }));
      }
      final refResponses = await Future.wait(references);
      if (!mounted) return;
      setState(() {
        _vehicules = _items(payload);
        _total = payload is Map
            ? (payload['total'] as int? ?? _vehicules.length)
            : _vehicules.length;
        _pages = payload is Map ? (payload['pages'] as int? ?? 1) : 1;
        _modeles = _items(refResponses[0].data);
        _marques = _items(refResponses[1].data);
        _cooperatives =
            refResponses.length > 2 ? _items(refResponses[2].data) : [];
        _isLoading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = userError(error, 'Impossible de charger les vehicules.',
            'MOBILE_VEHICLES_LOAD_ERROR');
        _isLoading = false;
      });
    }
  }

  String _modeleLabel(int? id) {
    final modele = _findById(_modeles, id);
    if (modele == null) return id == null ? 'Modele non defini' : 'Modele #$id';
    final marque = _findById(_marques, modele['id_marque']);
    return '${marque?['nom'] ?? ''} ${modele['nom'] ?? ''}'.trim();
  }

  String _cooperativeLabel(int? id) {
    final cooperative = _findById(_cooperatives, id);
    return cooperative?['nom'] as String? ??
        (id == null ? 'Cooperative non definie' : 'Cooperative #$id');
  }

  Future<void> _toggle(Map<String, dynamic> item) async {
    try {
      await widget.apiClient.patch('/vehicules/${item['id']}/toggle');
      await _load(showLoading: false);
    } catch (error) {
      if (mounted)
        setState(() => _error = userError(
            error,
            'Impossible de modifier le statut.',
            'MOBILE_VEHICLE_TOGGLE_ERROR'));
    }
  }

  Future<void> _delete(Map<String, dynamic> item) async {
    if (!mounted || !await _confirm('Supprimer ce vehicule ?')) return;
    try {
      await widget.apiClient.delete('/vehicules/${item['id']}');
      await _load(showLoading: false);
    } catch (error) {
      if (mounted)
        setState(() => _error = userError(
            error,
            'Impossible de supprimer le vehicule.',
            'MOBILE_VEHICLE_DELETE_ERROR'));
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
                  child: const Text('Annuler')),
              ElevatedButton(
                  onPressed: () => Navigator.pop(dialogContext, true),
                  child: const Text('Confirmer')),
            ],
          ),
        ) ??
        false;
  }

  Widget _documentDraftEditor(
    _DocumentDraft draft,
    bool submitting,
    StateSetter setDialogState,
    VoidCallback onRemove,
  ) {
    return Card(
      color: AppTheme.surfaceCard,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Document',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                IconButton(
                  onPressed: submitting ? null : onRemove,
                  icon: const Icon(Icons.delete_outline),
                  tooltip: 'Retirer',
                ),
              ],
            ),
            DropdownButtonFormField<String>(
              initialValue: draft.type,
              decoration: const InputDecoration(labelText: 'Type'),
              items: const [
                DropdownMenuItem(
                    value: 'CARTE_GRISE', child: Text('Carte grise')),
                DropdownMenuItem(value: 'ASSURANCE', child: Text('Assurance')),
                DropdownMenuItem(
                    value: 'VISITE_TECHNIQUE', child: Text('Visite technique')),
                DropdownMenuItem(
                    value: 'AUTRE_DOCUMENT', child: Text('Autre document')),
              ],
              onChanged: submitting
                  ? null
                  : (value) =>
                      setDialogState(() => draft.type = value ?? draft.type),
            ),
            const SizedBox(height: 8),
            CustomTextField(
              controller: draft.number,
              labelText: 'Numero du document',
              prefixIcon: Icons.numbers,
            ),
            const SizedBox(height: 8),
            CustomTextField(
              controller: draft.delivery,
              labelText: 'Date de delivrance (AAAA-MM-JJ)',
              prefixIcon: Icons.calendar_today,
              validator: (value) => value != null &&
                      value.trim().isNotEmpty &&
                      DateTime.tryParse(value.trim()) == null
                  ? 'Date invalide'
                  : null,
            ),
            const SizedBox(height: 8),
            CustomTextField(
              controller: draft.expiration,
              labelText: 'Date d expiration (AAAA-MM-JJ)',
              prefixIcon: Icons.event_available,
              validator: (value) => value != null &&
                      value.trim().isNotEmpty &&
                      DateTime.tryParse(value.trim()) == null
                  ? 'Date invalide'
                  : null,
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: submitting
                  ? null
                  : () async {
                      final result = await FilePicker.platform.pickFiles(
                        withData: true,
                        type: FileType.custom,
                        allowedExtensions: [
                          'pdf',
                          'png',
                          'jpg',
                          'jpeg',
                          'gif',
                          'webp',
                          'doc',
                          'docx',
                          'xls',
                          'xlsx',
                        ],
                      );
                      if (result != null && result.files.isNotEmpty) {
                        setDialogState(() => draft.file = result.files.single);
                      }
                    },
              icon: const Icon(Icons.attach_file),
              label: Text(draft.file?.name ?? 'Joindre un fichier'),
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Document valide'),
              value: draft.isValid,
              onChanged: submitting
                  ? null
                  : (value) => setDialogState(() => draft.isValid = value),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _uploadDocumentDraft(int vehicleId, _DocumentDraft draft) async {
    final selectedFile = draft.file;
    if (selectedFile == null) return;
    final MultipartFile multipart;
    if (selectedFile.bytes != null) {
      multipart = MultipartFile.fromBytes(
        selectedFile.bytes!,
        filename: selectedFile.name,
      );
    } else if (selectedFile.path != null) {
      multipart = await MultipartFile.fromFile(
        selectedFile.path!,
        filename: selectedFile.name,
      );
    } else {
      throw StateError('Le fichier selectionne est inaccessible.');
    }
    final delivery = draft.delivery.text.trim();
    final expiration = draft.expiration.text.trim();
    await widget.apiClient.post(
      '/vehicules/$vehicleId/documents/upload',
      data: FormData.fromMap({
        'type_document': draft.type,
        'numero_document':
            draft.number.text.trim().isEmpty ? null : draft.number.text.trim(),
        'date_delivrance': delivery.isEmpty ? null : delivery,
        'date_expiration': expiration.isEmpty ? null : expiration,
        'is_valid': draft.isValid,
        'file': multipart,
      }),
      options: Options(contentType: 'multipart/form-data'),
    );
  }

  Future<void> _showForm([Map<String, dynamic>? current]) async {
    if (_modeles.isEmpty || _cooperatives.isEmpty) {
      setState(() => _error =
          'Les modeles et cooperatives doivent etre disponibles avant la saisie.');
      return;
    }
    final formKey = GlobalKey<FormState>();
    final immatriculation = TextEditingController(
        text: current?['immatriculation'] as String? ?? '');
    final chevaux =
        TextEditingController(text: current?['chevaux']?.toString() ?? '');
    final places = TextEditingController(
        text: current?['nombre_places']?.toString() ?? '');
    final description =
        TextEditingController(text: current?['description'] as String? ?? '');
    int? modeleId = current?['id_modele'] as int?;
    int? cooperativeId = current?['id_cooperative'] as int?;
    bool disponibilite = current?['disponibilite'] as bool? ?? true;
    String etat = current?['etat'] as String? ?? 'BON_ETAT';
    final documents = <_DocumentDraft>[];
    bool submitting = false;
    String? formError;

    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (context, setDialogState) => AlertDialog(
            backgroundColor: AppTheme.surface,
            title: Text(
                current == null ? 'Nouveau vehicule' : 'Modifier le vehicule'),
            content: SizedBox(
              width: 520,
              child: SingleChildScrollView(
                child: Form(
                  key: formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (formError != null) ErrorBanner(message: formError!),
                      CustomTextField(
                          controller: immatriculation,
                          labelText: 'Immatriculation',
                          prefixIcon: Icons.badge_outlined,
                          validator: (v) => v == null || v.trim().length < 2
                              ? 'Immatriculation requise'
                              : null),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<int>(
                        initialValue: modeleId,
                        decoration: const InputDecoration(labelText: 'Modele'),
                        items: _modeles
                            .map((item) => DropdownMenuItem<int>(
                                value: item['id'] as int,
                                child: Text(_modeleLabel(item['id'] as int))))
                            .toList(),
                        onChanged: submitting
                            ? null
                            : (value) => setDialogState(() => modeleId = value),
                        validator: (value) =>
                            value == null ? 'Modele requis' : null,
                      ),
                      if (modeleId != null) ...[
                        const SizedBox(height: 8),
                        Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                                'Marque deduite : ${_modeleLabel(modeleId).split(' ').first}',
                                style: const TextStyle(
                                    color: AppTheme.primaryAccent))),
                      ],
                      const SizedBox(height: 12),
                      DropdownButtonFormField<int>(
                        initialValue: cooperativeId,
                        decoration: const InputDecoration(
                            labelText: 'Cooperative proprietaire'),
                        items: _cooperatives
                            .map((item) => DropdownMenuItem<int>(
                                value: item['id'] as int,
                                child: Text(item['nom'] as String? ?? '')))
                            .toList(),
                        onChanged: submitting
                            ? null
                            : (value) =>
                                setDialogState(() => cooperativeId = value),
                        validator: (value) =>
                            value == null ? 'Cooperative requise' : null,
                      ),
                      const SizedBox(height: 12),
                      Row(children: [
                        Expanded(
                            child: CustomTextField(
                                controller: chevaux,
                                labelText: 'Chevaux',
                                prefixIcon: Icons.speed,
                                keyboardType: TextInputType.number,
                                validator: (v) => v != null &&
                                        v.isNotEmpty &&
                                        int.tryParse(v) == null
                                    ? 'Nombre invalide'
                                    : null)),
                        const SizedBox(width: 12),
                        Expanded(
                            child: CustomTextField(
                                controller: places,
                                labelText: 'Nombre de places',
                                prefixIcon: Icons.event_seat,
                                keyboardType: TextInputType.number,
                                validator: (v) =>
                                    int.tryParse(v ?? '') == null ||
                                            int.parse(v!) <= 0
                                        ? 'Nombre requis'
                                        : null))
                      ]),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        initialValue: etat,
                        decoration: const InputDecoration(labelText: 'Etat'),
                        items: const [
                          DropdownMenuItem(
                              value: 'BON_ETAT', child: Text('Bon etat')),
                          DropdownMenuItem(
                              value: 'MOYEN', child: Text('Moyen')),
                          DropdownMenuItem(
                              value: 'A_REPARER', child: Text('A reparer')),
                          DropdownMenuItem(
                              value: 'HORS_SERVICE',
                              child: Text('Hors service'))
                        ],
                        onChanged: submitting
                            ? null
                            : (value) => setDialogState(() {
                                  etat = value ?? 'BON_ETAT';
                                  if (etat == 'HORS_SERVICE')
                                    disponibilite = false;
                                }),
                      ),
                      SwitchListTile(
                          title: const Text('Disponible'),
                          value: disponibilite,
                          onChanged: submitting || etat == 'HORS_SERVICE'
                              ? null
                              : (value) =>
                                  setDialogState(() => disponibilite = value),
                          contentPadding: EdgeInsets.zero),
                      CustomTextField(
                          controller: description,
                          labelText: 'Description',
                          prefixIcon: Icons.notes_outlined),
                      const Divider(height: 28),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Documents du vehicule',
                            style: TextStyle(
                                fontSize: 16, fontWeight: FontWeight.bold),
                          ),
                          TextButton.icon(
                            onPressed: submitting
                                ? null
                                : () => setDialogState(
                                    () => documents.add(_DocumentDraft())),
                            icon: const Icon(Icons.add),
                            label: const Text('Ajouter'),
                          ),
                        ],
                      ),
                      if (documents.isEmpty)
                        const Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            'Optionnel: vous pouvez rattacher un ou plusieurs fichiers.',
                            style: TextStyle(color: Colors.white60),
                          ),
                        ),
                      for (final document in documents)
                        _documentDraftEditor(
                          document,
                          submitting,
                          setDialogState,
                          () => setDialogState(() {
                            documents.remove(document);
                            document.dispose();
                          }),
                        ),
                    ],
                  ),
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
                            'id_modele': modeleId,
                            'id_cooperative': cooperativeId,
                            'immatriculation': immatriculation.text.trim(),
                            'chevaux': chevaux.text.trim().isEmpty
                                ? null
                                : int.parse(chevaux.text.trim()),
                            'nombre_places': int.parse(places.text.trim()),
                            'disponibilite': disponibilite,
                            'etat': etat,
                            'description': description.text.trim().isEmpty
                                ? null
                                : description.text.trim(),
                          };
                          final Response<dynamic> saved;
                          if (current == null) {
                            saved = await widget.apiClient
                                .post('/vehicules', data: payload);
                          } else {
                            saved = await widget.apiClient.put(
                                '/vehicules/${current['id']}',
                                data: payload);
                          }
                          for (final document in documents) {
                            if (document.isEmpty) continue;
                            final delivery = document.delivery.text.trim();
                            final expiration = document.expiration.text.trim();
                            if (document.file == null) {
                              throw StateError(
                                  'Chaque document renseigne doit avoir un fichier.');
                            }
                            if (delivery.isNotEmpty &&
                                expiration.isNotEmpty &&
                                expiration.compareTo(delivery) < 0) {
                              throw StateError(
                                  'La date d expiration doit suivre la date de delivrance.');
                            }
                            final savedVehicle =
                                Map<String, dynamic>.from(saved.data as Map);
                            await _uploadDocumentDraft(
                                savedVehicle['id'] as int, document);
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
                                'MOBILE_VEHICLE_SAVE_ERROR');
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
      immatriculation.dispose();
      chevaux.dispose();
      places.dispose();
      description.dispose();
      for (final document in documents) {
        document.dispose();
      }
    }
  }

  Future<void> _showDetails(int vehicleId) async {
    try {
      final response = await widget.apiClient.get('/vehicules/$vehicleId');
      final vehicle = Map<String, dynamic>.from(response.data as Map);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: Text('${vehicle['immatriculation'] ?? 'Vehicule'} - Details'),
          content: SizedBox(
              width: 560,
              child: SingleChildScrollView(child: _detailsContent(vehicle))),
          actions: [
            if (_can('VEHICULE_UPDATE'))
              TextButton(
                  onPressed: () {
                    Navigator.pop(dialogContext);
                    _showDocumentForm(vehicleId);
                  },
                  child: const Text('Ajouter un document')),
            TextButton(
                onPressed: () => Navigator.pop(dialogContext),
                child: const Text('Fermer')),
          ],
        ),
      );
    } catch (error) {
      if (mounted)
        setState(() => _error = userError(error,
            'Impossible de charger le detail.', 'MOBILE_VEHICLE_DETAIL_ERROR'));
    }
  }

  Widget _detailsContent(Map<String, dynamic> vehicle) {
    final modele = vehicle['modele'] is Map
        ? Map<String, dynamic>.from(vehicle['modele'])
        : null;
    final cooperative = vehicle['cooperative'] is Map
        ? Map<String, dynamic>.from(vehicle['cooperative'])
        : null;
    final documents = vehicle['documents'] is List
        ? (vehicle['documents'] as List)
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList()
        : <Map<String, dynamic>>[];
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _detailLine('Marque',
          _findById(_marques, modele?['id_marque'])?['nom'] as String? ?? '-'),
      _detailLine(
          'Modele',
          modele?['nom'] as String? ??
              _modeleLabel(vehicle['id_modele'] as int?)),
      _detailLine(
          'Proprietaire',
          cooperative?['nom'] as String? ??
              _cooperativeLabel(vehicle['id_cooperative'] as int?)),
      _detailLine('Chevaux', '${vehicle['chevaux'] ?? '-'}'),
      _detailLine('Places', '${vehicle['nombre_places'] ?? '-'}'),
      _detailLine('Disponibilite',
          vehicle['disponibilite'] == true ? 'Disponible' : 'Indisponible'),
      _detailLine('Etat', vehicle['etat'] as String? ?? '-'),
      const Divider(),
      const Text('Documents',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      const SizedBox(height: 8),
      if (documents.isEmpty) const Text('Aucun document rattache.'),
      ...documents.map((document) => Card(
          color: AppTheme.surfaceCard,
          child: ListTile(
              title: Text(document['type_document'] as String? ?? 'Document'),
              subtitle: Text(
                  'N° ${document['numero_document'] ?? '-'} - Expiration : ${document['date_expiration'] ?? '-'}'),
              trailing: Icon(
                  document['is_expired'] == true
                      ? Icons.warning_amber
                      : Icons.verified,
                  color: document['is_expired'] == true
                      ? Colors.orange
                      : AppTheme.success)))),
    ]);
  }

  Widget _detailLine(String label, String value) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(
            width: 125,
            child: Text(label, style: const TextStyle(color: Colors.white60))),
        Expanded(
            child: Text(value,
                style: const TextStyle(fontWeight: FontWeight.w600)))
      ]));

  Future<void> _showDocumentForm(int vehicleId) async {
    final formKey = GlobalKey<FormState>();
    final number = TextEditingController();
    final delivery = TextEditingController();
    final expiration = TextEditingController();
    String type = 'CARTE_GRISE';
    PlatformFile? selectedFile;
    bool submitting = false;
    String? formError;
    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
            builder: (context, setDialogState) => AlertDialog(
                  backgroundColor: AppTheme.surface,
                  title: const Text('Ajouter un document'),
                  content: SizedBox(
                      width: 500,
                      child: Form(
                          key: formKey,
                          child: SingleChildScrollView(
                              child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                if (formError != null)
                                  ErrorBanner(message: formError!),
                                DropdownButtonFormField<String>(
                                    initialValue: type,
                                    decoration: const InputDecoration(
                                        labelText: 'Type'),
                                    items: const [
                                      DropdownMenuItem(
                                          value: 'CARTE_GRISE',
                                          child: Text('Carte grise')),
                                      DropdownMenuItem(
                                          value: 'ASSURANCE',
                                          child: Text('Assurance')),
                                      DropdownMenuItem(
                                          value: 'VISITE_TECHNIQUE',
                                          child: Text('Visite technique')),
                                      DropdownMenuItem(
                                          value: 'AUTRE_DOCUMENT',
                                          child: Text('Autre document'))
                                    ],
                                    onChanged: submitting
                                        ? null
                                        : (value) => setDialogState(
                                            () => type = value ?? type)),
                                const SizedBox(height: 12),
                                CustomTextField(
                                    controller: number,
                                    labelText: 'Numero',
                                    prefixIcon: Icons.numbers),
                                const SizedBox(height: 12),
                                CustomTextField(
                                    controller: delivery,
                                    labelText:
                                        'Date de delivrance (AAAA-MM-JJ)',
                                    prefixIcon: Icons.calendar_today,
                                    validator: (value) => value != null &&
                                            value.isNotEmpty &&
                                            DateTime.tryParse(value) == null
                                        ? 'Date invalide'
                                        : null),
                                const SizedBox(height: 12),
                                CustomTextField(
                                    controller: expiration,
                                    labelText: 'Date d expiration (AAAA-MM-JJ)',
                                    prefixIcon: Icons.event_available,
                                    validator: (value) => value != null &&
                                            value.isNotEmpty &&
                                            DateTime.tryParse(value) == null
                                        ? 'Date invalide'
                                        : null),
                                const SizedBox(height: 12),
                                OutlinedButton.icon(
                                    onPressed: submitting
                                        ? null
                                        : () async {
                                            final result = await FilePicker
                                                .platform
                                                .pickFiles(
                                                    withData: true,
                                                    type: FileType.custom,
                                                    allowedExtensions: [
                                                  'pdf',
                                                  'png',
                                                  'jpg',
                                                  'jpeg',
                                                  'doc',
                                                  'docx',
                                                  'xls',
                                                  'xlsx'
                                                ]);
                                            if (result != null &&
                                                result.files.isNotEmpty)
                                              setDialogState(() =>
                                                  selectedFile =
                                                      result.files.single);
                                          },
                                    icon: const Icon(Icons.attach_file),
                                    label: Text(selectedFile?.name ??
                                        'Joindre un fichier')),
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
                                final deliveryDate =
                                    delivery.text.trim().isEmpty
                                        ? null
                                        : delivery.text.trim();
                                final expirationDate =
                                    expiration.text.trim().isEmpty
                                        ? null
                                        : expiration.text.trim();
                                if (deliveryDate != null &&
                                    expirationDate != null &&
                                    expirationDate.compareTo(deliveryDate) <
                                        0) {
                                  setDialogState(() => formError =
                                      'La date d expiration doit suivre la date de delivrance.');
                                  return;
                                }
                                setDialogState(() {
                                  submitting = true;
                                  formError = null;
                                });
                                try {
                                  if (selectedFile?.bytes != null) {
                                    final data = FormData.fromMap({
                                      'type_document': type,
                                      'numero_document':
                                          number.text.trim().isEmpty
                                              ? null
                                              : number.text.trim(),
                                      'date_delivrance': deliveryDate,
                                      'date_expiration': expirationDate,
                                      'is_valid': true,
                                      'file': MultipartFile.fromBytes(
                                          selectedFile!.bytes!,
                                          filename: selectedFile!.name)
                                    });
                                    await widget.apiClient.post(
                                        '/vehicules/$vehicleId/documents/upload',
                                        data: data,
                                        options: Options(
                                            contentType:
                                                'multipart/form-data'));
                                  } else {
                                    await widget.apiClient.post(
                                        '/vehicules/$vehicleId/documents',
                                        data: {
                                          'type_document': type,
                                          'numero_document':
                                              number.text.trim().isEmpty
                                                  ? null
                                                  : number.text.trim(),
                                          'date_delivrance': deliveryDate,
                                          'date_expiration': expirationDate
                                        });
                                  }
                                  if (dialogContext.mounted)
                                    Navigator.pop(dialogContext);
                                } catch (error) {
                                  setDialogState(() {
                                    submitting = false;
                                    formError = userError(
                                        error,
                                        'Impossible d ajouter le document.',
                                        'MOBILE_DOCUMENT_ADD_ERROR');
                                  });
                                }
                              },
                        child: submitting
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2))
                            : const Text('Enregistrer'))
                  ],
                )),
      );
    } finally {
      number.dispose();
      delivery.dispose();
      expiration.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    final canCreate = _can('VEHICULE_CREATE');
    final canUpdate = _can('VEHICULE_UPDATE');
    final canDelete = _can('VEHICULE_DELETE');
    return Scaffold(
      appBar: AppBar(title: Text('Vehicules ($_total)'), actions: [
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
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
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
              padding: const EdgeInsets.all(16),
              child: ErrorBanner(message: _error!)),
        Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _vehicules.isEmpty
                    ? const Center(child: Text('Aucun vehicule enregistre.'))
                    : RefreshIndicator(
                        onRefresh: _load,
                        child: ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _vehicules.length,
                            itemBuilder: (context, index) {
                              final item = _vehicules[index];
                              final active = item['is_active'] == true;
                              return Card(
                                  color: AppTheme.surface,
                                  child: ListTile(
                                      onTap: () =>
                                          _showDetails(item['id'] as int),
                                      leading: CircleAvatar(
                                          child:
                                              const Icon(Icons.directions_bus)),
                                      title: Text(
                                          item['immatriculation'] as String? ??
                                              '-'),
                                      subtitle: Text(
                                          '${_modeleLabel(item['id_modele'] as int?)} - ${_cooperativeLabel(item['id_cooperative'] as int?)}\n${item['nombre_places'] ?? '-'} places - ${item['etat'] ?? '-'}'),
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
                                                      child: Text(active
                                                          ? 'Desactiver'
                                                          : 'Activer')),
                                                if (canUpdate)
                                                  const PopupMenuItem(
                                                      value: 'edit',
                                                      child: Text('Modifier')),
                                                if (canDelete)
                                                  const PopupMenuItem(
                                                      value: 'delete',
                                                      child: Text('Supprimer'))
                                              ])));
                            }))),
        if (!_isLoading && _pages > 1)
          Padding(
              padding: const EdgeInsets.all(12),
              child:
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
              ]))
      ])),
    );
  }
}
