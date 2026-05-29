"""Stripe test payment endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.payment import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    StripeConfigResponse,
)
from app.services.stripe_service import StripeNotConfiguredError, StripeService

router = APIRouter()


@router.get("/config", response_model=StripeConfigResponse)
async def get_stripe_config(
    current_user: User = Depends(get_current_user),
):
    """Publishable key for client-side Stripe (test mode)."""
    _ = current_user
    if not StripeService.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured on the server",
        )
    return StripeConfigResponse(
        publishable_key=StripeService.get_publishable_key(),
        test_mode=True,
    )


@router.post("/checkout/test", response_model=CheckoutSessionResponse)
async def create_test_checkout(
    body: CheckoutSessionRequest | None = None,
    current_user: User = Depends(get_current_user),
):
    """
    Create a Stripe Checkout Session for a one-time test payment.
    Open ``checkout_url`` in the browser; use test card 4242 4242 4242 4242.
    """
    try:
        result = StripeService.create_test_checkout_session(
            user_id=str(current_user.id),
            user_email=current_user.email,
            amount_cents=body.amount_cents if body else None,
        )
    except StripeNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {exc}",
        ) from exc

    if not result["checkout_url"]:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a checkout URL",
        )

    return CheckoutSessionResponse(**result)


@router.get("/return", response_class=HTMLResponse)
async def payment_return(status: str = "success", session_id: str | None = None):
    """Browser redirect target after Stripe Checkout (mobile returns manually)."""
    title = "Payment successful" if status == "success" else "Payment cancelled"
    subtitle = (
        "You can close this page and return to Memoir."
        if status == "success"
        else "No charge was made. Return to the app to try again."
    )
    session_line = (
        f"<p style='color:#666;font-size:14px'>Session: {session_id}</p>"
        if session_id
        else ""
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title></head>
<body style="font-family:system-ui,sans-serif;padding:32px;text-align:center;background:#f2f1f7">
<h1 style="color:#202020">{title}</h1>
<p style="color:#555">{subtitle}</p>
{session_line}
</body></html>"""
