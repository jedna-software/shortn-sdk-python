"""Forward a lead and a sale from your backend, then read the test events back.

The click id comes from the capture script on your site (the snt_click_id value).

    SHORTN_API_KEY=sk_live_... SHORTN_CLICK_ID=clk_... python examples/track_conversions.py
"""

import os

from shortn_sdk import Shortn, ShortnAPIError


def main() -> None:
    shortn = Shortn(os.environ["SHORTN_API_KEY"])
    click_id = os.environ["SHORTN_CLICK_ID"]
    signup_id = os.environ.get("SIGNUP_ID", "signup_8412")
    invoice_id = os.environ.get("INVOICE_ID", "inv_123")

    lead = shortn.conversions.track_lead(
        click_id=click_id,
        idempotency_key=f"signup:{signup_id}",
        event_name="Sign up",
        lead_category="signup",
        test_mode=True,
    )
    print(lead["type"], lead["event"]["public_id"], "duplicate:", lead["event"]["duplicate"])

    try:
        sale = shortn.conversions.track_sale(
            click_id=click_id,
            amount_cents=4900,
            currency="EUR",
            invoice_id=invoice_id,
            idempotency_key=f"sale:{invoice_id}",
            test_mode=True,
        )
        print(sale["type"], sale["event"]["amount"], sale["event"]["currency"])
    except ShortnAPIError as error:
        print("sale refused:", error.status, error.code, error.hint)

    events = shortn.conversions.events(environment="test", limit=10)
    for event in events["data"]:
        print(event["occurred_at"], event["event_type"], event.get("event_name"))


if __name__ == "__main__":
    main()
