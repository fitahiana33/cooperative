import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../controllers/auth/auth_controller.dart';
import '../management/cooperatives_page.dart';
import '../management/gares_page.dart';

class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    final user = authState.user;
    final role = (user?.role ?? 'passenger').toLowerCase();
    final isStaff = ['admin', 'responsable_gare', 'agent_gare', 'responsable_cooperative', 'manager'].contains(role);

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF3B82F6).withValues(alpha: 0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.directions_bus_rounded,
                color: Color(0xFF60A5FA),
                size: 22,
              ),
            ),
            const SizedBox(width: 10),
            const Text(
              'Coopérative',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.white,
                fontSize: 20,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: Color(0xFFF87171)),
            tooltip: 'Déconnexion',
            onPressed: () {
              _confirmLogout(context, ref);
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF2563EB).withValues(alpha: 0.35),
                    blurRadius: 20,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 32,
                    backgroundColor: Colors.white.withValues(alpha: 0.2),
                    child: Text(
                      user != null && user.firstName.isNotEmpty
                          ? user.firstName[0].toUpperCase()
                          : 'U',
                      style: const TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user?.fullName ?? 'Utilisateur',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          user?.email ?? '',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.8),
                            fontSize: 13,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.black.withValues(alpha: 0.25),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
                          ),
                          child: Text(
                            'Rôle: ${(user?.role ?? "passenger").toUpperCase()}',
                            style: const TextStyle(
                              color: Color(0xFF93C5FD),
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            if (isStaff) ...[
              const Text(
                'Administration & Gestion',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 14),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 14,
                mainAxisSpacing: 14,
                childAspectRatio: 1.3,
                children: [
                  _buildActionCard(
                    icon: Icons.location_city_rounded,
                    title: 'Gérer les Gares',
                    subtitle: 'Créer, activer et consulter les gares',
                    color: const Color(0xFF3B82F6),
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const GaresPage()));
                    },
                  ),
                  _buildActionCard(
                    icon: Icons.business_rounded,
                    title: 'Gérer Coopératives',
                    subtitle: 'Partenaires, agréments & membres',
                    color: const Color(0xFF10B981),
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const CooperativesPage()));
                    },
                  ),
                ],
              ),
              const SizedBox(height: 28),
            ],

            const Text(
              'Services & Réservations',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 14),

            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 14,
              mainAxisSpacing: 14,
              childAspectRatio: 1.3,
              children: [
                _buildActionCard(
                  icon: Icons.search_rounded,
                  title: 'Rechercher Voyage',
                  subtitle: 'Trouvez vos lignes de taxi-brousse',
                  color: const Color(0xFF3B82F6),
                ),
                _buildActionCard(
                  icon: Icons.confirmation_number_outlined,
                  title: 'Mes Réservations',
                  subtitle: 'Consultez vos billets validés',
                  color: const Color(0xFF10B981),
                ),
                _buildActionCard(
                  icon: Icons.history_rounded,
                  title: 'Historique',
                  subtitle: 'Vos anciens trajets',
                  color: const Color(0xFF8B5CF6),
                ),
                _buildActionCard(
                  icon: Icons.support_agent_rounded,
                  title: 'Assistance',
                  subtitle: 'Support client 24/7',
                  color: const Color(0xFFF59E0B),
                ),
              ],
            ),
            const SizedBox(height: 28),

            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline_rounded, color: Color(0xFF60A5FA)),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Session active sécurisée via jetons JWT (Storage local & Refresh Token)',
                      style: TextStyle(color: Colors.grey.shade300, fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(height: 10),
            Text(
              title,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              subtitle,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: Colors.grey.shade400,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmLogout(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Déconnexion', style: TextStyle(color: Colors.white)),
        content: const Text(
          'Voulez-vous vraiment vous déconnecter de l\'application ?',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annuler', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFEF4444),
              foregroundColor: Colors.white,
            ),
            onPressed: () {
              Navigator.pop(context);
              ref.read(authControllerProvider.notifier).logout();
            },
            child: const Text('Déconnexion'),
          ),
        ],
      ),
    );
  }
}
