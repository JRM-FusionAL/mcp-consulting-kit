import os
import httpx

STRIPE_API_URL = "https://api.stripe.com/v1"

class StripeClient:
    def __init__(self) -> None:
        key = os.getenv("STRIPE_API_KEY")
        if not key:
            raise RuntimeError("STRIPE_API_KEY not set")
        self.key = key
        self.client = httpx.Client(timeout=10.0, auth=(self.key, ""))

    def retrieve_customer(self, customer_id: str):
        resp = self.client.get(f"{STRIPE_API_URL}/customers/{customer_id}")
        resp.raise_for_status()
        return resp.json()

    def list_charges(self, customer_id: str | None = None, limit: int = 10):
        params = {"limit": limit}
        if customer_id:
            params["customer"] = customer_id
        resp = self.client.get(f"{STRIPE_API_URL}/charges", params=params)
        resp.raise_for_status()
        return resp.json()

    def list_subscriptions(self, customer_id: str | None = None, limit: int = 10):
        params = {"limit": limit}
        if customer_id:
            params["customer"] = customer_id
        resp = self.client.get(f"{STRIPE_API_URL}/subscriptions", params=params)
        resp.raise_for_status()
        return resp.json()
