import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../controllers/auth/auth_controller.dart';
import '../../../data/repositories/driver_pointage/driver_pointage_repository_impl.dart';
import '../../../data/repositories/reservation/reservation_repository_impl.dart';
import '../../../domain/services/driver_pointage/driver_pointage_service.dart';
import '../../../domain/services/reservation/reservation_service.dart';
import '../operations/driver_pointage_page.dart';
import '../operations/reservations_page.dart';

class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    final user = authState.user;
    final role = (user?.role ?? 'passenger').toLowerCase();
    final isDriver = role == 'chauffeur' || role == 'driver';
    final isPassenger = role == 'passager' || role == 'passenger';
    final apiClient = ref.watch(authApiClientProvider);
    final reservationService = ReservationService(ReservationRepositoryImpl(apiClient));
    final pointageService = DriverPointageService(DriverPointageRepositoryImpl(apiClient));

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Cooperative'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: Color(0xFFF87171)),
            tooltip: 'Deconnexion',
            onPressed: () => _confirmLogout(context, ref),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _welcomeCard(user?.fullName ?? 'Utilisateur', user?.email ?? '', role),
            const SizedBox(height: 28),
            Text(
              isDriver ? 'Espace chauffeur' : 'Espace client',
              style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 14),
            if (isDriver)
              _actionCard(
                icon: Icons.fact_check_rounded,
                title: 'Pointage des trajets',
                subtitle: 'Pointez votre depart puis votre arrivee.',
                color: const Color(0xFF14B8A6),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => DriverPointagePage(pointageService: pointageService))),
              )
            else if (isPassenger)
              _actionCard(
                icon: Icons.confirmation_number_outlined,
                title: 'Reserver un voyage',
                subtitle: 'Recherchez un depart et gerez vos billets.',
                color: const Color(0xFF3B82F6),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ReservationsPage(reservationService: reservationService))),
              )
            else
              const Text('Cette application mobile est reservee aux clients et aux chauffeurs.', style: TextStyle(color: Colors.white70)),
          ],
        ),
      ),
    );
  }

  Widget _welcomeCard(String name, String email, String role) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)]),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(name, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(email, style: const TextStyle(color: Colors.white70)),
          const SizedBox(height: 12),
          Text('Role : ${role.toUpperCase()}', style: const TextStyle(color: Color(0xFFBFDBFE))),
        ]),
      );

  Widget _actionCard({required IconData icon, required String title, required String subtitle, required Color color, required VoidCallback onTap}) => GestureDetector(
        onTap: onTap,
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.06), borderRadius: BorderRadius.circular(18), border: Border.all(color: Colors.white.withValues(alpha: 0.1))),
          child: Row(children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(width: 16),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 4),
              Text(subtitle, style: TextStyle(color: Colors.grey.shade400, fontSize: 12)),
            ])),
            const Icon(Icons.chevron_right, color: Colors.white54),
          ]),
        ),
      );

  void _confirmLogout(BuildContext context, WidgetRef ref) {
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Deconnexion'),
        content: const Text('Voulez-vous vous deconnecter ?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Annuler')),
          ElevatedButton(onPressed: () { Navigator.pop(dialogContext); ref.read(authControllerProvider.notifier).logout(); }, child: const Text('Deconnexion')),
        ],
      ),
    );
  }
}
