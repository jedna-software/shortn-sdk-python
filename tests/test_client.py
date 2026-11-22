"""Client behaviour: configuration, headers, error mapping and retry rules."""

from __future__ import annotations

import email.message
import io
import socket
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib import response as urlresponse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import BASE, FakeTransport, make_client  # noqa: E402

from shortn_sdk import client as client_module  # noqa: E402
from shortn_sdk import (  # noqa: E402
    RetryOptions,
    Shortn,
    ShortnAPIError,
    ShortnConfigurationError,
    ShortnError,
    ShortnNetworkError,
    __version__,
)

SLEEP = "shortn_sdk.client.time.sleep"


class ConfigurationTest(unittest.TestCase):
    def test_default_base_url_and_user_agent(self) -> None:
        transport = FakeTransport()
        client = Shortn("sk_live_test", transport=transport)
        client.workspaces.list()
        self.assertEqual(transport.last["url"], "https://app.shortn.link/api/v1/workspaces")
        self.assertEqual(transport.last["headers"]["User-Agent"], f"shortn-sdk-python/{__version__}")
        self.assertEqual(transport.last["headers"]["Accept"], "application/json")
        self.assertEqual(__version__, "0.1.0")

    def test_base_url_is_normalized(self) -> None:
        for base in ("https://dev.example.test/", "https://dev.example.test/api/v1", "https://dev.example.test/api/v1/"):
            with self.subTest(base):
                transport = FakeTransport()
                Shortn("k", base_url=base, transport=transport).domains.list()
                self.assertEqual(transport.last["url"], "https://dev.example.test/api/v1/domains")

    def test_invalid_base_url_is_a_configuration_error(self) -> None:
        for base in ("app.shortn.link", "ftp://app.shortn.link", "https://", "https:///api/v1", "http://[::1"):
            with self.subTest(base):
                with self.assertRaises(ShortnConfigurationError):
                    Shortn("k", base_url=base, transport=FakeTransport())

    def test_http_base_url_is_allowed(self) -> None:
        transport = FakeTransport()
        Shortn("k", base_url="http://localhost:8080", transport=transport).domains.list()
        self.assertEqual(transport.last["url"], "http://localhost:8080/api/v1/domains")

    def test_user_agent_suffix_and_timeout(self) -> None:
        client, transport = make_client(user_agent="my-app/2.0", timeout=7.5)
        client.workspaces.list()
        self.assertEqual(transport.last["headers"]["User-Agent"], f"shortn-sdk-python/{__version__} my-app/2.0")
        self.assertEqual(transport.last["timeout"], 7.5)

    def test_api_key_is_trimmed_and_sent_as_bearer(self) -> None:
        client, transport = make_client(api_key="  sk_live_abc \n")
        client.links.list()
        self.assertEqual(transport.last["headers"]["Authorization"], "Bearer sk_live_abc")
        self.assertNotIn("sk_live_abc", repr(client))

    def test_keyed_endpoints_need_a_key(self) -> None:
        client, transport = make_client(api_key=None)
        with self.assertRaises(ShortnConfigurationError):
            client.links.list()
        with self.assertRaises(ShortnConfigurationError):
            client.conversions.track_lead(click_id="c", idempotency_key="k")
        self.assertEqual(transport.requests, [])

    def test_public_helpers_work_without_a_key(self) -> None:
        client, transport = make_client((200, {"valid": True}), api_key=None)
        client.public.validate_url("example.com")
        client.public.plans()
        self.assertNotIn("Authorization", transport.requests[0]["headers"])
        self.assertNotIn("Authorization", transport.requests[1]["headers"])

    def test_public_helpers_never_send_the_key(self) -> None:
        client, transport = make_client((200, {"plans": {}}))
        client.public.validate_url("example.com")
        client.public.qr_code(url="https://example.com")
        client.public.plans()
        self.assertEqual(len(transport.requests), 3)
        for sent in transport.requests:
            self.assertNotIn("Authorization", sent["headers"])
        client.request("GET", "/future", auth=False)
        self.assertNotIn("Authorization", transport.last["headers"])

    def test_only_set_query_params_are_sent(self) -> None:
        client, transport = make_client()
        client.links.list(limit=None, offset=None)
        self.assertEqual(transport.last["url"], f"{BASE}/api/v1/links")
        client.conversions.events(limit=0)
        self.assertEqual(transport.last["raw_query"], "limit=0")

    def test_none_fields_are_left_out_of_bodies_but_falsy_values_stay(self) -> None:
        client, transport = make_client()
        client.links.update("id", title=None, description="", active=False, team_public_ids=[])
        self.assertEqual(transport.last["body"], {"description": "", "active": False, "team_public_ids": []})

    def test_dates_in_bodies_are_rfc3339_utc(self) -> None:
        cet = timezone(timedelta(hours=1))
        cases = [
            (datetime(2026, 11, 22, 10, 30, tzinfo=cet), "2026-11-22T09:30:00Z"),
            (datetime(2026, 11, 22, 10, 30, 5, 250000, tzinfo=timezone.utc), "2026-11-22T10:30:05.250000Z"),
            (datetime(2026, 11, 22, 10, 30), "2026-11-22T10:30:00Z"),  # naive: taken as UTC
            (date(2026, 11, 22), "2026-11-22T00:00:00Z"),
        ]
        for value, expected in cases:
            with self.subTest(value):
                client, transport = make_client()
                client.conversions.track_lead(click_id="c", idempotency_key="k", occurred_at=value)
                self.assertEqual(transport.last["body"]["occurred_at"], expected)

    def test_link_schedule_dates_are_rfc3339_utc(self) -> None:
        client, transport = make_client()
        client.links.create(
            url="https://example.com",
            title="t",
            starts_at=date(2026, 12, 1),
            expires_at=datetime(2026, 12, 31, 23, 0, tzinfo=timezone(timedelta(hours=-5))),
        )
        self.assertEqual(transport.last["body"]["starts_at"], "2026-12-01T00:00:00Z")
        self.assertEqual(transport.last["body"]["expires_at"], "2027-01-01T04:00:00Z")

    def test_generic_request_for_uncovered_endpoints(self) -> None:
        client, transport = make_client((200, {"ok": True}))
        self.assertEqual(client.request("get", "/future", query={"a": 1}), {"ok": True})
        self.assertEqual(transport.last["method"], "GET")
        self.assertEqual(transport.last["url"], f"{BASE}/api/v1/future?a=1")


class ErrorMappingTest(unittest.TestCase):
    def test_structured_error(self) -> None:
        body = {
            "code": "conversion_identity_required",
            "error": "idempotency_key is required",
            "hint": "Send a stable key.",
            "details": {"field": "idempotency_key"},
            "request_id": "req_123",
        }
        client, _ = make_client((400, body))
        with self.assertRaises(ShortnAPIError) as raised:
            client.conversions.track_lead(click_id="clk", idempotency_key="")
        err = raised.exception
        self.assertEqual(err.status, 400)
        self.assertEqual(err.status_code, 400)
        self.assertEqual(err.code, "conversion_identity_required")
        self.assertEqual(err.message, "idempotency_key is required")
        self.assertEqual(err.hint, "Send a stable key.")
        self.assertEqual(err.field, "idempotency_key")
        self.assertEqual(err.details, {"field": "idempotency_key"})
        self.assertEqual(err.request_id, "req_123")
        self.assertEqual(err.body, body)
        self.assertIn(b"conversion_identity_required", err.raw_body)
        self.assertEqual(str(err), "400 conversion_identity_required: idempotency_key is required")
        self.assertIsInstance(err, ShortnError)

    def test_plan_limit_fields_stay_reachable(self) -> None:
        body = {
            "code": "plan_limit_exceeded",
            "error": "Active links limit reached",
            "feature": "active_links",
            "limit": 25,
            "current": 25,
            "required_plan": None,
            "upgrade_url": "/profile/billing",
        }
        client, _ = make_client((403, body))
        with self.assertRaises(ShortnAPIError) as raised:
            client.links.create(url="https://example.com", title="x")
        self.assertEqual(raised.exception.body["feature"], "active_links")
        self.assertEqual(raised.exception.body["limit"], 25)
        self.assertIsNone(raised.exception.details)
        self.assertIsNone(raised.exception.field)

    def test_error_only_envelope(self) -> None:
        client, _ = make_client((404, {"error": "team not found"}))
        with self.assertRaises(ShortnAPIError) as raised:
            client.teams.get("nope")
        self.assertIsNone(raised.exception.code)
        self.assertEqual(raised.exception.message, "team not found")
        self.assertEqual(str(raised.exception), "404: team not found")

    def test_request_id_header_and_retry_after(self) -> None:
        headers = {"Content-Type": "application/json", "Shortn-Request-Id": "req_h", "Retry-After": "12"}
        client, _ = make_client((409, {"code": "conversion_idempotency_conflict", "error": "conflict"}, headers))
        with self.assertRaises(ShortnAPIError) as raised:
            client.conversions.track_sale(click_id="c", currency="EUR")
        self.assertEqual(raised.exception.request_id, "req_h")
        self.assertEqual(raised.exception.retry_after, 12.0)
        self.assertEqual(raised.exception.headers["shortn-request-id"], "req_h")

    def test_non_json_error_body(self) -> None:
        client, _ = make_client((502, b"<html>Bad gateway</html>", {"Content-Type": "text/html"}))
        with self.assertRaises(ShortnAPIError) as raised:
            client.domains.list()
        self.assertEqual(raised.exception.status, 502)
        self.assertEqual(raised.exception.body, "<html>Bad gateway</html>")
        self.assertEqual(raised.exception.raw_body, b"<html>Bad gateway</html>")
        self.assertIsNone(raised.exception.code)

    def test_empty_error_body(self) -> None:
        client, _ = make_client((500, b""))
        with self.assertRaises(ShortnAPIError) as raised:
            client.domains.list()
        self.assertEqual(raised.exception.message, "Shortn API request failed with status 500")

    def test_invalid_json_on_success(self) -> None:
        client, _ = make_client((200, b"not json"))
        with self.assertRaises(ShortnError):
            client.domains.list()

    def test_network_error(self) -> None:
        client, _ = make_client(urlerror.URLError("connection refused"), retry=False)
        with self.assertRaises(ShortnNetworkError) as raised:
            client.domains.list()
        self.assertIsInstance(raised.exception.__cause__, urlerror.URLError)

    def test_transport_bugs_are_not_hidden(self) -> None:
        client, transport = make_client(KeyError("bug"))
        with self.assertRaises(KeyError):
            client.domains.list()
        self.assertEqual(len(transport.requests), 1)


class RetryTest(unittest.TestCase):
    def test_get_is_retried_on_429_honouring_retry_after(self) -> None:
        client, transport = make_client(
            (429, {"code": "api_rate_limit_exceeded", "error": "slow down"}, {"Retry-After": "3"}),
            (200, {"data": []}),
        )
        with mock.patch(SLEEP) as sleep:
            self.assertEqual(client.links.list(), {"data": []})
        self.assertEqual(len(transport.requests), 2)
        sleep.assert_called_once_with(3.0)

    def test_retry_after_above_the_cap_raises_without_waiting(self) -> None:
        client, transport = make_client(
            (429, {"code": "api_monthly_limit_exceeded", "error": "monthly limit"}, {"Retry-After": "864000"}),
            (200, {}),
            retry=RetryOptions(max_retry_after=5, jitter=False),
        )
        with mock.patch(SLEEP) as sleep:
            with self.assertRaises(ShortnAPIError) as raised:
                client.links.list()
        sleep.assert_not_called()
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(raised.exception.code, "api_monthly_limit_exceeded")
        self.assertEqual(raised.exception.retry_after, 864000.0)

    def test_retry_after_at_the_cap_is_waited_for(self) -> None:
        client, transport = make_client(
            (429, {"error": "slow down"}, {"Retry-After": "5"}),
            (200, {}),
            retry=RetryOptions(max_retry_after=5, jitter=False),
        )
        with mock.patch(SLEEP) as sleep:
            client.links.list()
        sleep.assert_called_once_with(5.0)
        self.assertEqual(len(transport.requests), 2)

    def test_retry_after_http_date(self) -> None:
        client, _ = make_client(
            (503, {"error": "busy"}, {"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}),
            (200, {}),
        )
        with mock.patch(SLEEP) as sleep:
            client.workspaces.list()
        sleep.assert_not_called()  # a date in the past means "now"

    def test_503_is_retried_with_backoff_until_attempts_run_out(self) -> None:
        client, transport = make_client(
            (503, {"error": "Failed to get analytics"}),
            retry=RetryOptions(max_retries=3, initial_delay=0.5, backoff_factor=2, max_delay=1.5, jitter=False),
        )
        with mock.patch(SLEEP) as sleep:
            with self.assertRaises(ShortnAPIError) as raised:
                client.analytics.link("id")
        self.assertEqual(raised.exception.status, 503)
        self.assertEqual(len(transport.requests), 4)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.5, 1.0, 1.5])

    def test_other_statuses_are_not_retried(self) -> None:
        for status in (400, 401, 403, 404, 409, 500, 502):
            with self.subTest(status):
                client, transport = make_client((status, {"error": "no"}))
                with self.assertRaises(ShortnAPIError):
                    client.workspaces.list()
                self.assertEqual(len(transport.requests), 1)

    def test_put_and_delete_are_retried(self) -> None:
        for call in (lambda c: c.tags.update("t", name="n"), lambda c: c.tags.delete("t")):
            client, transport = make_client((503, {"error": "busy"}), (200, {}))
            with mock.patch(SLEEP):
                call(client)
            self.assertEqual(len(transport.requests), 2)

    def test_patch_and_plain_post_are_not_retried(self) -> None:
        calls = [
            lambda c: c.links.update("l", title="t"),
            lambda c: c.links.create(url="https://example.com", title="t"),
            lambda c: c.links.enable("l"),
            lambda c: c.reports.create_rule(report_type="custom_builder_v1"),
            lambda c: c.conversions.track_sale(click_id="c", currency="EUR", invoice_id="inv"),
            lambda c: c.conversions.track_refund(invoice_id="inv", refund_id="re"),
        ]
        for index, call in enumerate(calls):
            with self.subTest(index):
                client, transport = make_client((429, {"error": "slow down"}), (200, {}))
                with mock.patch(SLEEP):
                    with self.assertRaises(ShortnAPIError):
                        call(client)
                self.assertEqual(len(transport.requests), 1)

    def test_post_with_idempotency_key_is_retried(self) -> None:
        calls = [
            lambda c: c.conversions.track_lead(click_id="c", idempotency_key="lead-1"),
            lambda c: c.conversions.track_sale(click_id="c", currency="EUR", idempotency_key="sale-1"),
            lambda c: c.conversions.track_refund(invoice_id="i", refund_id="r", idempotency_key="refund-1"),
            lambda c: c.conversions.validate_lead(click_id="c", idempotency_key="lead-1"),
        ]
        for index, call in enumerate(calls):
            with self.subTest(index):
                client, transport = make_client((503, {"error": "busy"}), (200, {"type": "lead"}))
                with mock.patch(SLEEP):
                    call(client)
                self.assertEqual(len(transport.requests), 2)
                self.assertEqual(transport.requests[0]["raw_body"], transport.requests[1]["raw_body"])

    def test_test_mode_posts_are_never_retried(self) -> None:
        calls = [
            lambda c: c.conversions.track_lead(click_id="c", idempotency_key="lead-1", test_mode=True),
            lambda c: c.conversions.track_sale(click_id="c", currency="EUR", idempotency_key="sale-1", test_mode=True),
            lambda c: c.conversions.track_refund(invoice_id="i", refund_id="r", idempotency_key="re-1", test_mode=True),
        ]
        for index, call in enumerate(calls):
            for failure in ((503, {"error": "busy"}), ConnectionResetError()):
                with self.subTest(index=index, failure=failure):
                    client, transport = make_client(failure, (200, {}))
                    with mock.patch(SLEEP) as sleep:
                        with self.assertRaises((ShortnAPIError, ShortnNetworkError)):
                            call(client)
                    self.assertEqual(len(transport.requests), 1)
                    sleep.assert_not_called()

    def test_test_mode_false_keeps_the_idempotency_retry(self) -> None:
        client, transport = make_client((503, {"error": "busy"}), (200, {}))
        with mock.patch(SLEEP):
            client.conversions.track_lead(click_id="c", idempotency_key="lead-1", test_mode=False)
        self.assertEqual(len(transport.requests), 2)

    def test_blank_idempotency_key_is_not_retried(self) -> None:
        client, transport = make_client((503, {"error": "busy"}), (200, {}))
        with mock.patch(SLEEP):
            with self.assertRaises(ShortnAPIError):
                client.conversions.track_lead(click_id="c", idempotency_key="  ")
        self.assertEqual(len(transport.requests), 1)

    def test_network_errors_are_retried_for_safe_requests(self) -> None:
        client, transport = make_client(socket.timeout("timed out"), ConnectionResetError(), (200, {"data": []}))
        with mock.patch(SLEEP):
            self.assertEqual(client.workspaces.list(), {"data": []})
        self.assertEqual(len(transport.requests), 3)

    def test_network_errors_on_unsafe_posts_are_not_retried(self) -> None:
        client, transport = make_client(ConnectionResetError(), (200, {}))
        with self.assertRaises(ShortnNetworkError):
            client.links.create(url="https://example.com", title="t")
        self.assertEqual(len(transport.requests), 1)

    def test_network_error_after_last_attempt(self) -> None:
        client, transport = make_client(urlerror.URLError("down"), retry=RetryOptions(max_retries=1, initial_delay=0))
        with self.assertRaises(ShortnNetworkError):
            client.workspaces.list()
        self.assertEqual(len(transport.requests), 2)

    def test_retries_can_be_turned_off(self) -> None:
        for retry in (False, RetryOptions(enabled=False), RetryOptions(max_retries=0)):
            with self.subTest(retry):
                client, transport = make_client((429, {"error": "slow"}), (200, {}), retry=retry)
                with mock.patch(SLEEP) as sleep:
                    with self.assertRaises(ShortnAPIError):
                        client.workspaces.list()
                self.assertEqual(len(transport.requests), 1)
                sleep.assert_not_called()

    def test_jitter_stays_within_bounds(self) -> None:
        client, _ = make_client(
            (503, {"error": "busy"}), (200, {}), retry=RetryOptions(initial_delay=2.0, jitter=True)
        )
        with mock.patch(SLEEP) as sleep:
            client.workspaces.list()
        delay = sleep.call_args.args[0]
        self.assertTrue(1.0 <= delay <= 2.0, delay)


class _FakeHTTPHandler(urlrequest.BaseHandler):
    """Answers every ``http://`` request from a list, before urllib's real handler."""

    handler_order = 100

    def __init__(self, *responses: tuple[int, dict[str, str], bytes]) -> None:
        self.responses = list(responses)
        self.requests: list[urlrequest.Request] = []

    def http_open(self, req: urlrequest.Request) -> urlresponse.addinfourl:
        self.requests.append(req)
        status, headers, body = self.responses.pop(0)
        message = email.message.Message()
        for name, value in headers.items():
            message[name] = value
        resp = urlresponse.addinfourl(io.BytesIO(body), message, req.full_url, status)
        resp.msg = "Fake"  # type: ignore[attr-defined]
        return resp


class UrllibTransportTest(unittest.TestCase):
    def _client(self, handler: _FakeHTTPHandler) -> Shortn:
        patcher = mock.patch.object(client_module, "_OPENER", client_module._build_opener(handler))
        patcher.start()
        self.addCleanup(patcher.stop)
        return Shortn("sk_live_test", base_url="http://api.example.test", retry=False)

    def test_success_and_error_statuses(self) -> None:
        handler = _FakeHTTPHandler(
            (200, {"Content-Type": "application/json"}, b'{"data": []}'),
            (404, {"Content-Type": "application/json"}, b'{"error": "not found"}'),
        )
        client = self._client(handler)
        self.assertEqual(client.workspaces.list(), {"data": []})
        with self.assertRaises(ShortnAPIError) as raised:
            client.teams.get("nope")
        self.assertEqual(raised.exception.status, 404)

    def test_redirects_are_not_followed(self) -> None:
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status):
                handler = _FakeHTTPHandler(
                    (status, {"Location": "http://elsewhere.example.test/collect"}, b""),
                    (200, {"Content-Type": "application/json"}, b"{}"),
                )
                client = self._client(handler)
                with self.assertRaises(ShortnAPIError) as raised:
                    client.links.create(url="https://example.com", title="t")
                self.assertEqual(raised.exception.status, status)
                self.assertEqual(raised.exception.headers["location"], "http://elsewhere.example.test/collect")
                self.assertEqual(len(handler.requests), 1)
                self.assertEqual(handler.requests[0].get_method(), "POST")


if __name__ == "__main__":
    unittest.main()
