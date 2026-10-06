import 'package:flutter/material.dart';

import '../../../core/errors/user_error.dart';
import '../../../domain/services/driver_pointage/driver_pointage_service.dart';

class DriverPointagePage extends StatefulWidget {
  final DriverPointageService pointageService;
  const DriverPointagePage({super.key, required this.pointageService});

  @override
  State<DriverPointagePage> createState() => _DriverPointagePageState();
}

class _DriverPointagePageState extends State<DriverPointagePage> {
  List<Map<String, dynamic>> _departs = [];
  bool _loading = true;
  int? _busyId;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final values = await widget.pointageService.listMyDepartures();
      if (mounted) setState(() => _departs = values);
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'Impossible de charger vos departs.', 'DRIVER_DEPARTS_ERROR'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _pointage(Map<String, dynamic> depart, String type) async {
    final id = depart['id'] as int;
    setState(() => _busyId = id);
    try {
      await widget.pointageService.pointage(id, type);
      await _load();
    } catch (exception) {
      if (mounted) setState(() => _error = userError(exception, 'Pointage impossible.', 'DRIVER_POINTAGE_ERROR'));
    } finally {
      if (mounted) setState(() => _busyId = null);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Pointage chauffeur')),
        body: RefreshIndicator(
          onRefresh: _load,
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    if (_error != null) Padding(padding: const EdgeInsets.only(bottom: 12), child: Text(_error!, style: const TextStyle(color: Colors.redAccent))),
                    if (_departs.isEmpty) const Text('Aucun depart affecte.', style: TextStyle(color: Colors.white70)),
                    ..._departs.map(_departureCard),
                  ],
                ),
        ),
      );

  Widget _departureCard(Map<String, dynamic> depart) {
    final id = depart['id'] as int;
    final status = depart['statut'] as String? ?? '';
    final route = depart['itineraire'] is Map ? Map<String, dynamic>.from(depart['itineraire'] as Map) : <String, dynamic>{};
    final from = (route['destination_depart'] as Map?)?['nom'] ?? 'Depart';
    final to = (route['destination_arrivee'] as Map?)?['nom'] ?? 'Arrivee';
    final canDepart = ['PROGRAMME', 'EMBARQUEMENT', 'RETARDE'].contains(status);
    final canArrive = status == 'PARTI';
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('$from -> $to', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17)),
          const SizedBox(height: 6),
          Text('${depart['date_depart'] ?? '-'} a ${depart['heure_depart'] ?? '-'}  |  $status'),
          const SizedBox(height: 14),
          Row(children: [
            Expanded(child: ElevatedButton(onPressed: canDepart && _busyId != id ? () => _pointage(depart, 'DEPART') : null, child: const Text('Pointer le depart'))),
            const SizedBox(width: 8),
            Expanded(child: OutlinedButton(onPressed: canArrive && _busyId != id ? () => _pointage(depart, 'ARRIVEE') : null, child: const Text("Pointer l'arrivee"))),
          ]),
        ]),
      ),
    );
  }
}
