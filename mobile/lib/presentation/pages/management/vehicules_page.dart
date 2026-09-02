import 'package:flutter/material.dart';
import '../../../data/repositories/vehicule/vehicule_repository_impl.dart';
import '../../../core/network/api_client.dart';
import '../../../domain/entities/vehicule/vehicule.dart';

class VehiculesPage extends StatefulWidget {
  final ApiClient apiClient;

  const VehiculesPage({super.key, required this.apiClient});

  @override
  State<VehiculesPage> createState() => _VehiculesPageState();
}

class _VehiculesPageState extends State<VehiculesPage> {
  late final VehiculeRepositoryImpl _repository;
  List<VehiculeEntity> _vehicules = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _repository = VehiculeRepositoryImpl(widget.apiClient);
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final items = await _repository.fetchVehicules();
      setState(() {
        _vehicules = items;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Impossible de charger la liste des véhicules.';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Gestion des Véhicules'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: ListView.builder(
                    itemCount: _vehicules.length,
                    itemBuilder: (context, index) {
                      final item = _vehicules[index];
                      return Card(
                        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        child: ListTile(
                          leading: const CircleAvatar(
                            child: Icon(Icons.directions_bus),
                          ),
                          title: Text(
                            item.immatriculation,
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Text('${item.nombrePlaces} places • Etat: ${item.etat}'),
                          trailing: Chip(
                            label: Text(item.disponibilite ? 'Disponible' : 'Occupé'),
                            backgroundColor: item.disponibilite ? Colors.green.shade100 : Colors.orange.shade100,
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
