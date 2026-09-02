import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

String userError(Object error, String fallback, String context) {
  debugPrint('[$context] $error');
  if (error is DioException) {
    final status = error.response?.statusCode;
    if (error.response == null) return 'Le serveur est momentanément indisponible. Vérifiez votre connexion puis réessayez.';
    if (status == 401) return 'Votre session a expiré. Reconnectez-vous puis réessayez.';
    if (status == 403) return 'Vous n’avez pas l’autorisation d’effectuer cette action.';
    if (status == 404) return 'La ressource demandée est introuvable.';
    if (status == 409) return 'Cette donnée existe déjà ou est encore utilisée.';
    if (status == 422) return 'Vérifiez les champs saisis puis réessayez.';
    if (status != null && status >= 500) return 'Une erreur est survenue. Veuillez réessayer.';
    return fallback;
  }
  final message = error.toString().replaceFirst('Exception: ', '').trim();
  if (message.isNotEmpty && !message.contains('StackTrace') && !message.contains('NoSuchMethod')) return message;
  return fallback;
}
