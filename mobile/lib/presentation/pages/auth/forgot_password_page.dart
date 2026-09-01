import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/utils/validators.dart';
import '../../controllers/auth/auth_controller.dart';
import '../../widgets/auth/auth_form_card.dart';
import '../../widgets/common/custom_button.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/error_banner.dart';

class ForgotPasswordPage extends ConsumerStatefulWidget {
  const ForgotPasswordPage({super.key});

  @override
  ConsumerState<ForgotPasswordPage> createState() => _ForgotPasswordPageState();
}

class _ForgotPasswordPageState extends ConsumerState<ForgotPasswordPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _tokenController = TextEditingController();
  final _newPasswordController = TextEditingController();

  bool _isResetMode = false;
  bool _isLoading = false;
  bool _obscureNewPassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _tokenController.dispose();
    _newPasswordController.dispose();
    super.dispose();
  }

  void _requestResetToken() async {
    if (_formKey.currentState?.validate() ?? false) {
      setState(() => _isLoading = true);
      final success = await ref
          .read(authControllerProvider.notifier)
          .forgotPassword(_emailController.text);
      setState(() => _isLoading = false);
      if (success && mounted) {
        setState(() => _isResetMode = true);
      }
    }
  }

  void _submitNewPassword() async {
    if (_tokenController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez saisir votre token de réinitialisation')),
      );
      return;
    }
    if (_newPasswordController.text.length < 8) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Le nouveau mot de passe doit contenir au moins 8 caractères')),
      );
      return;
    }

    setState(() => _isLoading = true);
    final success = await ref.read(authControllerProvider.notifier).resetPassword(
          token: _tokenController.text,
          newPassword: _newPasswordController.text,
        );
    setState(() => _isLoading = false);

    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Mot de passe réinitialisé avec succès! Connectez-vous.'),
          backgroundColor: Color(0xFF10B981),
        ),
      );
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF0F172A),
              Color(0xFF1E293B),
              Color(0xFF334155),
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white),
                      onPressed: () => Navigator.pop(context),
                    ),
                    const Text(
                      'Mot de passe oublié',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
                  child: AuthFormCard(
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          if (authState.errorMessage != null) ...[
                            ErrorBanner(message: authState.errorMessage!),
                            const SizedBox(height: 16),
                          ],
                          if (authState.infoMessage != null) ...[
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: const Color(0xFF10B981).withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.4)),
                              ),
                              child: Text(
                                authState.infoMessage!,
                                style: const TextStyle(color: Color(0xFFA7F3D0), fontSize: 13),
                              ),
                            ),
                            const SizedBox(height: 16),
                          ],

                          if (!_isResetMode) ...[
                            const Text(
                              'Entrez votre adresse email pour recevoir des instructions et réinitialiser votre mot de passe.',
                              style: TextStyle(color: Colors.white70, fontSize: 14),
                            ),
                            const SizedBox(height: 20),
                            CustomTextField(
                              controller: _emailController,
                              labelText: 'Adresse Email',
                              prefixIcon: Icons.email_outlined,
                              keyboardType: TextInputType.emailAddress,
                              validator: Validators.validateEmail,
                            ),
                            const SizedBox(height: 24),
                            CustomButton(
                              text: 'Envoyer les instructions',
                              isLoading: _isLoading,
                              onPressed: _requestResetToken,
                            ),
                          ] else ...[
                            const Text(
                              'Un code de réinitialisation a été généré. Entrez le code et votre nouveau mot de passe ci-dessous.',
                              style: TextStyle(color: Colors.white70, fontSize: 14),
                            ),
                            const SizedBox(height: 20),
                            CustomTextField(
                              controller: _tokenController,
                              labelText: 'Token de réinitialisation',
                              prefixIcon: Icons.vpn_key_outlined,
                            ),
                            const SizedBox(height: 16),
                            CustomTextField(
                              controller: _newPasswordController,
                              labelText: 'Nouveau mot de passe',
                              prefixIcon: Icons.lock_outline,
                              obscureText: _obscureNewPassword,
                              validator: Validators.validatePassword,
                              suffixIcon: IconButton(
                                icon: Icon(_obscureNewPassword ? Icons.visibility_off : Icons.visibility),
                                onPressed: () => setState(() => _obscureNewPassword = !_obscureNewPassword),
                              ),
                            ),
                            const SizedBox(height: 24),
                            CustomButton(
                              text: 'Réinitialiser le mot de passe',
                              isLoading: _isLoading,
                              backgroundColor: const Color(0xFF10B981),
                              onPressed: _submitNewPassword,
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
