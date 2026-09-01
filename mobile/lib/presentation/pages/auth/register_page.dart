import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/utils/validators.dart';
import '../../controllers/auth/auth_controller.dart';
import '../../controllers/auth/auth_state.dart';
import '../../widgets/auth/auth_form_card.dart';
import '../../widgets/common/custom_button.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/error_banner.dart';

class RegisterPage extends ConsumerStatefulWidget {
  const RegisterPage({super.key});

  @override
  ConsumerState<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends ConsumerState<RegisterPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _telephoneController = TextEditingController();
  final _addressController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;

  @override
  void dispose() {
    _nameController.dispose();
    _firstNameController.dispose();
    _emailController.dispose();
    _telephoneController.dispose();
    _addressController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  void _submit() async {
    if (_formKey.currentState?.validate() ?? false) {
      FocusScope.of(context).unfocus();
      final success = await ref.read(authControllerProvider.notifier).register(
            name: _nameController.text,
            firstName: _firstNameController.text,
            email: _emailController.text,
            telephone: _telephoneController.text,
            address: _addressController.text,
            password: _passwordController.text,
          );
      if (success && mounted) {
        Navigator.pop(context);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    final isLoading = authState.status == AuthStatus.loading;

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
                      'Créer un compte',
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
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
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

                          CustomTextField(
                            controller: _nameController,
                            labelText: 'Nom de famille',
                            prefixIcon: Icons.person_outline,
                            validator: (v) => Validators.validateRequired(v, 'votre nom'),
                          ),
                          const SizedBox(height: 16),

                          CustomTextField(
                            controller: _firstNameController,
                            labelText: 'Prénom',
                            prefixIcon: Icons.person_pin_outlined,
                            validator: (v) => Validators.validateRequired(v, 'votre prénom'),
                          ),
                          const SizedBox(height: 16),

                          CustomTextField(
                            controller: _emailController,
                            labelText: 'Adresse Email',
                            prefixIcon: Icons.email_outlined,
                            keyboardType: TextInputType.emailAddress,
                            validator: Validators.validateEmail,
                          ),
                          const SizedBox(height: 16),

                          CustomTextField(
                            controller: _telephoneController,
                            labelText: 'Numéro Téléphone (optionnel)',
                            prefixIcon: Icons.phone_outlined,
                            keyboardType: TextInputType.phone,
                          ),
                          const SizedBox(height: 16),

                          CustomTextField(
                            controller: _addressController,
                            labelText: 'Adresse / Ville (optionnel)',
                            prefixIcon: Icons.home_outlined,
                          ),
                          const SizedBox(height: 16),

                          CustomTextField(
                            controller: _passwordController,
                            labelText: 'Mot de passe',
                            prefixIcon: Icons.lock_outline,
                            obscureText: _obscurePassword,
                            validator: Validators.validatePassword,
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                                color: Colors.grey.shade400,
                              ),
                              onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                            ),
                          ),
                          const SizedBox(height: 16),

                          CustomTextField(
                            controller: _confirmPasswordController,
                            labelText: 'Confirmer le mot de passe',
                            prefixIcon: Icons.lock_reset_outlined,
                            obscureText: _obscureConfirmPassword,
                            validator: (v) => Validators.validateConfirmPassword(v, _passwordController.text),
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscureConfirmPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                                color: Colors.grey.shade400,
                              ),
                              onPressed: () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                            ),
                          ),
                          const SizedBox(height: 24),

                          CustomButton(
                            text: 'S\'inscrire maintenant',
                            isLoading: isLoading,
                            onPressed: _submit,
                          ),
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
