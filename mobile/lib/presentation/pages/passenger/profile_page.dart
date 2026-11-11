import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../../../core/errors/user_error.dart';
import '../../widgets/common/user_avatar.dart';
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
  bool _changingPhoto = false;
  String? _photoError;
  bool get _busy => _saving || _changingPassword || _changingPhoto;
  final _confirmation = TextEditingController();
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
    for (final controller in [
      _firstName,
      _name,
      _phone,
      _address,
      _currentPassword,
      _newPassword,
      _confirmation
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _saveProfile() async {
    if (_busy || !(_profileKey.currentState?.validate() ?? false)) return;
    setState(() {
      _saving = true;
      _profileError = null;
    });
    final error =
        await ref.read(authControllerProvider.notifier).updateProfile({
      'first_name': _firstName.text.trim(),
      'name': _name.text.trim(),
      'telephone': _phone.text.trim().isEmpty ? null : _phone.text.trim(),
      'address': _address.text.trim().isEmpty ? null : _address.text.trim(),
    });
    if (!mounted) return;
    setState(() {
      _saving = false;
      _profileError = error;
    });
    if (error == null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Profil enregistré.')));
    }
  }

  Future<void> _changePassword() async {
    if (_busy || !(_passwordKey.currentState?.validate() ?? false)) return;
    setState(() {
      _changingPassword = true;
      _passwordError = null;
    });
    final error =
        await ref.read(authControllerProvider.notifier).changePassword(
              currentPassword: _currentPassword.text,
              newPassword: _newPassword.text,
            );
    if (!mounted) return;
    // On success the app returns to the login screen (every session ends).
    setState(() {
      _changingPassword = false;
      _passwordError = error;
    });
  }

  Future<void> _changePhoto({bool remove = false}) async {
    if (_busy) return;
    setState(() {
      _changingPhoto = true;
      _photoError = null;
    });
    try {
      String? error;
      if (remove) {
        error = await ref.read(authControllerProvider.notifier).changePhoto();
      } else {
        final file = await FilePicker.pickFile(
            type: FileType.custom,
            allowedExtensions: ['jpg', 'jpeg', 'png', 'webp']);
        if (!mounted || file == null) return;
        final size = await file.length();
        if (!mounted) return;
        if (size != null && size > 4 * 1024 * 1024) {
          setState(() {
            _photoError =
                'Choisissez une image JPEG, PNG ou WebP de 4 Mo maximum.';
          });
          return;
        }
        final bytes = BytesBuilder(copy: false);
        await for (final chunk in file.readAsByteStream()) {
          if (!mounted) return;
          if (bytes.length + chunk.length > 4 * 1024 * 1024) {
            setState(() {
              _photoError = 'La photo doit faire au maximum 4 Mo.';
            });
            return;
          }
          bytes.add(chunk);
        }
        if (!mounted) return;
        error = await ref
            .read(authControllerProvider.notifier)
            .changePhoto(bytes: bytes.takeBytes(), filename: file.name);
      }
      if (!mounted) return;
      setState(() {
        _photoError = error;
      });
      if (error == null) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(remove ? 'Photo supprimée.' : 'Photo mise à jour.')));
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _photoError = userError(error, 'Impossible de sélectionner la photo.',
              'PHOTO_PICKER_ERROR');
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _changingPhoto = false;
        });
      }
    }
  }

  String? _required(String? value) =>
      (value ?? '').trim().isEmpty ? 'Champ obligatoire.' : null;

  String? _strongPassword(String? value) {
    final text = value ?? '';
    if (text.length < 8) return 'Au moins 8 caractères.';
    if (!text.contains(RegExp(r'[A-Za-zÀ-ÿ]')) ||
        !text.contains(RegExp(r'\d'))) {
      return 'Au moins une lettre et un chiffre.';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authControllerProvider).user;
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
            title: const Text('Mon profil'),
            bottom: const TabBar(
                tabs: [Tab(text: 'Informations'), Tab(text: 'Sécurité')])),
        body: TabBarView(children: [
          ListView(
              key: const PageStorageKey('profile-information'),
              padding: const EdgeInsets.all(20),
              children: [
                if (user != null)
                  Card(
                      child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Column(children: [
                            UserAvatar(user: user, radius: 44),
                            const SizedBox(height: 12),
                            Text(user.fullName,
                                textAlign: TextAlign.center,
                                style: Theme.of(context).textTheme.titleLarge),
                            const SizedBox(height: 4),
                            Text(user.email, textAlign: TextAlign.center),
                            const SizedBox(height: 12),
                            Wrap(
                                alignment: WrapAlignment.center,
                                spacing: 8,
                                children: [
                                  OutlinedButton.icon(
                                      onPressed:
                                          _busy ? null : () => _changePhoto(),
                                      icon: const Icon(
                                          Icons.add_a_photo_outlined),
                                      label: Text(_changingPhoto
                                          ? 'Traitement…'
                                          : user.photoVersion == null
                                              ? 'Ajouter une photo'
                                              : 'Changer la photo')),
                                  if (user.photoVersion != null)
                                    TextButton(
                                        onPressed: _busy
                                            ? null
                                            : () => _changePhoto(remove: true),
                                        child:
                                            const Text('Supprimer la photo')),
                                ]),
                            const Text('JPEG, PNG ou WebP · 4 Mo maximum',
                                style: TextStyle(fontSize: 12)),
                            if (_photoError != null)
                              ErrorBanner(message: _photoError!),
                          ]))),
                const SizedBox(height: 16),
                Form(
                    key: _profileKey,
                    child: AutofillGroup(
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                          const Text('Informations personnelles',
                              style: TextStyle(
                                  fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 12),
                          TextFormField(
                              controller: _firstName,
                              enabled: !_busy,
                              autofillHints: const [AutofillHints.givenName],
                              decoration:
                                  const InputDecoration(labelText: 'Prénom *'),
                              validator: _required),
                          const SizedBox(height: 12),
                          TextFormField(
                              controller: _name,
                              enabled: !_busy,
                              autofillHints: const [AutofillHints.familyName],
                              decoration:
                                  const InputDecoration(labelText: 'Nom *'),
                              validator: _required),
                          const SizedBox(height: 12),
                          TextFormField(
                              controller: _phone,
                              enabled: !_busy,
                              keyboardType: TextInputType.phone,
                              autofillHints: const [
                                AutofillHints.telephoneNumber
                              ],
                              decoration: const InputDecoration(
                                  labelText: 'Téléphone')),
                          const SizedBox(height: 12),
                          TextFormField(
                              controller: _address,
                              enabled: !_busy,
                              autofillHints: const [
                                AutofillHints.fullStreetAddress
                              ],
                              decoration:
                                  const InputDecoration(labelText: 'Adresse')),
                          const SizedBox(height: 12),
                          const Text(
                              'Pour modifier votre adresse email de connexion, contactez votre administrateur.',
                              style: TextStyle(fontSize: 12)),
                          if (_profileError != null) ...[
                            const SizedBox(height: 12),
                            ErrorBanner(message: _profileError!)
                          ],
                          const SizedBox(height: 20),
                          FilledButton(
                              onPressed: _busy ? null : _saveProfile,
                              child: Text(_saving
                                  ? 'Enregistrement…'
                                  : 'Enregistrer les modifications')),
                        ]))),
              ]),
          ListView(
              key: const PageStorageKey('profile-security'),
              padding: const EdgeInsets.all(20),
              children: [
                Form(
                    key: _passwordKey,
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const Text('Changer mon mot de passe',
                              style: TextStyle(
                                  fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 12),
                          const Text(
                              'Après le changement, reconnectez-vous avec votre nouveau mot de passe sur chacun de vos appareils.'),
                          const SizedBox(height: 20),
                          TextFormField(
                              controller: _currentPassword,
                              enabled: !_busy,
                              obscureText: true,
                              autofillHints: const [AutofillHints.password],
                              decoration: const InputDecoration(
                                  labelText: 'Mot de passe actuel *'),
                              validator: _required),
                          const SizedBox(height: 16),
                          TextFormField(
                              controller: _newPassword,
                              enabled: !_busy,
                              obscureText: true,
                              autofillHints: const [AutofillHints.newPassword],
                              decoration: const InputDecoration(
                                  labelText: 'Nouveau mot de passe *',
                                  helperText:
                                      '8 caractères minimum, une lettre et un chiffre'),
                              validator: _strongPassword),
                          const SizedBox(height: 16),
                          TextFormField(
                              controller: _confirmation,
                              enabled: !_busy,
                              obscureText: true,
                              autofillHints: const [AutofillHints.newPassword],
                              decoration: const InputDecoration(
                                  labelText:
                                      'Confirmer le nouveau mot de passe *'),
                              validator: (value) => value != _newPassword.text
                                  ? 'Les mots de passe doivent être identiques.'
                                  : _required(value)),
                          if (_passwordError != null) ...[
                            const SizedBox(height: 12),
                            ErrorBanner(message: _passwordError!)
                          ],
                          const SizedBox(height: 20),
                          FilledButton(
                              onPressed: _busy ? null : _changePassword,
                              child: Text(_changingPassword
                                  ? 'Modification…'
                                  : 'Modifier le mot de passe')),
                        ])),
              ]),
        ]),
      ),
    );
  }
}
