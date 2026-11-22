"""Every SDK method: HTTP method, path, query and JSON body, against a fake transport."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import make_client  # noqa: E402

WS = "8c0f6b52-4d0e-4a71-9a3e-2f6d1c7b5a10"
LINK = "3f6c1e2a-9b8d-4c7e-a1f0-5d2e3c4b6a71"

# (name, call, method, path, query, body). query/body None means "none sent".
CASES = [
    # links
    ("links.list", lambda c: c.links.list(), "GET", "/api/v1/links", None, None),
    ("links.list paged", lambda c: c.links.list(limit=100, offset=0), "GET", "/api/v1/links", {"limit": "100", "offset": "0"}, None),
    ("links.get", lambda c: c.links.get(LINK), "GET", f"/api/v1/links/{LINK}", None, None),
    (
        "links.create",
        lambda c: c.links.create(
            url="https://example.com/spring",
            title="Spring",
            workspace_public_id=WS,
            tag_public_ids=["t1"],
            utm_source="newsletter",
            ab_split_percent=0,
            preview_custom=False,
            description=None,
            attribution={"type": "campaign", "external_id": "spring"},
            targeting_geo_overrides=[{"target": "country:de", "url": "https://example.com/de"}],
        ),
        "POST",
        "/api/v1/links",
        None,
        {
            "url": "https://example.com/spring",
            "title": "Spring",
            "workspace_public_id": WS,
            "tag_public_ids": ["t1"],
            "utm_source": "newsletter",
            "ab_split_percent": 0,
            "preview_custom": False,
            "attribution": {"type": "campaign", "external_id": "spring"},
            "targeting_geo_overrides": [{"target": "country:de", "url": "https://example.com/de"}],
        },
    ),
    (
        "links.update",
        lambda c: c.links.update(LINK, title="New", description="", team_public_ids=[]),
        "PATCH",
        f"/api/v1/links/{LINK}",
        None,
        {"title": "New", "description": "", "team_public_ids": []},
    ),
    ("links.delete", lambda c: c.links.delete(LINK), "DELETE", f"/api/v1/links/{LINK}", None, None),
    ("links.enable", lambda c: c.links.enable(LINK), "POST", f"/api/v1/links/{LINK}/enable", None, None),
    (
        "links.set_ab_winner",
        lambda c: c.links.set_ab_winner(LINK, variant="B"),
        "POST",
        f"/api/v1/links/{LINK}/ab/winner",
        None,
        {"variant": "B"},
    ),
    # analytics
    ("analytics.link", lambda c: c.analytics.link(LINK), "GET", f"/api/v1/analytics/links/{LINK}", None, None),
    (
        "analytics.link query",
        lambda c: c.analytics.link(LINK, query={"future": "x", "unset": None}),
        "GET",
        f"/api/v1/analytics/links/{LINK}",
        {"future": "x"},
        None,
    ),
    # workspaces
    ("workspaces.list", lambda c: c.workspaces.list(), "GET", "/api/v1/workspaces", None, None),
    ("workspaces.get", lambda c: c.workspaces.get(WS), "GET", f"/api/v1/workspaces/{WS}", None, None),
    # tags
    ("tags.list", lambda c: c.tags.list(WS), "GET", f"/api/v1/workspaces/{WS}/tags", None, None),
    (
        "tags.list filtered",
        lambda c: c.tags.list(WS, team_public_ids=["a", "b"], report_scope=True),
        "GET",
        f"/api/v1/workspaces/{WS}/tags",
        {"team_public_ids": "a,b", "report_scope": "1"},
        None,
    ),
    ("tags.list team none", lambda c: c.tags.list(WS, team="none"), "GET", f"/api/v1/workspaces/{WS}/tags", {"team": "none"}, None),
    (
        "tags.create",
        lambda c: c.tags.create(WS, name="Spring", color="#3b82f6"),
        "POST",
        f"/api/v1/workspaces/{WS}/tags",
        None,
        {"name": "Spring", "color": "#3b82f6"},
    ),
    (
        "tags.create teams",
        lambda c: c.tags.create(WS, name="Spring", color="#3b82f6", team_public_ids=["t"]),
        "POST",
        f"/api/v1/workspaces/{WS}/tags",
        None,
        {"name": "Spring", "color": "#3b82f6", "team_public_ids": ["t"]},
    ),
    ("tags.get", lambda c: c.tags.get("tag-1"), "GET", "/api/v1/tags/tag-1", None, None),
    ("tags.update", lambda c: c.tags.update("tag-1", name="Renamed"), "PUT", "/api/v1/tags/tag-1", None, {"name": "Renamed"}),
    ("tags.update teams", lambda c: c.tags.update("tag-1", team_public_ids=[]), "PUT", "/api/v1/tags/tag-1", None, {"team_public_ids": []}),
    ("tags.delete", lambda c: c.tags.delete("tag-1"), "DELETE", "/api/v1/tags/tag-1", None, None),
    # utm templates
    ("utm_templates.list", lambda c: c.utm_templates.list(WS), "GET", f"/api/v1/workspaces/{WS}/utm-templates", None, None),
    (
        "utm_templates.list filtered",
        lambda c: c.utm_templates.list(WS, include_team_scoped=True, team_public_ids="a,b"),
        "GET",
        f"/api/v1/workspaces/{WS}/utm-templates",
        {"include_team_scoped": "1", "team_public_ids": "a,b"},
        None,
    ),
    (
        "utm_templates.create",
        lambda c: c.utm_templates.create(WS, name="Newsletter", utm_source="newsletter", utm_medium="email"),
        "POST",
        f"/api/v1/workspaces/{WS}/utm-templates",
        None,
        {"name": "Newsletter", "utm_source": "newsletter", "utm_medium": "email"},
    ),
    (
        "utm_templates.update",
        lambda c: c.utm_templates.update("tpl-1", name="Newsletter", utm_campaign="dec", lost_access_action="copy"),
        "PUT",
        "/api/v1/utm-templates/tpl-1",
        None,
        {"name": "Newsletter", "utm_campaign": "dec", "lost_access_action": "copy"},
    ),
    ("utm_templates.delete", lambda c: c.utm_templates.delete("tpl-1"), "DELETE", "/api/v1/utm-templates/tpl-1", None, None),
    (
        "utm_templates.delete clear",
        lambda c: c.utm_templates.delete("tpl-1", links="clear"),
        "DELETE",
        "/api/v1/utm-templates/tpl-1",
        {"links": "clear"},
        None,
    ),
    # destinations
    ("destinations.list", lambda c: c.destinations.list(WS), "GET", f"/api/v1/workspaces/{WS}/destinations", None, None),
    (
        "destinations.create",
        lambda c: c.destinations.create(WS, name="Hook", type="webhook", config={"webhook_url": "https://example.com/h"}),
        "POST",
        f"/api/v1/workspaces/{WS}/destinations",
        None,
        {"name": "Hook", "type": "webhook", "config": {"webhook_url": "https://example.com/h"}},
    ),
    (
        "destinations.update",
        lambda c: c.destinations.update(WS, "dst-1", name="Hook 2", type="webhook"),
        "PUT",
        f"/api/v1/workspaces/{WS}/destinations/dst-1",
        None,
        {"name": "Hook 2", "type": "webhook"},
    ),
    (
        "destinations.update config",
        lambda c: c.destinations.update(WS, "dst-1", name="Inbox", type="email", config={"to": ["a@example.com"]}, team_public_ids=[]),
        "PUT",
        f"/api/v1/workspaces/{WS}/destinations/dst-1",
        None,
        {"name": "Inbox", "type": "email", "config": {"to": ["a@example.com"]}, "team_public_ids": []},
    ),
    (
        "destinations.delete",
        lambda c: c.destinations.delete(WS, "dst-1"),
        "DELETE",
        f"/api/v1/workspaces/{WS}/destinations/dst-1",
        None,
        None,
    ),
    # teams
    ("teams.list", lambda c: c.teams.list(WS), "GET", f"/api/v1/workspaces/{WS}/teams", None, None),
    (
        "teams.create",
        lambda c: c.teams.create(WS, name="Paid Social", description="Ads"),
        "POST",
        f"/api/v1/workspaces/{WS}/teams",
        None,
        {"name": "Paid Social", "description": "Ads"},
    ),
    ("teams.create name only", lambda c: c.teams.create(WS, name="Paid"), "POST", f"/api/v1/workspaces/{WS}/teams", None, {"name": "Paid"}),
    ("teams.get", lambda c: c.teams.get("paid-social"), "GET", "/api/v1/teams/paid-social", None, None),
    (
        "teams.get workspace",
        lambda c: c.teams.get("paid-social", workspace=WS),
        "GET",
        "/api/v1/teams/paid-social",
        {"workspace": WS},
        None,
    ),
    (
        "teams.update",
        lambda c: c.teams.update("paid-social", name="Paid Social EU", workspace=WS),
        "PUT",
        "/api/v1/teams/paid-social",
        {"workspace": WS},
        {"name": "Paid Social EU"},
    ),
    ("teams.delete", lambda c: c.teams.delete("paid-social"), "DELETE", "/api/v1/teams/paid-social", None, None),
    (
        "teams.delete workspace",
        lambda c: c.teams.delete("paid-social", workspace=WS),
        "DELETE",
        "/api/v1/teams/paid-social",
        {"workspace": WS},
        None,
    ),
    # domains
    ("domains.list", lambda c: c.domains.list(), "GET", "/api/v1/domains", None, None),
    ("domains.create", lambda c: c.domains.create(domain="go.example.com"), "POST", "/api/v1/domains", None, {"domain": "go.example.com"}),
    ("domains.verify", lambda c: c.domains.verify(14), "POST", "/api/v1/domains/14/verify", None, None),
    ("domains.delete", lambda c: c.domains.delete(14), "DELETE", "/api/v1/domains/14", None, None),
    # reports
    ("reports.list_rules", lambda c: c.reports.list_rules(), "GET", "/api/v1/reports/rules", None, None),
    (
        "reports.list_rules filtered",
        lambda c: c.reports.list_rules(workspace_public_id=WS, schedule_types=["every_x", "event"], link_public_ids=[LINK], team_public_ids="t1"),
        "GET",
        "/api/v1/reports/rules",
        {"workspace_public_id": WS, "schedule_types": "every_x,event", "link_public_ids": LINK, "team_public_ids": "t1"},
        None,
    ),
    ("reports.get_rule", lambda c: c.reports.get_rule("rule-1"), "GET", "/api/v1/reports/rules/rule-1", None, None),
    (
        "reports.create_rule",
        lambda c: c.reports.create_rule(
            workspace_public_id=WS,
            report_type="custom_builder_v1",
            interval_seconds=604800,
            enabled=False,
            destination_public_ids=[],
            definition_json={"version": "custom_builder.v1", "trigger": "scheduled", "sections": []},
        ),
        "POST",
        "/api/v1/reports/rules",
        None,
        {
            "workspace_public_id": WS,
            "report_type": "custom_builder_v1",
            "interval_seconds": 604800,
            "enabled": False,
            "destination_public_ids": [],
            "definition_json": {"version": "custom_builder.v1", "trigger": "scheduled", "sections": []},
        },
    ),
    (
        "reports.update_rule",
        lambda c: c.reports.update_rule("rule-1", enabled=False),
        "PATCH",
        "/api/v1/reports/rules/rule-1",
        None,
        {"enabled": False},
    ),
    ("reports.delete_rule", lambda c: c.reports.delete_rule("rule-1"), "DELETE", "/api/v1/reports/rules/rule-1", None, None),
    # conversions: writes
    (
        "conversions.track_lead",
        lambda c: c.conversions.track_lead(click_id="clk_1", idempotency_key="lead-1", event_name="Sign up", lead_category="signup", test_mode=True),
        "POST",
        "/api/v1/conversions/leads",
        None,
        {"click_id": "clk_1", "idempotency_key": "lead-1", "event_name": "Sign up", "lead_category": "signup", "test_mode": True},
    ),
    (
        "conversions.validate_lead",
        lambda c: c.conversions.validate_lead(click_id="clk_1", idempotency_key="lead-1"),
        "POST",
        "/api/v1/conversions/leads/validations",
        None,
        {"click_id": "clk_1", "idempotency_key": "lead-1"},
    ),
    (
        "conversions.track_sale",
        lambda c: c.conversions.track_sale(
            click_id="clk_1",
            currency="EUR",
            amount_cents=4900,
            invoice_id="inv_1",
            settlement_amount_cents=5300,
            settlement_currency="USD",
            metadata={"plan": "pro"},
        ),
        "POST",
        "/api/v1/conversions/sales",
        None,
        {
            "click_id": "clk_1",
            "currency": "EUR",
            "amount_cents": 4900,
            "invoice_id": "inv_1",
            "settlement_amount_cents": 5300,
            "settlement_currency": "USD",
            "metadata": {"plan": "pro"},
        },
    ),
    (
        "conversions.validate_sale",
        lambda c: c.conversions.validate_sale(click_id="clk_1", currency="EUR", amount="49.00", idempotency_key="sale-1"),
        "POST",
        "/api/v1/conversions/sales/validations",
        None,
        {"click_id": "clk_1", "currency": "EUR", "amount": "49.00", "idempotency_key": "sale-1"},
    ),
    (
        "conversions.track_refund",
        lambda c: c.conversions.track_refund(invoice_id="inv_1", refund_id="re_1", amount_cents=1900, reason="Damaged"),
        "POST",
        "/api/v1/conversions/refunds",
        None,
        {"invoice_id": "inv_1", "refund_id": "re_1", "amount_cents": 1900, "reason": "Damaged"},
    ),
    (
        "conversions.validate_refund",
        lambda c: c.conversions.validate_refund(invoice_id="inv_1", refund_id="re_1", amount="19.00", currency="EUR"),
        "POST",
        "/api/v1/conversions/refunds/validations",
        None,
        {"invoice_id": "inv_1", "refund_id": "re_1", "amount": "19.00", "currency": "EUR"},
    ),
    # conversions: reads
    ("conversions.summary", lambda c: c.conversions.summary(), "GET", "/api/v1/conversions/summary", None, None),
    ("conversions.attribution", lambda c: c.conversions.attribution(), "GET", "/api/v1/conversions/attribution", None, None),
    (
        "conversions.attribution query",
        lambda c: c.conversions.attribution(from_=date(2026, 11, 1), to="2026-11-14", environment="test", limit=10),
        "GET",
        "/api/v1/conversions/attribution",
        {"from": "2026-11-01", "to": "2026-11-14", "environment": "test", "limit": "10"},
        None,
    ),
    (
        "conversions.timeline",
        lambda c: c.conversions.timeline(environment="test", interval="week"),
        "GET",
        "/api/v1/conversions/timeline",
        {"environment": "test", "interval": "week"},
        None,
    ),
    (
        "conversions.events",
        lambda c: c.conversions.events(
            from_="2026-11-01T00:00:00Z",
            environment="test",
            limit=25,
            offset=50,
            event_type="sale",
            lead_category="signup",
            event_origin="observed",
            link="abC12x9",
            event="evt-1",
            q="spring sale",
            include_total=True,
        ),
        "GET",
        "/api/v1/conversions/events",
        {
            "from": "2026-11-01T00:00:00Z",
            "environment": "test",
            "limit": "25",
            "offset": "50",
            "event_type": "sale",
            "lead_category": "signup",
            "event_origin": "observed",
            "link": "abC12x9",
            "event": "evt-1",
            "q": "spring sale",
            "include_total": "1",
        },
        None,
    ),
    # public
    (
        "public.validate_url",
        lambda c: c.public.validate_url("example.com/menu"),
        "GET",
        "/api/v1/validate",
        {"url": "example.com/menu"},
        None,
    ),
    ("public.plans", lambda c: c.public.plans(), "GET", "/api/v1/plans", None, None),
    (
        "public.qr_code",
        lambda c: c.public.qr_code(url="https://shtnl.ink/abC12x9", format="svg", size="download", color_mode="flat", fg="1f2937", frameTemplate="scan", frame_text_follows_background=False),
        "GET",
        "/api/v1/qr",
        {
            "url": "https://shtnl.ink/abC12x9",
            "format": "svg",
            "size": "download",
            "colorMode": "flat",
            "fg": "1f2937",
            "frameTemplate": "scan",
            "frameTextFollowsBackground": "false",
        },
        None,
    ),
]


class EveryMethodTest(unittest.TestCase):
    def test_every_method(self) -> None:
        for name, call, method, path, query, body in CASES:
            with self.subTest(name):
                client, transport = make_client((200, {"ok": True}))
                call(client)
                self.assertEqual(len(transport.requests), 1)
                sent = transport.last
                self.assertEqual(sent["method"], method)
                self.assertEqual(sent["path"], path)
                self.assertEqual(sent["query"], query or {})
                self.assertEqual(sent["body"], body)
                if name.startswith("public."):
                    self.assertNotIn("Authorization", sent["headers"])
                else:
                    self.assertEqual(sent["headers"]["Authorization"], "Bearer sk_live_test")
                if body is None:
                    self.assertNotIn("Content-Type", sent["headers"])
                else:
                    self.assertEqual(sent["headers"]["Content-Type"], "application/json")

    def test_every_group_and_method_is_covered(self) -> None:
        client, _ = make_client()
        groups = [
            "links", "analytics", "workspaces", "tags", "utm_templates", "destinations",
            "teams", "domains", "reports", "conversions", "public",
        ]
        public_methods = {
            f"{group}.{attr}"
            for group in groups
            for attr in dir(getattr(client, group))
            if not attr.startswith("_") and callable(getattr(getattr(client, group), attr))
        }
        tested = {name.split(" ")[0] for name, *_ in CASES}
        self.assertEqual(public_methods - tested, set())
        self.assertEqual(len(public_methods), 50)

    def test_responses_are_returned_as_decoded_json(self) -> None:
        payload = {"data": {"public_id": LINK, "brand_new_field": {"nested": [1, 2]}}}
        client, _ = make_client((200, payload))
        self.assertEqual(client.links.get(LINK), payload)

    def test_list_responses_stay_lists(self) -> None:
        client, _ = make_client((200, [{"public_id": "dst-1", "type": "email"}]))
        self.assertEqual(client.destinations.list(WS), [{"public_id": "dst-1", "type": "email"}])

    def test_delete_rule_returns_none_on_204(self) -> None:
        client, transport = make_client((204, b""))
        self.assertIsNone(client.reports.delete_rule("rule-1"))
        self.assertEqual(transport.last["method"], "DELETE")

    def test_qr_code_returns_bytes_with_image_accept(self) -> None:
        png = b"\x89PNG\r\n\x1a\nrest"
        client, transport = make_client((200, png, {"Content-Type": "image/png"}), api_key=None)
        self.assertEqual(client.public.qr_code(url="https://shtnl.ink/abc"), png)
        self.assertEqual(transport.last["headers"]["Accept"], "image/*")
        self.assertEqual(transport.last["query"], {"url": "https://shtnl.ink/abc"})

    def test_qr_code_svg_accept(self) -> None:
        client, transport = make_client((200, b"<svg/>", {"Content-Type": "image/svg+xml"}), api_key=None)
        self.assertEqual(client.public.qr_code(url="https://shtnl.ink/abc", format="svg"), b"<svg/>")
        self.assertEqual(transport.last["headers"]["Accept"], "image/svg+xml")


class PathEscapingTest(unittest.TestCase):
    def test_path_segments_are_escaped(self) -> None:
        client, transport = make_client()
        client.links.get("a/b?c#d e")
        self.assertEqual(transport.last["url"], "https://api.example.test/api/v1/links/a%2Fb%3Fc%23d%20e")

        client.teams.get("../workspaces", workspace=WS)
        self.assertTrue(transport.last["url"].startswith("https://api.example.test/api/v1/teams/..%2Fworkspaces?"))

        client.destinations.update("w/1", "d/2", name="n", type="email")
        self.assertEqual(transport.last["url"], "https://api.example.test/api/v1/workspaces/w%2F1/destinations/d%2F2")

        client.tags.get("ünï")
        self.assertEqual(transport.last["url"], "https://api.example.test/api/v1/tags/%C3%BCn%C3%AF")

    def test_empty_path_parameter_is_refused(self) -> None:
        client, transport = make_client()
        for call in (
            lambda: client.links.get(""),
            lambda: client.links.delete("  "),
            lambda: client.tags.update(None, name="x"),  # type: ignore[arg-type]
            lambda: client.destinations.delete(WS, ""),
        ):
            with self.assertRaises(ValueError):
                call()
        self.assertEqual(transport.requests, [])

    def test_query_values_are_escaped(self) -> None:
        client, transport = make_client()
        client.conversions.events(q="a&b=c d", link="https://shtnl.ink/x?y")
        self.assertEqual(transport.last["raw_query"], "link=https%3A%2F%2Fshtnl.ink%2Fx%3Fy&q=a%26b%3Dc%20d")
        self.assertEqual(transport.last["query"], {"q": "a&b=c d", "link": "https://shtnl.ink/x?y"})


if __name__ == "__main__":
    unittest.main()
