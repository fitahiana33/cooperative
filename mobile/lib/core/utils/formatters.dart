import 'package:intl/intl.dart';

/// French formatting for dates, times, amounts and statuses shown to passengers.
class Fmt {
  static final _money = NumberFormat.decimalPattern('fr_FR');
  static final _date = DateFormat('EEE d MMM yyyy', 'fr_FR');
  static final _shortDate = DateFormat('dd/MM/yyyy', 'fr_FR');
  static final _dateTime = DateFormat('dd/MM/yyyy HH:mm', 'fr_FR');

  static String money(Object? value, [String? currency]) {
    final amount = value is num ? value : num.tryParse('${value ?? ''}') ?? 0;
    final unit = (currency == null || currency == 'MGA') ? 'Ar' : currency;
    return '${_money.format(amount.round())} $unit';
  }

  /// "2026-10-08" -> "jeu. 8 oct. 2026"
  static String date(Object? isoDate) {
    final parsed = DateTime.tryParse('${isoDate ?? ''}');
    return parsed == null ? '—' : _date.format(parsed);
  }

  static String shortDate(Object? isoDate) {
    final parsed = DateTime.tryParse('${isoDate ?? ''}');
    return parsed == null ? '—' : _shortDate.format(parsed);
  }

  /// "08:00:00" -> "08:00"
  static String time(Object? value) {
    final text = '${value ?? ''}';
    return text.length >= 5 ? text.substring(0, 5) : (text.isEmpty ? '—' : text);
  }

  /// ISO timestamp (UTC) -> local "08/10/2026 13:45"
  static String dateTime(Object? isoTimestamp) {
    final parsed = DateTime.tryParse('${isoTimestamp ?? ''}');
    return parsed == null ? '—' : _dateTime.format(parsed.toLocal());
  }

  static String apiDate(DateTime value) => DateFormat('yyyy-MM-dd').format(value);

  static const _labels = {
    'PROGRAMME': 'Programmé',
    'EMBARQUEMENT': 'Embarquement',
    'RETARDE': 'Retardé',
    'PARTI': 'Parti',
    'TERMINE': 'Terminé',
    'ANNULE': 'Annulé',
    'EN_ATTENTE': 'En attente de paiement',
    'CONFIRMEE': 'Confirmée',
    'PAYEE': 'Payée',
    'ANNULEE': 'Annulée',
    'EXPIREE': 'Expirée',
    'EMBARQUEE': 'Embarquée',
    'TERMINEE': 'Terminée',
    'VALIDE': 'Valide',
    'UTILISE': 'Utilisé',
    'EXPIRE': 'Expiré',
  };

  static String status(Object? value) => _labels['${value ?? ''}'] ?? '${value ?? '—'}';
}
