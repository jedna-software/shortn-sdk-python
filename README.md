# Shortn Python SDK

Python client for the [Shortn](https://shortn.link) public API (`/api/v1`): links, link
analytics, workspaces, tags, UTM templates, report destinations, teams, custom domains,
report and alert rules, conversions, and the key-less public helpers.

- Python 3.10 or newer, no dependencies (standard-library HTTP).
- Typed: every method has type hints, and request fields and responses are described by
  `TypedDict` classes in `shortn_sdk.types`.
- For trusted server-side code only. Never put an API key in a browser, mobile or desktop
  app.

API reference: <https://docs.shortn.link/docs/api/>.

## Install

```sh
pip install shortn-sdk
```

The import name is `shortn_sdk`.

## Quick start

Create an API key under **Profile → API keys** and give it the scopes you need.

```python
import os

from shortn_sdk import Shortn

shortn = Shortn(os.environ["SHORTN_API_KEY"])

workspace = shortn.workspaces.list()["data"][0]
link = shortn.links.create(
    url="https://example.com/spring",
    title="Spring campaign",
    workspace_public_id=workspace["public_id"],
    utm_source="newsletter",
)
print(link["short_url"])
```

Every method returns the API's decoded JSON as plain `dict`/`list` objects, so fields the
API adds later are there without an SDK update. Parameters are keyword-only, except the
IDs in the path, and are named like the API's JSON fields. Parameters you don't pass (or
pass as `None`) are not sent.

## Configuration

```python
from shortn_sdk import RetryOptions, Shortn

shortn = Shortn(
    os.environ["SHORTN_API_KEY"],
    base_url="https://app.shortn.link",  # the SDK appends /api/v1
    timeout=10,                           # seconds per attempt
    retry=RetryOptions(max_retries=3),    # or retry=False
    user_agent="my-app/1.0",              # appended to shortn-sdk-python/0.1.0
)
```

`transport=` replaces the HTTP layer, for tests or a custom HTTP stack. A transport is a
callable `(method, url, headers, body, timeout) -> (status, headers, body)`; see
`shortn_sdk.Transport`.

## Resources

| Attribute | Methods | API |
|---|---|---|
| `links` | `list`, `get`, `create`, `update`, `delete`, `enable`, `set_ab_winner` | `/links` |
| `analytics` | `link` | `/analytics/links/{public_id}` |
| `workspaces` | `list`, `get` | `/workspaces` |
| `tags` | `list`, `create`, `get`, `update`, `delete` | `/workspaces/{id}/tags`, `/tags/{id}` |
| `utm_templates` | `list`, `create`, `update`, `delete` | `/workspaces/{id}/utm-templates`, `/utm-templates/{id}` |
| `destinations` | `list`, `create`, `update`, `delete` | `/workspaces/{id}/destinations[/{id}]` |
| `teams` | `list`, `create`, `get`, `update`, `delete` | `/workspaces/{id}/teams`, `/teams/{slug}` |
| `domains` | `list`, `create`, `verify`, `delete` | `/domains` |
| `reports` | `list_rules`, `get_rule`, `create_rule`, `update_rule`, `delete_rule` | `/reports/rules` |
| `conversions` | `track_lead`, `validate_lead`, `track_sale`, `validate_sale`, `track_refund`, `validate_refund`, `summary`, `attribution`, `timeline`, `events` | `/conversions/...` |
| `public` (no key) | `validate_url`, `qr_code`, `plans` | `/validate`, `/qr`, `/plans` |

For an endpoint the SDK doesn't cover yet, `shortn.request("GET", "/path", query={...})`
sends an authenticated request and decodes the answer.

### Links

Links are identified by their `public_id`, not by the short code.

```python
page = shortn.links.list(limit=100)
for item in page["data"]:
    print(item["short_code"], item["clicks"])
if page["pagination"]["has_more"]:
    page = shortn.links.list(limit=100, offset=page["pagination"]["next_offset"])

link = shortn.links.get(public_id)["data"]
shortn.links.update(public_id, title="Spring sale", url="https://example.com/spring-sale")
shortn.links.delete(public_id)   # suspends the link; analytics are kept
shortn.links.enable(public_id)   # active again
shortn.links.set_ab_winner(public_id, variant="B")
```

`links.create` takes every documented field as a keyword argument: `custom_code`,
`short_domain`, `team_public_ids`, `tag_public_ids`, `utm_template_id`, `utm_*`,
`starts_at`, `expires_at`, `expiration_action`, `access_mode`, `password`,
`targeting_geo_overrides`, `device_targets`, `ab_variants`, `conversion_enabled`,
`attribution`, `preview_*`, `cloaking_enabled` and more (see `LinkCreateParams`).

### Analytics

```python
totals = shortn.analytics.link(public_id)
print(totals["total_clicks"], totals["unique_clicks"], totals["clicks_by_country"])
```

### Workspaces

```python
for ws in shortn.workspaces.list()["data"]:
    print(ws["public_id"], ws["name"], ws["role"])
workspace = shortn.workspaces.get(workspace_id)["data"]
```

### Tags

```python
tag = shortn.tags.create(workspace_id, name="Spring", color="#14b8a6")
shortn.tags.update(tag["public_id"], name="Spring 2027")
shortn.tags.list(workspace_id, team="none")["tags"]
shortn.tags.delete(tag["public_id"])
```

### UTM templates

```python
template = shortn.utm_templates.create(
    workspace_id, name="Newsletter", utm_source="newsletter", utm_medium="email"
)["data"]
# PUT replaces the template: send every value you want to keep.
shortn.utm_templates.update(
    template["public_id"], name="Newsletter", utm_source="newsletter", utm_campaign="december"
)
shortn.utm_templates.list(workspace_id, include_team_scoped=True)
shortn.utm_templates.delete(template["public_id"], links="keep")
```

### Destinations

```python
hook = shortn.destinations.create(
    workspace_id, name="Ops webhook", type="webhook", config={"webhook_url": "https://example.com/hooks/shortn"}
)
shortn.destinations.update(workspace_id, hook["public_id"], name="Ops webhook (EU)", type="webhook")
shortn.destinations.list(workspace_id)   # a list
shortn.destinations.delete(workspace_id, hook["public_id"])
```

### Teams

Teams are read, changed and archived by `slug`. Pass `workspace=` when the key reaches
several workspaces that use the same slug.

```python
team = shortn.teams.create(workspace_id, name="Paid Social")
shortn.teams.get(team["slug"], workspace=workspace_id)
shortn.teams.update(team["slug"], description="Paid social campaigns", workspace=workspace_id)
shortn.teams.list(workspace_id)["teams"]
shortn.teams.delete(team["slug"], workspace=workspace_id)   # archives it
```

### Domains

Adding, verifying and deleting domains needs an account-wide key.

```python
domain = shortn.domains.create(domain="go.example.com")["domain"]
print(domain["dns"])                       # records to create at your DNS provider
check = shortn.domains.verify(domain["id"])
shortn.domains.list()["data"]
shortn.domains.delete(domain["id"])
```

### Reports and alerts

```python
rule = shortn.reports.create_rule(
    workspace_public_id=workspace_id,
    report_type="custom_builder_v1",
    schedule_type="every_x",
    interval_seconds=604800,
    report_name="Weekly traffic",
    destination_public_ids=[hook["public_id"]],
    definition_json={
        "version": "custom_builder.v1",
        "trigger": "scheduled",
        "sections": [{"id": "total_clicks", "order": 1, "settings": {"window": "7d"}}],
    },
)["data"]
shortn.reports.update_rule(rule["public_id"], enabled=False)
shortn.reports.list_rules(workspace_public_id=workspace_id, schedule_types=["every_x"])
shortn.reports.get_rule(rule["public_id"])["data"]["definition"]
shortn.reports.delete_rule(rule["public_id"])   # returns None
```

### Conversions

Send leads, sales and refunds from your backend with the click id the
[capture script](https://docs.shortn.link/docs/conversion-tracking/install-capture-script/)
stored on your site.

```python
shortn.conversions.track_lead(
    click_id="clk_...", idempotency_key="signup:8412", event_name="Sign up", lead_category="signup"
)
shortn.conversions.track_sale(
    click_id="clk_...", amount_cents=4900, currency="EUR", invoice_id="inv_123", idempotency_key="sale:inv_123"
)
shortn.conversions.track_refund(invoice_id="inv_123", refund_id="re_456", amount_cents=1900)

# The same checks without recording anything:
shortn.conversions.validate_sale(click_id="clk_...", amount="49.00", currency="EUR", invoice_id="inv_123")

summary = shortn.conversions.summary()["data"]
rows = shortn.conversions.attribution(from_="2026-11-01", to="2026-11-30", limit=20)
points = shortn.conversions.timeline(interval="week")
events = shortn.conversions.events(environment="test", event_type="sale", limit=50)
```

`from_` is sent as the API's `from` parameter (`from` is a Python keyword). Dates take an
RFC 3339 string, a `YYYY-MM-DD` string, or a `datetime.date`/`datetime.datetime`.

In request bodies (`occurred_at`, a link's `starts_at` and `expires_at`) the SDK sends a
`datetime` as an RFC 3339 UTC timestamp such as `2026-11-22T09:30:00Z`: an aware
`datetime` is converted to UTC, a naive one is taken to be UTC already, and a `date`
becomes midnight UTC. Strings are sent as you pass them and must carry an offset.
Send `test_mode=True` to record test events, and read them with `environment="test"`.
A refund names a live sale by its `invoice_id`.

### Public helpers (no API key)

```python
public = Shortn()   # no key: only client.public works

public.public.validate_url("example.com/menu")   # {"valid": True, "normalized": "https://example.com/menu"}
png = public.public.qr_code(url="https://shtnl.ink/abC12x9", size="download")   # bytes
svg = public.public.qr_code(url="https://shtnl.ink/abC12x9", format="svg", fg="1f2937")
plans = public.public.plans()["plans"]
```

QR options take snake_case or the API's camelCase names (`color_mode` or `colorMode`).
These helpers never send the API key, also on a client that has one. A client without a
key raises `ShortnConfigurationError` for every other method.

Creating a link without a key, and the public preview of an anonymous link, need a human
check in the browser, so they are not in the SDK: use `links.create` and `analytics.link`
with a key.

## Errors

Every non-2xx answer raises `ShortnAPIError`:

```python
from shortn_sdk import ShortnAPIError, ShortnNetworkError

try:
    shortn.links.create(url="https://example.com", title="Docs", custom_code="docs")
except ShortnAPIError as error:
    print(error.status)      # 409
    print(error.code)        # "custom_code_conflict"; None only for a non-API answer
    print(error.message)     # the API's "error" text
    print(error.hint, error.field, error.details, error.request_id, error.retry_after)
    print(error.body)        # the whole decoded body, e.g. "feature" and "required_plan" on plan limits
except ShortnNetworkError:
    ...                      # no response: DNS, connection, timeout
```

Every error the API sends carries a `code`; `error.code` is `None` only when the answer
didn't come from the API, such as a proxy's `502` page, so branch on `error.status` then. A
UTM template update that would cut teams off from links answers `409` with code
`lost_access_action_required`, and the affected links are in `error.body["impact"]`.

All SDK errors derive from `ShortnError`. `error.raw_body` holds the undecoded body and
`error.headers` the response headers (lower-case names).

## Retries

The client retries a request on `429` and `503` answers and on network errors, when it is
safe to send it again:

- `GET`, `PUT` and `DELETE` requests;
- `POST` requests whose body carries an `idempotency_key` (conversion writes).

`PATCH` requests and other `POST`s, such as `links.create`, are sent once. So is every
conversion sent with `test_mode=True`, even with an `idempotency_key`: the API doesn't
deduplicate test events, so a retry could record one twice.

A `Retry-After` header is honoured; otherwise the delay grows exponentially with jitter.
When `Retry-After` asks for longer than `max_retry_after` seconds, the client raises the
`ShortnAPIError` at once instead of waiting: the monthly quota
(`api_monthly_limit_exceeded`) answers with the days left until it resets. Read
`error.retry_after` to decide what to do.

Redirects are not followed: a `3xx` answer raises `ShortnAPIError`, so a request is never
replayed as a `GET` or sent with your key to another host.

```python
RetryOptions(
    max_retries=2,         # retries after the first attempt
    initial_delay=0.5,
    max_delay=8.0,
    backoff_factor=2.0,
    jitter=True,
    max_retry_after=60.0,
    enabled=True,
)
```

Pass `retry=False` to turn retries off.

## Examples

- [`examples/create_link.py`](https://github.com/jedna-software/shortn-sdk-python/blob/main/examples/create_link.py): tag, create and read a link.
- [`examples/track_conversions.py`](https://github.com/jedna-software/shortn-sdk-python/blob/main/examples/track_conversions.py): send a test lead and sale, read events.
- [`examples/public_helpers.py`](https://github.com/jedna-software/shortn-sdk-python/blob/main/examples/public_helpers.py): validation, QR code and plans without a key.

## Development

See [CONTRIBUTING.md](https://github.com/jedna-software/shortn-sdk-python/blob/main/CONTRIBUTING.md). The unit tests run offline; `tests/test_smoke.py` is
an opt-in test against a live instance.

## License

MIT
