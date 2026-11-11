import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../widgets/common/user_avatar.dart';

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
      final result = await ref
          .read(travelRepositoryProvider)
          .listNotifications(unreadOnly: true);
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
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        backgroundColor: AppTheme.background,
        title: const Row(children: [
          Icon(Icons.directions_bus_rounded, color: AppTheme.primaryAccent),
          SizedBox(width: 10),
          Text('Coopérative', style: TextStyle(fontWeight: FontWeight.w800))
        ]),
        actions: [
          if (user != null)
            IconButton(
                tooltip: 'Mon profil',
                onPressed: () => _open(const ProfilePage()),
                icon: UserAvatar(user: user, radius: 17)),
          IconButton(
            tooltip: _unread > 0
                ? '$_unread notification(s) non lue(s)'
                : 'Notifications',
            onPressed: () => _open(const NotificationsPage()),
            icon: Badge(
                isLabelVisible: _unread > 0,
                label: Text('$_unread'),
                child: const Icon(Icons.notifications_outlined)),
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
          physics: const AlwaysScrollableScrollPhysics(),
          padding: EdgeInsets.symmetric(
              horizontal: MediaQuery.sizeOf(context).width > 960
                  ? (MediaQuery.sizeOf(context).width - 920) / 2
                  : 20,
              vertical: 24),
          children: [
            _welcomeCard(user?.fullName ?? 'Utilisateur', user?.email ?? ''),
            if (isPassenger || isDriver) ...[
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: () => _open(isDriver
                    ? const DriverPointagePage()
                    : const TripSearchPage()),
                icon: Icon(
                    isDriver ? Icons.departure_board : Icons.search_rounded),
                label:
                    Text(isDriver ? 'Voir mes départs' : 'Trouver un voyage'),
                style: FilledButton.styleFrom(
                    minimumSize: const Size(double.infinity, 56),
                    backgroundColor: AppTheme.primary,
                    foregroundColor: AppTheme.background,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14))),
              ),
            ],
            const SizedBox(height: 24),
            if (isDriver) ...[
              _section('Espace chauffeur'),
              _actionCard(
                  Icons.directions_bus_rounded,
                  'Mes départs',
                  'Pointez vos départs et arrivées, voyez vos passagers.',
                  const Color(0xFF14B8A6),
                  const DriverPointagePage()),
            ] else if (isPassenger) ...[
              _section('Voyager'),
              _actionCard(
                  Icons.search_rounded,
                  'Rechercher un voyage',
                  'Choisissez votre trajet, votre date et vos places.',
                  const Color(0xFF3B82F6),
                  const TripSearchPage()),
              _actionCard(
                  Icons.event_note_rounded,
                  'Mes réservations',
                  'Consultez le statut et les détails de vos voyages.',
                  const Color(0xFF89C9C4),
                  const ReservationsPage()),
              _actionCard(
                  Icons.qr_code_2_rounded,
                  'Mes billets',
                  'Présentez le QR code à l’embarquement.',
                  const Color(0xFF10B981),
                  const TicketsPage()),
            ] else
              const Padding(
                padding: EdgeInsets.only(bottom: 16),
                child: Text(
                    'L’application mobile est destinée aux voyageurs et aux chauffeurs. Utilisez l’application web pour la gestion.',
                    style: TextStyle(color: Colors.white70)),
              ),
            _section('Mon compte'),
            _actionCard(
                Icons.person_outline_rounded,
                'Mon profil',
                'Coordonnées et mot de passe.',
                const Color(0xFF64748B),
                const ProfilePage()),
            const SizedBox(height: 12),
            const Padding(
                padding: EdgeInsets.all(12),
                child: Text(
                    'Avant le départ, vérifiez la gare et l’horaire de votre réservation. Gardez votre billet à portée de main.',
                    style: TextStyle(
                        color: Colors.white60, height: 1.6, fontSize: 13))),
          ],
        ),
      ),
      bottomNavigationBar: isPassenger
          ? SafeArea(
              top: false,
              child: NavigationBar(
                backgroundColor: AppTheme.surface,
                indicatorColor: AppTheme.surfaceCard,
                selectedIndex: 0,
                onDestinationSelected: (index) {
                  if (index == 1) _open(const ReservationsPage());
                  if (index == 2) _open(const TicketsPage());
                  if (index == 3) _open(const ProfilePage());
                },
                destinations: const [
                  NavigationDestination(
                      icon: Icon(Icons.home_outlined),
                      selectedIcon: Icon(Icons.home_rounded),
                      label: 'Accueil'),
                  NavigationDestination(
                      icon: Icon(Icons.confirmation_number_outlined),
                      label: 'Réservations'),
                  NavigationDestination(
                      icon: Icon(Icons.qr_code_2_rounded), label: 'Billets'),
                  NavigationDestination(
                      icon: Icon(Icons.person_outline), label: 'Profil'),
                ],
              ))
          : null,
    );
  }

  Widget _section(String title) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Text(title,
            style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold)),
      );

  Widget _welcomeCard(String name, String email) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(26),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
              colors: [Color(0xFF225968), Color(0xFF193C50)]),
          border: Border.all(color: const Color(0xFF3A6975)),
          borderRadius: BorderRadius.circular(24),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('LE VOYAGE COMMENCE ICI',
              style: TextStyle(
                  color: AppTheme.primaryAccent,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 2)),
          const SizedBox(height: 16),
          Text('Bonjour $name',
              style: const TextStyle(color: Colors.white70, fontSize: 15)),
          const SizedBox(height: 12),
          const Text('Votre destination.\nVotre place. Votre voyage.',
              style: TextStyle(
                  color: Colors.white,
                  fontSize: 30,
                  height: 1.2,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -.8)),
          const SizedBox(height: 14),
          const Text(
              'Retrouvez vos trajets et préparez votre prochain départ en toute simplicité.',
              style: TextStyle(color: Colors.white70, height: 1.6)),
        ]),
      );

  Widget _actionCard(IconData icon, String title, String subtitle, Color color,
          Widget page) =>
      Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Material(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(18),
          child: InkWell(
            borderRadius: BorderRadius.circular(18),
            onTap: () => _open(page),
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Row(children: [
                Icon(icon, color: color, size: 32),
                const SizedBox(width: 16),
                Expanded(
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                      Text(title,
                          style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 16)),
                      const SizedBox(height: 4),
                      Text(subtitle,
                          style: const TextStyle(
                              color: Colors.white60,
                              fontSize: 13,
                              height: 1.5)),
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
          TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Annuler')),
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
