import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/error_banner.dart';

class BoardingPage extends StatefulWidget {
  final ApiClient apiClient;
  const BoardingPage({super.key, required this.apiClient});
  @override
  State<BoardingPage> createState() => _BoardingPageState();
}

class _BoardingPageState extends State<BoardingPage> {
  final _code = TextEditingController();
  bool _busy = false;
  String? _error;
  Map<String, dynamic>? _result;

  @override
  void dispose() { _code.dispose(); super.dispose(); }

  Future<void> _control() async {
    if (_code.text.trim().length < 3) { setState(() => _error = 'Saisissez un numéro de billet ou un QR Code.'); return; }
    setState(() { _busy = true; _error = null; _result = null; });
    try { final response = await widget.apiClient.post('/embarquement/controle', data: {'code': _code.text.trim()}); if (mounted) setState(() => _result = Map<String, dynamic>.from(response.data as Map)); }
    catch (exception) { if (mounted) setState(() => _error = userError(exception, 'Billet non autorisé à l’embarquement.', 'MOBILE_BOARDING_ERROR')); }
    finally { if (mounted) setState(() => _busy = false); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('Contrôle embarquement')), body: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [const Text('Rechercher ou scanner un billet', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)), const SizedBox(height: 16), TextField(controller: _code, decoration: const InputDecoration(labelText: 'Numéro billet ou QR Code')), const SizedBox(height: 12), SizedBox(width: double.infinity, child: ElevatedButton(onPressed: _busy ? null : _control, child: Text(_busy ? 'Contrôle…' : 'Contrôler'))), if (_error != null) ErrorBanner(message: _error!), if (_result != null) Card(color: _result!['statut'] == 'VALIDE' ? Colors.green.shade50 : AppTheme.surface, child: ListTile(leading: Icon(_result!['statut'] == 'VALIDE' ? Icons.check_circle : Icons.cancel), title: Text(_result!['statut'] == 'VALIDE' ? 'Embarquement enregistré' : 'Embarquement refusé'), subtitle: Text(_result!['motif_refus'] as String? ?? 'Le billet a été validé.')))]));
}
