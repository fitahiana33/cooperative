class MarqueOption {
  final int id;
  final String nom;

  const MarqueOption({required this.id, required this.nom});

  factory MarqueOption.fromJson(Map<String, dynamic> json) {
    return MarqueOption(
      id: json['id'] as int,
      nom: json['nom'] as String? ?? '',
    );
  }
}

class ModeleOption {
  final int id;
  final int idMarque;
  final String nom;

  const ModeleOption({required this.id, required this.idMarque, required this.nom});

  factory ModeleOption.fromJson(Map<String, dynamic> json) {
    return ModeleOption(
      id: json['id'] as int,
      idMarque: json['id_marque'] as int? ?? 0,
      nom: json['nom'] as String? ?? '',
    );
  }
}

class CooperativeOption {
  final int id;
  final String nom;

  const CooperativeOption({required this.id, required this.nom});

  factory CooperativeOption.fromJson(Map<String, dynamic> json) {
    return CooperativeOption(
      id: json['id'] as int,
      nom: json['nom'] as String? ?? '',
    );
  }
}
