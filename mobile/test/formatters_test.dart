import 'package:cooperative_mobile/core/utils/formatters.dart';
import 'package:cooperative_mobile/core/utils/reset_link.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';

void main() {
  setUpAll(() => initializeDateFormatting('fr_FR'));

  test('amounts are shown in ariary with French grouping', () {
    expect(Fmt.money('45000.00', 'MGA').replaceAll(' ', ' ').replaceAll(' ', ' '), '45 000 Ar');
    expect(Fmt.money(1500, 'EUR').endsWith('EUR'), isTrue);
  });

  test('times drop the seconds', () {
    expect(Fmt.time('08:00:00'), '08:00');
    expect(Fmt.time(null), '—');
  });

  test('statuses are readable French labels', () {
    expect(Fmt.status('EN_ATTENTE'), 'En attente de paiement');
    expect(Fmt.status('PROGRAMME'), 'Programmé');
    expect(Fmt.status('INCONNU'), 'INCONNU');
  });

  test('reset token is read from the emailed link or typed directly', () {
    expect(extractResetToken('http://localhost:5173/forgot-password?token=abc.def'), 'abc.def');
    expect(extractResetToken('  abc.def  '), 'abc.def');
  });
}
