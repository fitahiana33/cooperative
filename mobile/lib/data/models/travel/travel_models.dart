// Typed views of the API payloads used by the passenger and driver screens.
// Parsing is tolerant: a missing optional field never crashes a screen.

int _int(Object? value, [int fallback = 0]) => value is int ? value : int.tryParse('${value ?? ''}') ?? fallback;
double _double(Object? value) => value is num ? value.toDouble() : double.tryParse('${value ?? ''}') ?? 0;
String _str(Object? value, [String fallback = '']) => value == null ? fallback : '$value';
Map<String, dynamic> _map(Object? value) => value is Map ? Map<String, dynamic>.from(value) : <String, dynamic>{};

class PageResult<T> {
  final List<T> items;
  final int total;
  final int page;
  final int pages;

  const PageResult({required this.items, required this.total, required this.page, required this.pages});

  bool get hasMore => page < pages;

  static PageResult<T> fromJson<T>(Object? data, T Function(Map<String, dynamic>) parse) {
    final json = _map(data);
    final items = (json['items'] as List? ?? const []).map((item) => parse(_map(item))).toList();
    return PageResult(items: items, total: _int(json['total'], items.length), page: _int(json['page'], 1), pages: _int(json['pages'], 1));
  }
}

class Destination {
  final int id;
  final String name;
  final String? region;
  final bool isActive;

  const Destination({required this.id, required this.name, this.region, this.isActive = true});

  factory Destination.fromJson(Map<String, dynamic> json) =>
      Destination(id: _int(json['id']), name: _str(json['nom']), region: json['region'] as String?, isActive: json['is_active'] != false);
}

class Departure {
  final int id;
  final String date;
  final String time;
  final String origin;
  final String destination;
  final String cooperative;
  final String vehiclePlate;
  final int seats;
  final int freeSeats;
  final double price;
  final String currency;
  final String status;
  final int seatsBesideDriver;
  final int seatsPerRow;

  const Departure({
    required this.id,
    required this.date,
    required this.time,
    required this.origin,
    required this.destination,
    required this.cooperative,
    required this.vehiclePlate,
    required this.seats,
    required this.freeSeats,
    required this.price,
    required this.currency,
    required this.status,
    this.seatsBesideDriver = 2,
    this.seatsPerRow = 4,
  });

  bool get isBookable => const {'PROGRAMME', 'EMBARQUEMENT', 'RETARDE'}.contains(status) && freeSeats > 0;

  factory Departure.fromJson(Map<String, dynamic> json) {
    final route = _map(json['itineraire']);
    final vehicle = _map(json['vehicule']);
    final fare = _map(json['tarif']);
    return Departure(
      id: _int(json['id']),
      date: _str(json['date_depart']),
      time: _str(json['heure_depart']),
      origin: _str(_map(route['destination_depart'])['nom'], '?'),
      destination: _str(_map(route['destination_arrivee'])['nom'], '?'),
      cooperative: _str(_map(json['cooperative'])['nom'], 'Coopérative'),
      vehiclePlate: _str(vehicle['immatriculation']),
      seats: _int(json['nombre_places']),
      freeSeats: _int(json['places_disponibles']),
      price: _double(fare['prix']),
      currency: _str(fare['devise'], 'MGA'),
      status: _str(json['statut']),
      seatsBesideDriver: _int(vehicle['places_avant'], 2),
      seatsPerRow: _int(vehicle['places_par_rangee'], 4),
    );
  }
}

class Seat {
  final int id;
  final int number;
  final String status;

  const Seat({required this.id, required this.number, required this.status});

  bool get isFree => status == 'DISPONIBLE';

  factory Seat.fromJson(Map<String, dynamic> json) =>
      Seat(id: _int(json['id']), number: _int(json['numero_place']), status: _str(json['statut']));
}

class PassengerSeat {
  final int departurePlaceId;
  final int seatNumber;
  final String name;
  final String? phone;
  final int? ticketId;
  final String? ticketNumber;
  final String? ticketStatus;

  const PassengerSeat({required this.departurePlaceId, required this.seatNumber, required this.name, this.phone, this.ticketId, this.ticketNumber, this.ticketStatus});

  factory PassengerSeat.fromJson(Map<String, dynamic> json) {
    final ticket = _map(json['billet']);
    return PassengerSeat(
      departurePlaceId: _int(json['id_depart_place']),
      seatNumber: _int(_map(json['depart_place'])['numero_place']),
      name: _str(json['nom_passager']),
      phone: json['telephone_passager'] as String?,
      ticketId: ticket.isEmpty ? null : _int(ticket['id']),
      ticketNumber: ticket.isEmpty ? null : _str(ticket['numero_billet']),
      ticketStatus: ticket.isEmpty ? null : _str(ticket['statut']),
    );
  }
}

class Reservation {
  final int id;
  final String number;
  final String status;
  final double amount;
  final String? expiresAt;
  final String createdAt;
  final int departureId;
  final String departureDate;
  final String departureTime;
  final String departureStatus;
  final String origin;
  final String destination;
  final String cooperative;
  final List<PassengerSeat> passengers;

  const Reservation({
    required this.id,
    required this.number,
    required this.status,
    required this.amount,
    required this.expiresAt,
    required this.createdAt,
    required this.departureId,
    required this.departureDate,
    required this.departureTime,
    required this.departureStatus,
    required this.origin,
    required this.destination,
    required this.cooperative,
    required this.passengers,
  });

  bool get isPending => status == 'EN_ATTENTE';
  bool get canBeCancelled => const {'EN_ATTENTE', 'CONFIRMEE', 'PAYEE'}.contains(status) && !const {'PARTI', 'TERMINE'}.contains(departureStatus);

  factory Reservation.fromJson(Map<String, dynamic> json) {
    final departure = _map(json['depart']);
    final route = _map(departure['itineraire']);
    final passengers = (json['places'] as List? ?? const []).map((item) => PassengerSeat.fromJson(_map(item))).toList()
      ..sort((a, b) => a.seatNumber.compareTo(b.seatNumber));
    return Reservation(
      id: _int(json['id']),
      number: _str(json['numero_reservation']),
      status: _str(json['statut']),
      amount: _double(json['montant_total']),
      expiresAt: json['date_expiration'] as String?,
      createdAt: _str(json['created_at']),
      departureId: _int(json['id_depart']),
      departureDate: _str(departure['date_depart']),
      departureTime: _str(departure['heure_depart']),
      departureStatus: _str(departure['statut']),
      origin: _str(_map(route['destination_depart'])['nom'], '?'),
      destination: _str(_map(route['destination_arrivee'])['nom'], '?'),
      cooperative: _str(_map(departure['cooperative'])['nom']),
      passengers: passengers,
    );
  }
}

class Ticket {
  final int id;
  final String number;
  final String qrValue;
  final String status;
  final String reservationNumber;
  final String passenger;
  final String? phone;
  final int seat;
  final String date;
  final String time;
  final String origin;
  final String destination;
  final double price;
  final String currency;
  final String cooperative;
  final String vehiclePlate;
  final String? usedAt;

  const Ticket({
    required this.id,
    required this.number,
    required this.qrValue,
    required this.status,
    required this.reservationNumber,
    required this.passenger,
    required this.phone,
    required this.seat,
    required this.date,
    required this.time,
    required this.origin,
    required this.destination,
    required this.price,
    required this.currency,
    required this.cooperative,
    required this.vehiclePlate,
    required this.usedAt,
  });

  bool get isValid => status == 'VALIDE';

  factory Ticket.fromJson(Map<String, dynamic> json) => Ticket(
        id: _int(json['id']),
        number: _str(json['numero_billet']),
        qrValue: _str(json['qr_code_uuid']),
        status: _str(json['statut']),
        reservationNumber: _str(json['numero_reservation']),
        passenger: _str(json['nom_passager']),
        phone: json['telephone_passager'] as String?,
        seat: _int(json['numero_place']),
        date: _str(json['date_depart']),
        time: _str(json['heure_depart']),
        origin: _str(json['destination_depart'], '?'),
        destination: _str(json['destination_arrivee'], '?'),
        price: _double(json['prix']),
        currency: _str(json['devise'], 'MGA'),
        cooperative: _str(json['nom_cooperative'] ?? json['cooperative']),
        vehiclePlate: _str(json['immatriculation']),
        usedAt: json['date_utilisation'] as String?,
      );
}

class AppNotification {
  final int id;
  final String type;
  final String title;
  final String message;
  final bool read;
  final String sentAt;

  const AppNotification({required this.id, required this.type, required this.title, required this.message, required this.read, required this.sentAt});

  factory AppNotification.fromJson(Map<String, dynamic> json) => AppNotification(
        id: _int(json['id']),
        type: _str(json['type_notification']),
        title: _str(json['titre']),
        message: _str(json['message']),
        read: json['est_lue'] == true,
        sentAt: _str(json['date_envoi']),
      );
}

class ManifestRow {
  final int seat;
  final String passenger;
  final String phone;
  final bool boarded;

  const ManifestRow({required this.seat, required this.passenger, required this.phone, required this.boarded});

  factory ManifestRow.fromJson(Map<String, dynamic> json) =>
      ManifestRow(seat: _int(json['place']), passenger: _str(json['passager']), phone: _str(json['telephone']), boarded: json['embarque'] == true);
}
