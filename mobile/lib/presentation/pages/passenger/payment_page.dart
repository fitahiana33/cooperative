import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/errors/user_error.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/travel/travel_models.dart';
import '../../../data/repositories/travel/travel_repository_impl.dart';

class PaymentPage extends ConsumerStatefulWidget {
  final Reservation reservation;
  const PaymentPage({super.key, required this.reservation});
  @override
  ConsumerState<PaymentPage> createState() => _PaymentPageState();
}

class _PaymentPageState extends ConsumerState<PaymentPage>
    with WidgetsBindingObserver {
  final _form = GlobalKey<FormState>();
  late final TextEditingController _amount;
  late final TextEditingController _phone;
  String _provider = 'MVOLA';
  bool _busy = false;
  String? _message;
  String? _error;
  String? _checkoutUrl;

  @override
  void initState() {
    super.initState();
    _amount = TextEditingController(
        text: widget.reservation.minimumPayment.toStringAsFixed(0));
    _phone = TextEditingController(text: widget.reservation.bookerPhone ?? '');
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _amount.dispose();
    _phone.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && !_busy) _check();
  }

  Future<void> _openCheckout() async {
    final uri = Uri.tryParse(_checkoutUrl ?? '');
    if (uri == null ||
        uri.scheme != 'https' ||
        !await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      throw StateError('Impossible d’ouvrir le paiement sécurisé.');
    }
  }

  Future<void> _pay() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await ref
          .read(travelRepositoryProvider)
          .createOnlinePayment(widget.reservation.id,
              double.parse(_amount.text), _provider, _phone.text);
      if (!mounted) return;
      setState(() {
        _message = result.message;
        _checkoutUrl = result.checkoutUrl;
      });
      if (result.amount != null &&
          result.amount != double.parse(_amount.text)) {
        setState(() {
          _amount.text = result.amount!.toStringAsFixed(0);
          _message =
              'Une demande de ${Fmt.money(result.amount!)} existe déjà. Appuyez à nouveau pour reprendre ce paiement.';
        });
      } else if (_checkoutUrl != null) {
        await _openCheckout();
      }
    } catch (error) {
      if (mounted)
        setState(() => _error = userError(
            error,
            'Vérifiez le statut avant de renouveler le paiement.',
            'MOBILE_PAYMENT_ERROR'));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _check() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final updated = await ref
          .read(travelRepositoryProvider)
          .getReservation(widget.reservation.id);
      if (!mounted) return;
      if (updated.paidAmount > widget.reservation.paidAmount ||
          !updated.canPay) {
        Navigator.pop(context, updated);
      } else {
        setState(() => _message =
            'La confirmation du paiement n’a pas encore été reçue. Votre réservation reste consultable.');
      }
    } catch (error) {
      if (mounted)
        setState(() => _error = userError(
            error,
            'Impossible de vérifier le paiement.',
            'MOBILE_PAYMENT_STATUS_ERROR'));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Paiement sécurisé')),
        body: ListView(padding: const EdgeInsets.all(20), children: [
          Text(widget.reservation.number,
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          Text(
              'Reste à régler : ${Fmt.money(widget.reservation.remainingAmount)}'),
          const SizedBox(height: 20),
          Form(
              key: _form,
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    DropdownButtonFormField<String>(
                      initialValue: _provider,
                      decoration:
                          const InputDecoration(labelText: 'Moyen de paiement'),
                      items: const [
                        DropdownMenuItem(value: 'MVOLA', child: Text('MVola')),
                        DropdownMenuItem(
                            value: 'ORANGE_MONEY', child: Text('Orange Money')),
                        DropdownMenuItem(
                            value: 'AIRTEL_MONEY', child: Text('Airtel Money'))
                      ],
                      onChanged: _busy
                          ? null
                          : (value) => setState(() => _provider = value!),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                        controller: _phone,
                        enabled: !_busy,
                        keyboardType: TextInputType.phone,
                        autofillHints: const [AutofillHints.telephoneNumber],
                        decoration: const InputDecoration(
                            labelText: 'Numéro Mobile Money',
                            helperText:
                                'Le compte qui autorisera le paiement.'),
                        validator: (value) {
                          final digits =
                              (value ?? '').replaceAll(RegExp(r'\D'), '');
                          if (!((digits.length == 10 &&
                                  digits.startsWith('0')) ||
                              (digits.length == 12 &&
                                  digits.startsWith('261')))) {
                            return 'Saisissez un numéro malgache valide.';
                          }
                          return null;
                        }),
                    const SizedBox(height: 16),
                    TextFormField(
                        controller: _amount,
                        enabled: !_busy,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                            labelText: 'Montant en ariary'),
                        validator: (value) {
                          final amount = double.tryParse(value ?? '');
                          if (amount == null ||
                              !amount.isFinite ||
                              amount != amount.roundToDouble() ||
                              amount < widget.reservation.minimumPayment ||
                              amount > widget.reservation.remainingAmount) {
                            return 'Entre ${Fmt.money(widget.reservation.minimumPayment)} et ${Fmt.money(widget.reservation.remainingAmount)}.';
                          }
                          return null;
                        }),
                    const SizedBox(height: 20),
                    FilledButton.icon(
                        onPressed: _busy ? null : _pay,
                        icon: const Icon(Icons.lock_outline),
                        label: Text(
                            _busy ? 'Préparation…' : 'Continuer le paiement')),
                  ])),
          if (_message != null)
            Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: Text(_message!, semanticsLabel: _message)),
          if (_error != null)
            Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: Text(_error!,
                    style:
                        TextStyle(color: Theme.of(context).colorScheme.error))),
          OutlinedButton(
              onPressed: _busy ? null : _check,
              child: const Text('Vérifier le statut du paiement')),
          const SizedBox(height: 12),
          const Text(
              'Le paiement s’ouvre dans le navigateur sécurisé. Revenez dans l’application pour vérifier sa confirmation.'),
        ]),
      );
}
