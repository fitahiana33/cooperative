import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/user_error.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/travel/travel_models.dart';
import '../../../data/repositories/travel/travel_repository_impl.dart';
import '../../widgets/common/async_view.dart';

class NotificationsPage extends ConsumerStatefulWidget {
  const NotificationsPage({super.key});

  @override
  ConsumerState<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends ConsumerState<NotificationsPage> {
  final List<AppNotification> _items = [];
  int _page = 1;
  bool _hasMore = false;
  bool _loading = true;
  String? _error;

  static const _icons = {
    'CONFIRMATION_RESERVATION': Icons.event_available,
    'CONFIRMATION_PAIEMENT': Icons.payments,
    'RAPPEL_DEPART': Icons.alarm,
    'RETARD': Icons.schedule,
    'ANNULATION': Icons.cancel,
    'MODIFICATION_HORAIRE': Icons.update,
    'CONFIRMATION_EMBARQUEMENT': Icons.directions_bus,
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool more = false}) async {
    setState(() { _loading = !more && _items.isEmpty; _error = null; });
    try {
      final result = await ref.read(travelRepositoryProvider).listNotifications(page: more ? _page + 1 : 1);
      if (!mounted) return;
      setState(() {
        if (!more) _items.clear();
        _items.addAll(result.items);
        _page = result.page;
        _hasMore = result.hasMore;
      });
    } catch (error) {
      if (mounted) setState(() => _error = userError(error, 'Impossible de charger les notifications.', 'MOBILE_NOTIFICATIONS_ERROR'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _open(AppNotification item) async {
    if (item.read) return;
    try {
      await ref.read(travelRepositoryProvider).markNotificationRead(item.id);
      if (!mounted) return;
      setState(() {
        final index = _items.indexOf(item);
        _items[index] = AppNotification(id: item.id, type: item.type, title: item.title, message: item.message, read: true, sentAt: item.sentAt);
      });
    } catch (_) {
      // Marking as read is not essential; the list stays usable.
    }
  }

  Future<void> _markAll() async {
    try {
      await ref.read(travelRepositoryProvider).markAllNotificationsRead();
      await _load();
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(userError(error, 'Action impossible.', 'MOBILE_NOTIFICATIONS_READ_ALL'))));
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Notifications'), actions: [
          IconButton(tooltip: 'Tout marquer comme lu', onPressed: _items.any((n) => !n.read) ? _markAll : null, icon: const Icon(Icons.done_all)),
        ]),
        body: RefreshIndicator(
          onRefresh: _load,
          child: AsyncView(
            loading: _loading,
            error: _items.isEmpty ? _error : null,
            empty: _items.isEmpty,
            emptyMessage: 'Aucune notification.',
            emptyIcon: Icons.notifications_none,
            onRetry: _load,
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: _items.length + (_hasMore ? 1 : 0),
              itemBuilder: (_, index) {
                if (index == _items.length) return TextButton(onPressed: () => _load(more: true), child: const Text('Voir plus'));
                final item = _items[index];
                return Card(
                  color: item.read ? AppTheme.surface : const Color(0xFF1E3A8A),
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: Icon(_icons[item.type] ?? Icons.notifications, color: item.read ? Colors.white54 : AppTheme.primaryAccent),
                    title: Text(item.title, style: TextStyle(fontWeight: item.read ? FontWeight.normal : FontWeight.bold)),
                    subtitle: Text('${item.message}\n${Fmt.dateTime(item.sentAt)}'),
                    isThreeLine: true,
                    onTap: () => _open(item),
                  ),
                );
              },
            ),
          ),
        ),
      );
}
