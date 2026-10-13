import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// Message to show for a failed request. The server's own explanation
/// (FastAPI `detail`) is preferred because it says what to do next
/// ("place n'est plus disponible", "email déjà utilisée"...).
String userError(Object error, String fallback, String context, {String? unauthorizedMessage}) {
  debugPrint('[$context] $error');
  if (error is DioException) {
    final response = error.response;
    if (response == null) {
      return error.type == DioExceptionType.connectionTimeout || error.type == DioExceptionType.receiveTimeout
          ? 'Le serveur met trop de temps à répondre. Réessayez dans un instant.'
          : 'Le serveur est momentanément indisponible. Vérifiez votre connexion puis réessayez.';
    }
    final status = response.statusCode ?? 0;
    final detail = _detail(response.data);
    if (status == 401) return unauthorizedMessage ?? detail ?? 'Votre session a expiré. Reconnectez-vous puis réessayez.';
    if (status == 429) return 'Trop de tentatives. Patientez une minute avant de réessayer.';
    if (status >= 500) return 'Une erreur est survenue. Veuillez réessayer.';
    if (detail != null) return detail;
    if (status == 403) return 'Vous n’avez pas l’autorisation d’effectuer cette action.';
    if (status == 404) return 'La ressource demandée est introuvable.';
    if (status == 409) return 'Cette opération entre en conflit avec des données existantes.';
    if (status == 422) return 'Vérifiez les champs saisis puis réessayez.';
    return fallback;
  }
  final message = error.toString().replaceFirst('Exception: ', '').trim();
  if (message.isNotEmpty && !message.contains('StackTrace') && !message.contains('NoSuchMethod') && !message.contains('is not a subtype')) return message;
  return fallback;
}

String? _detail(Object? data) {
  if (data is! Map) return null;
  final detail = data['detail'];
  if (detail is String && detail.trim().isNotEmpty) return detail.trim();
  // Validation errors: [{"loc": [...], "msg": "..."}]
  if (detail is List && detail.isNotEmpty && detail.first is Map) {
    final message = (detail.first as Map)['msg'];
    if (message is String) return message.replaceFirst('Value error, ', '');
  }
  return null;
}
