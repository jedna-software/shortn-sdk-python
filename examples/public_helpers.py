"""The endpoints that need no API key: URL validation, QR codes and the plan catalog.

    python examples/public_helpers.py
"""

from shortn_sdk import Shortn


def main() -> None:
    shortn = Shortn()  # no API key

    validation = shortn.public.validate_url("example.com/pricing")
    if not validation["valid"]:
        raise SystemExit(validation.get("error") or "URL is not valid.")
    print("normalized:", validation["normalized"])

    png = shortn.public.qr_code(url=validation["normalized"], size="preview-hd")
    with open("pricing-qr.png", "wb") as handle:
        handle.write(png)
    print("wrote pricing-qr.png,", len(png), "bytes")

    for plan_id, plan in shortn.public.plans()["plans"].items():
        print(plan_id, plan["Name"], plan["Price"], plan["Currency"])


if __name__ == "__main__":
    main()
