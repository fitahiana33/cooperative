import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../controllers/auth/auth_controller.dart';
import '../../widgets/common/error_banner.dart';

/// Personal information and password, for every role.
class ProfilePage extends ConsumerStatefulWidget {
  const ProfilePage({super.key});

  @override
  ConsumerState<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends ConsumerState<ProfilePage> {
  final _profileKey = GlobalKey<FormState>();
  final _passwordKey = GlobalKey<FormState>();
  late final TextEditingController _firstName;
  late final TextEditingController _name;
  late final TextEditingController _phone;
  late final TextEditingController _address;
  final _currentPassword = TextEditingController();
  final _newPassword = TextEditingController();
  bool _saving = false;
  bool _changingPassword = false;
  String? _profileError;
  String? _passwordError;

  @override
  void initState() {
    super.initState();
    final user = ref.read(authControllerProvider).user;
    _firstName = TextEditingController(text: user?.firstName ?? '');
    _name = TextEditingController(text: user?.name ?? '');
    _phone = TextEditingController(text: user?.telephone ?? '');
    _address = TextEditingController(text: user?.address ?? '');
  }

  @override
  void dispose() {
    for (final controller in [_firstName, _name, _phone, _address, _currentPassword, _newPassword]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _saveProfile() async {
    if (!(_profileKey.currentState?.validate() ?? false)) return;
    setState(() { _saving = true; _profileError = null; });
    final error = await ref.read(authControllerProvider.notifier).updateProfile({
      'first_name': _firstName.text.trim(),
      'name': _name.text.trim(),
      'telephone': _phone.text.trim().isEmpty ? null : _phone.text.trim(),
      'address': _address.text.trim().isEmpty ? null : _address.text.trim(),
    });
    if (!mounted) return;
    setState(() { _saving = false; _profileError = error; });
    if (error == null) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Profil enregistré.')));
  }

  Future<void> _changePassword() async {
    if (!(_passwordKey.currentState?.validate() ?? false)) return;
    setState(() { _changingPassword = true; _passwordError = null; });
    final error = await ref.read(authControllerProvider.notifier).changePassword(
          currentPassword: _currentPassword.text,
          newPassword: _newPassword.text,
        );
    if (!mounted) return;
    // On success the app returns to the login screen (every session ends).
    setState(() { _changingPassword = false; _passwordError = error; });
  }

  String? _required(String? value) => (value ?? '').trim().isEmpty ? 'Champ obligatoire.' : null;

  String? _strongPassword(String? value) {
    final text = value ?? '';
    if (text.length < 8) return 'Au moins 8 caractères.';
    if (!text.contains(RegExp(r'[A-Za-zÀ-ÿ]')) || !text.contains(RegExp(r'\d'))) return 'Au moins une lettre et un chiffre.';
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authControllerProvider).user;
    return Scaffold(
      appBar: AppBar(title: const Text('Mon profil')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Text(user?.email ?? '', style: const TextStyle(color: Colors.white70)),
        const SizedBox(height: 16),
        Form(
          key: _profileKey,
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            const Text('Informations personnelles', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
            TextFormField(controller: _firstName, decoration: const InputDecoration(labelText: 'Prénom *'), validator: _required),
            TextFormField(controller: _name, decoration: const InputDecoration(labelText: 'Nom *'), validator: _required),
            TextFormField(controller: _phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Téléphone')),
            TextFormField(controller: _address, decoration: const InputDecoration(labelText: 'Adresse')),
            if (_profileError != null) ...[const SizedBox(height: 12), ErrorBanner(message: _profileError!)],
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _saving ? null : _saveProfile, child: Text(_saving ? 'Enregistrement…' : 'Enregistrer')),
          ]),
        ),
        const SizedBox(height: 32),
        Form(
          key: _passwordKey,
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            const Text('Mot de passe', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Après le changement, vous devrez vous reconnecter sur tous vos appareils.', style: TextStyle(color: Colors.white60, fontSize: 12)),
            TextFormField(controller: _currentPassword, obscureText: true, decoration: const InputDecoration(labelText: 'Mot de passe actuel *'), validator: _required),
            TextFormField(controller: _newPassword, obscureText: true, decoration: const InputDecoration(labelText: 'Nouveau mot de passe *'), validator: _strongPassword),
            if (_passwordError != null) ...[const SizedBox(height: 12), ErrorBanner(message: _passwordError!)],
            const SizedBox(height: 12),
            OutlinedButton(onPressed: _changingPassword ? null : _changePassword, child: Text(_changingPassword ? 'Modification…' : 'Changer le mot de passe')),
          ]),
        ),
      ]),
    );
  }
}
