import 'package:flutter/material.dart';

import '../../../core/utils/formatters.dart';

class StatusChip extends StatelessWidget {
  final String status;

  const StatusChip(this.status, {super.key});

  static Color colorFor(String status) {
    switch (status) {
      case 'PAYEE':
      case 'CONFIRMEE':
      case 'VALIDE':
      case 'PROGRAMME':
      case 'EMBARQUEMENT':
        return const Color(0xFF10B981);
      case 'EN_ATTENTE':
      case 'RETARDE':
        return const Color(0xFFF59E0B);
      case 'EMBARQUEE':
      case 'UTILISE':
      case 'PARTI':
      case 'TERMINEE':
      case 'TERMINE':
        return const Color(0xFF3B82F6);
      default:
        return const Color(0xFFEF4444);
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = colorFor(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.18), borderRadius: BorderRadius.circular(20), border: Border.all(color: color.withValues(alpha: 0.6))),
      child: Text(Fmt.status(status), style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600)),
    );
  }
}
