"""Stripe Checkout helpers (test mode)."""
from __future__ import annotations

import logging

import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)


class StripeNotConfiguredError(Exception):
    """Raised when Stripe secret key is missing."""


class StripeService:
    @staticmethod
    def _ensure_configured() -> None:
        if not settings.STRIPE_SECRET_KEY:
            raise StripeNotConfiguredError(
                "Stripe is not configured. Set STRIPE_SECRET_KEY in backend/.env"
            )
        stripe.api_key = settings.STRIPE_SECRET_KEY

    @staticmethod
    def is_configured() -> bool:
        return bool(settings.STRIPE_SECRET_KEY)

    @staticmethod
    def get_publishable_key() -> str:
        return settings.STRIPE_PUBLISHABLE_KEY or ""

    @staticmethod
    def create_test_checkout_session(
        *,
        user_id: str,
        user_email: str | None,
        amount_cents: int | None = None,
    ) -> dict[str, str]:
        StripeService._ensure_configured()

        cents = amount_cents or settings.STRIPE_TEST_AMOUNT_CENTS
        success_url = (
            f"{settings.STRIPE_SUCCESS_URL}"
            "&session_id={CHECKOUT_SESSION_ID}"
        )

        params: dict = {
            "mode": "payment",
            "line_items": [
                {
                    "price_data": {
                        "currency": settings.STRIPE_CURRENCY,
                        "product_data": {
                            "name": "Memoir — test payment",
                            "description": "Stripe test checkout (use card 4242…)",
                        },
                        "unit_amount": cents,
                    },
                    "quantity": 1,
                }
            ],
            "success_url": success_url,
            "cancel_url": settings.STRIPE_CANCEL_URL,
            "client_reference_id": user_id,
            "metadata": {
                "user_id": user_id,
                "type": "test_checkout",
            },
        }
        if user_email:
            params["customer_email"] = user_email

        session = stripe.checkout.Session.create(**params)
        logger.info(
            "Stripe checkout session created user_id=%s session_id=%s",
            user_id,
            session.id,
        )
        return {
            "checkout_url": session.url or "",
            "session_id": session.id,
        }
