import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/repositories/travel/travel_repository_impl.dart';
import '../../controllers/auth/auth_controller.dart';
import '../operations/driver_pointage_page.dart';
import '../passenger/notifications_page.dart';
import '../passenger/profile_page.dart';
import '../passenger/reservations_page.dart';
import '../passenger/tickets_page.dart';
import '../passenger/trip_search_page.dart';

class HomePage extends ConsumerStatefulWidget {
  const HomePage({super.key});

  @override
  ConsumerState<HomePage> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  int _unread = 0;

  @override
  void initState() {
    super.initState();
    _loadUnread();
  }

  Future<void> _loadUnread() async {
    try {
      final result = await ref.read(travelRepositoryProvider).listNotifications(unreadOnly: true);
      if (mounted) setState(() => _unread = result.total);
    } catch (_) {
      // The badge is optional.
    }
  }

  Future<void> _open(Widget page) async {
    await Navigator.push(context, MaterialPageRoute(builder: (_) => page));
    if (mounted) _loadUnread();
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authControllerProvider).user;
    final role = (user?.role ?? 'passenger').toLowerCase();
    final isDriver = role == 'chauffeur' || role == 'driver';
    final isPassenger = role == 'passager' || role == 'passenger';

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Coopérative'),
        actions: [
          IconButton(
            tooltip: _unread > 0 ? '$_unread notification(s) non lue(s)' : 'Notifications',
            onPressed: () => _open(const NotificationsPage()),
            icon: Badge(isLabelVisible: _unread > 0, label: Text('$_unread'), child: const Icon(Icons.notifications_outlined)),
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: Color(0xFFF87171)),
            tooltip: 'Déconnexion',
            onPressed: () => _confirmLogout(context),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadUnread,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            _welcomeCard(user?.fullName ?? 'Utilisateur', user?.email ?? ''),
            const SizedBox(height: 24),
            if (isDriver) ...[
              _section('Espace chauffeur'),
              _actionCard(Icons.directions_bus_rounded, 'Mes départs', 'Pointez vos départs et arrivées, voyez vos passagers.', const Color(0xFF14B8A6), const DriverPointagePage()),
            ] else if (isPassenger) ...[
              _section('Voyager'),
              _actionCard(Icons.search_rounded, 'Rechercher un voyage', 'Choisissez votre trajet, votre date et vos places.', const Color(0xFF3B82F6), const TripSearchPage()),
              _actionCard(Icons.event_note_rounded, 'Mes réservations', 'Suivez, payez au guichet ou annulez vos réservations.', const Color(0xFF8B5CF6), const ReservationsPage()),
              _actionCard(Icons.qr_code_2_rounded, 'Mes billets', 'Présentez le QR code à l’embarquement.', const Color(0xFF10B981), const TicketsPage()),
            ] else
              const Padding(
                padding: EdgeInsets.only(bottom: 16),
                child: Text('L’application mobile est destinée aux voyageurs et aux chauffeurs. Utilisez l’application web pour la gestion.', style: TextStyle(color: Colors.white70)),
              ),
            _section('Mon compte'),
            _actionCard(Icons.person_outline_rounded, 'Mon profil', 'Coordonnées et mot de passe.', const Color(0xFF64748B), const ProfilePage()),
          ],
        ),
      ),
    );
  }

  Widget _section(String title) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Text(title, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
      );

  Widget _welcomeCard(String name, String email) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)]),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Bonjour $name', style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(email, style: const TextStyle(color: Colors.white70)),
        ]),
      );

  Widget _actionCard(IconData icon, String title, String subtitle, Color color, Widget page) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Material(
          color: Colors.white.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(18),
          child: InkWell(
            borderRadius: BorderRadius.circular(18),
            onTap: () => _open(page),
            child: Padding(
              padding: const EdgeInsets.all(18),
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
          ),
        ),
      );

  void _confirmLogout(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Déconnexion'),
        content: const Text('Voulez-vous vous déconnecter ?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Annuler')),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(dialogContext);
              ref.read(authControllerProvider.notifier).logout();
            },
            child: const Text('Se déconnecter'),
          ),
        ],
      ),
    );
  }
}
