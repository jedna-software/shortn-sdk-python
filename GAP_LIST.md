# Coverage and gaps

Checked against the Shortn API's `/api/v1` routes and the public API reference on
2026-11-21, and exercised against a running Shortn instance.

## Covered: 50 methods, every public route an API key can use

| Group | Methods | Routes |
|---|---|---|
| `links` | `list`, `get`, `create`, `update`, `delete`, `enable`, `set_ab_winner` | `GET/POST /links`, `GET/PATCH/DELETE /links/{public_id}`, `POST /links/{public_id}/enable`, `POST /links/{public_id}/ab/winner` |
| `analytics` | `link` | `GET /analytics/links/{public_id}` |
| `workspaces` | `list`, `get` | `GET /workspaces`, `GET /workspaces/{public_id}` |
| `tags` | `list`, `create`, `get`, `update`, `delete` | `GET/POST /workspaces/{id}/tags`, `GET/PUT/DELETE /tags/{id}` |
| `utm_templates` | `list`, `create`, `update`, `delete` | `GET/POST /workspaces/{id}/utm-templates`, `PUT/DELETE /utm-templates/{id}` |
| `destinations` | `list`, `create`, `update`, `delete` | `GET/POST /workspaces/{id}/destinations`, `PUT/DELETE /workspaces/{id}/destinations/{id}` |
| `teams` | `list`, `create`, `get`, `update`, `delete` | `GET/POST /workspaces/{id}/teams`, `GET/PUT/DELETE /teams/{slug}` |
| `domains` | `list`, `create`, `verify`, `delete` | `GET/POST /domains`, `POST /domains/{id}/verify`, `DELETE /domains/{id}` |
| `reports` | `list_rules`, `get_rule`, `create_rule`, `update_rule`, `delete_rule` | `GET/POST /reports/rules`, `GET/PATCH/DELETE /reports/rules/{id}` |
| `conversions` | `track_lead`, `validate_lead`, `track_sale`, `validate_sale`, `track_refund`, `validate_refund`, `summary`, `attribution`, `timeline`, `events` | `POST /conversions/{leads,sales,refunds}[/validations]`, `GET /conversions/{summary,attribution,timeline,events}` |
| `public` | `validate_url`, `qr_code`, `plans` | `GET /validate`, `GET /qr`, `GET /plans` (no key) |

`Shortn.request()` reaches any other `/api/v1` endpoint with the same auth, errors and
retries.

## Left out on purpose

- Key-less `POST /links` and `GET /links/{code}/analytics`: they need a browser human
  check (`X-Turnstile-Token`), so a server can't call them. With a key, use
  `links.create` and `analytics.link`.
- Dashboard (browser-session) endpoints outside `/api/v1`.

## Behaviour to know

- Test mode and refunds (by design): a refund only finds a live sale. Refunding a
  `test_mode` sale answers `404 conversion_sale_not_found`, also with `test_mode` on the
  refund, so the test-mode flow can't cover refunds end to end; the smoke test accepts
  that answer.
- Test events are never deduplicated, even with an `idempotency_key`, so the SDK never
  retries a conversion sent with `test_mode=True`.
- The monthly API quota answers `429 api_monthly_limit_exceeded` with a `Retry-After` of
  days. The SDK raises it at once rather than waiting longer than `max_retry_after`.
- `links.delete` suspends a link; the API has no permanent delete.

## Possible follow-ups

- Async client (`asyncio`) with the same surface.
- Pagination helpers that follow `next_offset` for `links.list` and `conversions.events`.
- Dataclass response models, for users who prefer attributes to dict keys.
