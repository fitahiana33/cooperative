"""Papi HTTP adapter; domain services own payment state and reconciliation."""
import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from fastapi import HTTPException
from app.core.config import settings


def create_payment_link(*, amount: Decimal, reference: str, description: str, client_name: str,
                        payer_phone: str | None, payer_email: str | None, provider: str) -> dict:
    payload = {
        "amount": int(amount),
        "clientName": client_name,
        "reference": reference,
        "description": description,
        "successUrl": f"{settings.frontend_url.rstrip('/')}/paiement/succes?reference={reference}",
        "failureUrl": f"{settings.frontend_url.rstrip('/')}/paiement/echec?reference={reference}",
        "notificationUrl": settings.papi_notification_url,
        "validDuration": settings.papi_valid_duration_hours,
        "provider": provider,
    }
    if payer_phone:
        payload["payerPhone"] = payer_phone
    if payer_email:
        payload["payerEmail"] = payer_email
    request = Request(
        f"{settings.papi_base_url.rstrip('/')}/payment-links",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Token": settings.papi_api_key or ""},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise HTTPException(502, f"Papi a refusé la demande de paiement ({exc.code}).") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(502, "Papi est momentanément indisponible.") from exc
    data = result.get("data") if isinstance(result, dict) else None
    link = data.get("paymentLink") if isinstance(data, dict) else None
    if not isinstance(link, str) or len(link) > 500 or urlparse(link).scheme != "https" or not urlparse(link).netloc:
        raise HTTPException(502, "Papi n'a pas retourné de lien de paiement sécurisé.")
    return data

