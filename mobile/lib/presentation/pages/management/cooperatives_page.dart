import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../controllers/cooperative/cooperative_controller.dart';
import '../../widgets/common/custom_button.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/error_banner.dart';

class CooperativesPage extends ConsumerStatefulWidget {
  const CooperativesPage({super.key});

  @override
  ConsumerState<CooperativesPage> createState() => _CooperativesPageState();
}

class _CooperativesPageState extends ConsumerState<CooperativesPage> {
  final _formKey = GlobalKey<FormState>();
  final _nomController = TextEditingController();
  final _sigleController = TextEditingController();
  final _agrementController = TextEditingController();
  final _villeController = TextEditingController();
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();

  @override
  void dispose() {
    _nomController.dispose();
    _sigleController.dispose();
    _agrementController.dispose();
    _villeController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  void _showAddCooperativeModal() {
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
                        'Ajouter une Coopérative',
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
                    labelText: 'Nom de la coopérative',
                    prefixIcon: Icons.business,
                    validator: (v) => v == null || v.isEmpty ? 'Nom requis' : null,
                  ),
                  const SizedBox(height: 12),
                  CustomTextField(
                    controller: _sigleController,
                    labelText: 'Sigle / Abréviation (ex: Cotisse)',
                    prefixIcon: Icons.short_text,
                  ),
                  const SizedBox(height: 12),
                  CustomTextField(
                    controller: _agrementController,
                    labelText: 'N° d\'Agrément / NIF',
                    prefixIcon: Icons.verified_outlined,
                  ),
                  const SizedBox(height: 12),
                  CustomTextField(
                    controller: _villeController,
                    labelText: 'Ville d\'attache',
                    prefixIcon: Icons.map_outlined,
                  ),
                  const SizedBox(height: 12),
                  CustomTextField(
                    controller: _phoneController,
                    labelText: 'Téléphone',
                    prefixIcon: Icons.phone_outlined,
                  ),
                  const SizedBox(height: 12),
                  CustomTextField(
                    controller: _emailController,
                    labelText: 'Email de contact',
                    prefixIcon: Icons.email_outlined,
                    keyboardType: TextInputType.emailAddress,
                  ),
                  const SizedBox(height: 20),
                  CustomButton(
                    text: 'Créer la coopérative',
                    onPressed: () async {
                      if (_formKey.currentState?.validate() ?? false) {
                        final navigator = Navigator.of(modalContext);
                        final success = await ref.read(cooperativeControllerProvider.notifier).createCooperative(
                              nom: _nomController.text,
                              sigle: _sigleController.text,
                              numeroAgrement: _agrementController.text,
                              ville: _villeController.text,
                              telephone: _phoneController.text,
                              email: _emailController.text,
                            );
                        if (success) {
                          navigator.pop();
                          _nomController.clear();
                          _sigleController.clear();
                          _agrementController.clear();
                          _villeController.clear();
                          _phoneController.clear();
                          _emailController.clear();
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
    final state = ref.watch(cooperativeControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Gestion des Coopératives'),
        backgroundColor: const Color(0xFF0F172A),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(cooperativeControllerProvider.notifier).loadCooperatives(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddCooperativeModal,
        backgroundColor: const Color(0xFF10B981),
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text('Nouvelle Coopérative', style: TextStyle(color: Colors.white)),
      ),
      body: Container(
        color: const Color(0xFF0F172A),
        child: SafeArea(
          child: Column(
            children: [
              if (state.error != null) ...[
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: ErrorBanner(message: state.error!),
                ),
              ],
              Expanded(
                child: state.isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : state.cooperatives.isEmpty
                        ? const Center(
                            child: Text(
                              'Aucune coopérative enregistrée.',
                              style: TextStyle(color: Colors.white54, fontSize: 16),
                            ),
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: state.cooperatives.length,
                            itemBuilder: (context, index) {
                              final item = state.cooperatives[index];
                              return Card(
                                color: const Color(0xFF1E293B),
                                margin: const EdgeInsets.only(bottom: 12),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                                child: ListTile(
                                  contentPadding: const EdgeInsets.all(16),
                                  leading: CircleAvatar(
                                    backgroundColor: const Color(0xFF60A5FA).withValues(alpha: 0.2),
                                    child: Text(
                                      (item.sigle ?? item.nom)[0].toUpperCase(),
                                      style: const TextStyle(
                                        color: Color(0xFF60A5FA),
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                  title: Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          item.nom,
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                            color: Colors.white,
                                            fontSize: 16,
                                          ),
                                        ),
                                      ),
                                      if (item.sigle != null) ...[
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: Colors.white10,
                                            borderRadius: BorderRadius.circular(6),
                                          ),
                                          child: Text(
                                            item.sigle!,
                                            style: const TextStyle(color: Colors.white70, fontSize: 12),
                                          ),
                                        ),
                                      ],
                                    ],
                                  ),
                                  subtitle: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const SizedBox(height: 4),
                                      if (item.ville != null)
                                        Text('Ville: ${item.ville}', style: TextStyle(color: Colors.grey.shade400)),
                                      if (item.telephone != null || item.email != null)
                                        Text(
                                          'Contact: ${item.telephone ?? item.email}',
                                          style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
                                        ),
                                    ],
                                  ),
                                  trailing: IconButton(
                                    icon: Icon(
                                      item.isActive ? Icons.toggle_on : Icons.toggle_off,
                                      color: item.isActive ? const Color(0xFF10B981) : Colors.grey,
                                      size: 36,
                                    ),
                                    onPressed: () {
                                      ref.read(cooperativeControllerProvider.notifier).toggleCooperativeStatus(item.id);
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
