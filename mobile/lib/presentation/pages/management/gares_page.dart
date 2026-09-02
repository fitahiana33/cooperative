import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../controllers/gare/gare_controller.dart';
import '../../widgets/common/custom_button.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/error_banner.dart';

class GaresPage extends ConsumerStatefulWidget {
  const GaresPage({super.key});

  @override
  ConsumerState<GaresPage> createState() => _GaresPageState();
}

class _GaresPageState extends ConsumerState<GaresPage> {
  final _formKey = GlobalKey<FormState>();
  final _nomController = TextEditingController();
  final _villeController = TextEditingController();
  final _adresseController = TextEditingController();
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _latController = TextEditingController();
  final _longController = TextEditingController();

  @override
  void dispose() {
    _nomController.dispose();
    _villeController.dispose();
    _adresseController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _latController.dispose();
    _longController.dispose();
    super.dispose();
  }

  void _showAddGareModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E293B),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (modalContext) {
        return Padding(
          padding: EdgeInsets.only(
            top: 24,
            left: 24,
            right: 24,
            bottom: MediaQuery.of(modalContext).viewInsets.bottom + 24,
          ),
          child: SingleChildScrollView(
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Ajouter une Gare',
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Colors.white70),
                        onPressed: () => Navigator.pop(modalContext),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  CustomTextField(
                    controller: _nomController,
                    labelText: 'Nom de la gare',
                    prefixIcon: Icons.location_city_outlined,
                    validator: (v) => v == null || v.isEmpty ? 'Nom requis' : null,
                  ),
                  const SizedBox(height: 12),
                  CustomTextField(
                    controller: _villeController,
                    labelText: 'Ville',
                    prefixIcon: Icons.map_outlined,
                    validator: (v) => v == null || v.isEmpty ? 'Ville requise' : null,
                  ),
                  const SizedBox(height: 12),
                  CustomTextField(
                    controller: _adresseController,
                    labelText: 'Adresse complète',
                    prefixIcon: Icons.place_outlined,
                    validator: (v) => v == null || v.isEmpty ? 'Adresse requise' : null,
                  ),
                  const SizedBox(height: 12),
                  CustomTextField(
                    controller: _phoneController,
                    labelText: 'Téléphone (optionnel)',
                    prefixIcon: Icons.phone_outlined,
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: CustomTextField(
                          controller: _latController,
                          labelText: 'Latitude (GPS)',
                          prefixIcon: Icons.my_location,
                          keyboardType: TextInputType.number,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: CustomTextField(
                          controller: _longController,
                          labelText: 'Longitude (GPS)',
                          prefixIcon: Icons.my_location,
                          keyboardType: TextInputType.number,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  CustomButton(
                    text: 'Créer la gare',
                    onPressed: () async {
                      if (_formKey.currentState?.validate() ?? false) {
                        final navigator = Navigator.of(modalContext);
                        final success = await ref.read(gareControllerProvider.notifier).createGare(
                              nom: _nomController.text,
                              ville: _villeController.text,
                              adresse: _adresseController.text,
                              telephone: _phoneController.text,
                              email: _emailController.text,
                              latitude: double.tryParse(_latController.text),
                              longitude: double.tryParse(_longController.text),
                            );
                        if (success) {
                          navigator.pop();
                          _nomController.clear();
                          _villeController.clear();
                          _adresseController.clear();
                          _phoneController.clear();
                          _emailController.clear();
                          _latController.clear();
                          _longController.clear();
                        }
                      }
                    },
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final gareState = ref.watch(gareControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Gestion des Gares'),
        backgroundColor: const Color(0xFF0F172A),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(gareControllerProvider.notifier).loadGares(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddGareModal,
        backgroundColor: const Color(0xFF3B82F6),
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text('Nouvelle Gare', style: TextStyle(color: Colors.white)),
      ),
      body: Container(
        color: const Color(0xFF0F172A),
        child: SafeArea(
          child: Column(
            children: [
              if (gareState.error != null) ...[
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: ErrorBanner(message: gareState.error!),
                ),
              ],
              Expanded(
                child: gareState.isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : gareState.gares.isEmpty
                        ? const Center(
                            child: Text(
                              'Aucune gare enregistrée.',
                              style: TextStyle(color: Colors.white54, fontSize: 16),
                            ),
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: gareState.gares.length,
                            itemBuilder: (context, index) {
                              final item = gareState.gares[index];
                              return Card(
                                color: const Color(0xFF1E293B),
                                margin: const EdgeInsets.only(bottom: 12),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                                child: ListTile(
                                  contentPadding: const EdgeInsets.all(16),
                                  leading: CircleAvatar(
                                    backgroundColor: item.isActive
                                        ? const Color(0xFF10B981).withValues(alpha: 0.2)
                                        : Colors.red.withValues(alpha: 0.2),
                                    child: Icon(
                                      Icons.location_city,
                                      color: item.isActive ? const Color(0xFF10B981) : Colors.red,
                                    ),
                                  ),
                                  title: Text(
                                    item.nom,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Colors.white,
                                      fontSize: 16,
                                    ),
                                  ),
                                  subtitle: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const SizedBox(height: 4),
                                      Text(
                                        '📍 ${item.ville} - ${item.adresse}',
                                        style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
                                      ),
                                      if (item.latitude != null && item.longitude != null) ...[
                                        const SizedBox(height: 2),
                                        Text(
                                          'GPS: ${item.latitude!.toStringAsFixed(4)}, ${item.longitude!.toStringAsFixed(4)}',
                                          style: const TextStyle(color: Color(0xFF60A5FA), fontSize: 12),
                                        ),
                                      ],
                                    ],
                                  ),
                                  trailing: IconButton(
                                    icon: Icon(
                                      item.isActive ? Icons.toggle_on : Icons.toggle_off,
                                      color: item.isActive ? const Color(0xFF10B981) : Colors.grey,
                                      size: 36,
                                    ),
                                    onPressed: () {
                                      ref.read(gareControllerProvider.notifier).toggleGareStatus(item.id);
                                    },
                                  ),
                                ),
                              );
                            },
                          ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
