import 'package:flutter/material.dart';
import '../../../data/repositories/chauffeur/chauffeur_repository_impl.dart';
import '../../../core/network/api_client.dart';
import '../../../domain/entities/chauffeur/chauffeur.dart';

class ChauffeursPage extends StatefulWidget {
  final ApiClient apiClient;

  const ChauffeursPage({super.key, required this.apiClient});

  @override
  State<ChauffeursPage> createState() => _ChauffeursPageState();
}

class _ChauffeursPageState extends State<ChauffeursPage> {
  late final ChauffeurRepositoryImpl _repository;
  List<ChauffeurEntity> _chauffeurs = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _repository = ChauffeurRepositoryImpl(widget.apiClient);
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final items = await _repository.fetchChauffeurs();
      setState(() {
        _chauffeurs = items;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Impossible de charger la liste des chauffeurs.';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Gestion des Chauffeurs'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: ListView.builder(
                    itemCount: _chauffeurs.length,
                    itemBuilder: (context, index) {
                      final item = _chauffeurs[index];
                      return Card(
                        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        child: ListTile(
                          leading: const CircleAvatar(
                            child: Icon(Icons.badge),
                          ),
                          title: Text(
                            'Permis N° ${item.numeroPermis}',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Text('Catégorie: ${item.categoriePermis} • Exp: ${item.dateExpirationPermis}'),
                          trailing: Chip(
                            label: Text(item.disponibilite ? 'Disponible' : 'En trajet'),
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
