import 'package:flutter/material.dart';

/// Loading, error (with retry) and empty states shared by the list screens.
class AsyncView extends StatelessWidget {
  final bool loading;
  final String? error;
  final bool empty;
  final String emptyMessage;
  final IconData emptyIcon;
  final VoidCallback onRetry;
  final Widget child;

  const AsyncView({
    super.key,
    required this.loading,
    required this.error,
    required this.empty,
    required this.emptyMessage,
    required this.onRetry,
    required this.child,
    this.emptyIcon = Icons.inbox_outlined,
  });

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (error != null || empty) {
      // Scrollable so pull-to-refresh also works on an empty or failed list.
      return LayoutBuilder(
        builder: (context, constraints) => SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight),
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Icon(error != null ? Icons.cloud_off_rounded : emptyIcon, size: 48, color: Colors.white38),
                  const SizedBox(height: 12),
                  Text(error ?? emptyMessage, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white70)),
                  if (error != null) ...[
                    const SizedBox(height: 16),
                    OutlinedButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh), label: const Text('Réessayer')),
                  ],
                ]),
              ),
            ),
          ),
        ),
      );
    }
    return child;
  }
}
