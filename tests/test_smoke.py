"""Opt-in smoke test against a live Shortn instance.

Skipped unless SHORTN_API_KEY and SHORTN_BASE_URL are set. It also needs:

- SHORTN_SMOKE_WORKSPACE: public ID of a workspace the test may create and delete things in;
- SHORTN_SMOKE_CLICK_ID: a click on a conversion-enabled link in that workspace.

Everything it creates has a random suffix and is removed again, also when a step fails.
Conversions are sent with ``test_mode`` and fresh idempotency keys.

    set -a; . ./smoke.env; set +a
    PYTHONPATH=src python -m unittest tests.test_smoke -v
"""

from __future__ import annotations

import os
import secrets
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shortn_sdk import RetryOptions, Shortn, ShortnAPIError  # noqa: E402

API_KEY = os.environ.get("SHORTN_API_KEY", "")
BASE_URL = os.environ.get("SHORTN_BASE_URL", "")
WORKSPACE = os.environ.get("SHORTN_SMOKE_WORKSPACE", "")
CLICK_ID = os.environ.get("SHORTN_SMOKE_CLICK_ID", "")
LINK_CODE = os.environ.get("SHORTN_SMOKE_LINK_CODE", "")

SUFFIX = secrets.token_hex(3)


def _ignore_missing(call, *args, **kwargs):
    """Cleanup helper: run a delete, ignoring "already gone"."""
    try:
        call(*args, **kwargs)
    except ShortnAPIError as exc:
        if exc.status not in (404, 410):
            raise


@unittest.skipUnless(API_KEY and BASE_URL and WORKSPACE, "set SHORTN_API_KEY, SHORTN_BASE_URL and SHORTN_SMOKE_WORKSPACE")
class SmokeTest(unittest.TestCase):
    client: Shortn

    @classmethod
    def setUpClass(cls) -> None:
        retry = RetryOptions(max_retries=4, initial_delay=1.0, max_retry_after=65.0)
        cls.client = Shortn(API_KEY, base_url=BASE_URL, timeout=30, retry=retry, user_agent="smoke-test")
        cls.public = Shortn(base_url=BASE_URL, retry=retry)

    def name(self, prefix: str) -> str:
        return f"{prefix}-{SUFFIX}"

    # ------------------------------------------------------------------

    def test_workspaces(self) -> None:
        listed = self.client.workspaces.list()
        ids = [ws["public_id"] for ws in listed["data"]]
        self.assertIn(WORKSPACE, ids)
        got = self.client.workspaces.get(WORKSPACE)
        self.assertEqual(got["data"]["public_id"], WORKSPACE)

    def test_public_helpers(self) -> None:
        validation = self.public.public.validate_url("example.com/sdk-smoke-python")
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["normalized"], "https://example.com/sdk-smoke-python")

        plans = self.public.public.plans()
        self.assertIn("free", plans["plans"])

        png = self.public.public.qr_code(url="https://example.com/sdk-smoke-python")
        self.assertIsInstance(png, bytes)
        self.assertTrue(png.startswith(b"\x89PNG"), "QR code should be a PNG")

    def test_links(self) -> None:
        links = self.client.links
        created = links.create(
            url="https://example.com/sdk-smoke-python",
            title=self.name("sdk-smoke-python"),
            workspace_public_id=WORKSPACE,
        )
        public_id = created["public_id"]
        self.addCleanup(_ignore_missing, links.delete, public_id)
        self.assertEqual(created["original_url"], "https://example.com/sdk-smoke-python")

        got = links.get(public_id)
        self.assertEqual(got["data"]["public_id"], public_id)

        new_title = self.name("sdk-smoke-python-renamed")
        links.update(public_id, title=new_title)
        self.assertEqual(links.get(public_id)["data"]["title"], new_title)

        listed = links.list(limit=100)
        self.assertIn(public_id, [link["public_id"] for link in listed["data"]])

        totals = self.client.analytics.link(public_id)
        self.assertIn("total_clicks", totals)

        with self.assertRaises(ShortnAPIError) as raised:
            links.set_ab_winner(public_id, variant="B")
        self.assertEqual(raised.exception.status, 409)
        self.assertEqual(raised.exception.code, "ab_test_not_running")

        links.delete(public_id)
        self.assertEqual(links.get(public_id)["data"]["status"], "suspended")
        links.enable(public_id)
        self.assertEqual(links.get(public_id)["data"]["status"], "active")
        links.delete(public_id)

    def test_link_not_found_error(self) -> None:
        with self.assertRaises(ShortnAPIError) as raised:
            self.client.links.get("00000000-0000-4000-8000-000000000000")
        self.assertEqual(raised.exception.status, 404)
        self.assertEqual(raised.exception.code, "link_not_found")

    def test_tags(self) -> None:
        tags = self.client.tags
        created = tags.create(WORKSPACE, name=self.name("sdk-py"), color="#3b82f6")
        tag_id = created["public_id"]
        self.addCleanup(_ignore_missing, tags.delete, tag_id)

        self.assertEqual(tags.get(tag_id)["name"], self.name("sdk-py"))
        updated = tags.update(tag_id, name=self.name("sdk-py2"), color="#16a34a")
        self.assertEqual(updated["name"], self.name("sdk-py2"))

        listed = tags.list(WORKSPACE)
        self.assertIn(tag_id, [tag["public_id"] for tag in listed["tags"] or []])

        deleted = tags.delete(tag_id)
        self.assertIn("links_updated", deleted)

    def test_utm_templates(self) -> None:
        templates = self.client.utm_templates
        created = templates.create(WORKSPACE, name=self.name("sdk-smoke-python"), utm_source="sdk", utm_medium="smoke")
        template_id = created["data"]["public_id"]
        self.addCleanup(_ignore_missing, templates.delete, template_id)

        updated = templates.update(
            template_id, name=self.name("sdk-smoke-python"), utm_source="sdk", utm_campaign="renamed"
        )
        self.assertEqual(updated["data"]["utm_campaign"], "renamed")
        self.assertEqual(updated["data"]["utm_medium"], "")

        listed = templates.list(WORKSPACE, include_team_scoped=True)
        self.assertIn(template_id, [t["public_id"] for t in listed["data"]])

        deleted = templates.delete(template_id, links="keep")
        self.assertTrue(deleted["data"]["deleted"])

    def test_teams(self) -> None:
        teams = self.client.teams
        created = teams.create(WORKSPACE, name=self.name("SDK smoke Python"), description="SDK smoke test")
        slug = created["slug"]
        self.addCleanup(_ignore_missing, teams.delete, slug, workspace=WORKSPACE)

        got = teams.get(slug, workspace=WORKSPACE)
        self.assertEqual(got["public_id"], created["public_id"])

        updated = teams.update(slug, name=self.name("SDK smoke Python renamed"), workspace=WORKSPACE)
        self.assertEqual(updated["name"], self.name("SDK smoke Python renamed"))

        listed = teams.list(WORKSPACE)
        self.assertIn(slug, [team["slug"] for team in listed["teams"] or []])

        self.assertTrue(teams.delete(slug, workspace=WORKSPACE)["success"])

    def test_destinations(self) -> None:
        destinations = self.client.destinations
        created = destinations.create(
            WORKSPACE,
            name=self.name("sdk-smoke-python"),
            type="webhook",
            config={"webhook_url": "https://example.com/hooks/sdk-smoke"},
        )
        destination_id = created["public_id"]
        self.addCleanup(_ignore_missing, destinations.delete, WORKSPACE, destination_id)

        updated = destinations.update(
            WORKSPACE, destination_id, name=self.name("sdk-smoke-python-renamed"), type="webhook"
        )
        self.assertTrue(updated["success"])

        listed = destinations.list(WORKSPACE)
        names = {d["public_id"]: d["name"] for d in listed}
        self.assertEqual(names.get(destination_id), self.name("sdk-smoke-python-renamed"))

        self.assertTrue(destinations.delete(WORKSPACE, destination_id)["success"])

    def test_reports(self) -> None:
        reports = self.client.reports
        # A paused weekly report, first run a year away, with no destinations: it can't send anything.
        first_run = (datetime.now(timezone.utc) + timedelta(days=365)).replace(microsecond=0)
        created = reports.create_rule(
            workspace_public_id=WORKSPACE,
            report_type="custom_builder_v1",
            schedule_type="every_x",
            interval_seconds=604800,
            initial_run_at=first_run.isoformat().replace("+00:00", "Z"),
            report_name=self.name("sdk-smoke-python"),
            enabled=False,
            destination_public_ids=[],
            definition_json={
                "version": "custom_builder.v1",
                "trigger": "scheduled",
                "sections": [{"id": "total_clicks", "order": 1, "settings": {"window": "7d"}}],
                "options": {"locale": "en-US"},
            },
        )
        rule_id = created["data"]["public_id"]
        self.addCleanup(_ignore_missing, reports.delete_rule, rule_id)
        if created["data"].get("enabled"):
            reports.update_rule(rule_id, enabled=False)

        got = reports.get_rule(rule_id)
        self.assertEqual(got["data"]["public_id"], rule_id)
        self.assertFalse(got["data"]["enabled"])

        updated = reports.update_rule(rule_id, report_name=self.name("sdk-smoke-python-renamed"))
        self.assertEqual(updated["data"]["public_id"], rule_id)

        listed = reports.list_rules(workspace_public_id=WORKSPACE, schedule_types=["every_x"])
        self.assertIn(rule_id, [rule["public_id"] for rule in listed["data"]])

        self.assertIsNone(reports.delete_rule(rule_id))

    def test_domains(self) -> None:
        listed = self.client.domains.list()
        self.assertIsInstance(listed["data"], list)

    @unittest.skipUnless(CLICK_ID, "set SHORTN_SMOKE_CLICK_ID")
    def test_conversions(self) -> None:
        conversions = self.client.conversions
        invoice_id = self.name("sdk-smoke-python-invoice")

        lead_args = dict(click_id=CLICK_ID, idempotency_key=self.name("sdk-smoke-python-lead"), test_mode=True)
        self.assertTrue(conversions.validate_lead(event_name="SDK smoke lead", **lead_args)["valid"])
        lead = conversions.track_lead(event_name="SDK smoke lead", lead_category="signup", **lead_args)
        self.assertEqual(lead["type"], "lead")
        self.assertTrue(lead["event"]["is_test"])

        sale_args = dict(click_id=CLICK_ID, currency="EUR", amount_cents=1000, invoice_id=invoice_id, test_mode=True)
        self.assertTrue(conversions.validate_sale(**sale_args)["valid"])
        sale = conversions.track_sale(idempotency_key=self.name("sdk-smoke-python-sale"), **sale_args)
        self.assertEqual(sale["type"], "sale")
        self.assertEqual(sale["event"]["amount_cents"], 1000)

        # By design, a test-mode refund names a live sale, so a test_mode sale can't be
        # refunded (404 conversion_sale_not_found), and the smoke test sends no live sales.
        # Both refund calls are still made; they must either succeed or fail that way.
        refund_args = dict(invoice_id=invoice_id, refund_id=self.name("sdk-smoke-python-refund"), test_mode=True)
        try:
            self.assertTrue(conversions.validate_refund(amount_cents=400, **refund_args)["valid"])
            refund = conversions.track_refund(amount_cents=400, reason="SDK smoke test", **refund_args)
            self.assertEqual(refund["type"], "refund")
        except ShortnAPIError as exc:
            self.assertEqual((exc.status, exc.code, exc.field), (404, "conversion_sale_not_found", "invoice_id"))
            with self.assertRaises(ShortnAPIError) as raised:
                conversions.track_refund(amount_cents=400, reason="SDK smoke test", **refund_args)
            self.assertEqual(raised.exception.code, "conversion_sale_not_found")
            print("\nby design: test_mode refunds of test_mode sales answer 404 conversion_sale_not_found",
                  file=sys.stderr)

        self.assertIn("data", conversions.summary())
        self.assertIn("data", conversions.attribution(environment="test", limit=10))
        self.assertIn("data", conversions.timeline(environment="test", interval="day"))
        events = conversions.events(environment="test", limit=10)
        self.assertEqual(events["environment"], "test")
        self.assertIn(sale["event"]["public_id"], [event["public_id"] for event in events["data"]])
        if LINK_CODE:
            by_link = conversions.events(environment="test", link=LINK_CODE, event_type="sale", limit=5)
            self.assertIn(sale["event"]["public_id"], [event["public_id"] for event in by_link["data"]])


if __name__ == "__main__":
    unittest.main()
