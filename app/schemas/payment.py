"""Stripe payment schemas."""
from pydantic import BaseModel, Field


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class StripeConfigResponse(BaseModel):
    publishable_key: str
    test_mode: bool = True


class CheckoutSessionRequest(BaseModel):
    amount_cents: int | None = Field(
        default=None,
        ge=50,
        le=999_999,
        description="Optional override for test payment amount in cents",
    )
