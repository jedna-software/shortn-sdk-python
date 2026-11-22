# Changelog

## 0.1.0 - 2026-11-22

First release. Requires Python 3.10 or newer; no runtime dependencies.

- Covers the Shortn public API (`/api/v1`) with 50 methods in 11 groups: `links`,
  `analytics`, `workspaces`, `tags`, `utm_templates`, `destinations`, `teams`, `domains`,
  `reports`, `conversions` and the key-less `public` helpers (`validate_url`, `qr_code`,
  `plans`).
- Keyword-only parameters named like the API's JSON fields, with `TypedDict` types for
  request fields and responses (`shortn_sdk.types`, `py.typed`). Responses are the
  decoded JSON, so new API fields need no SDK update.
- Path parameters are URL-escaped; only the query parameters and body fields you set are
  sent.
- One error type, `ShortnAPIError`, with `status`, `code`, `message`, `hint`, `field`,
  `details`, `request_id`, `retry_after` and the raw body. `ShortnNetworkError` when no
  response arrives; `ShortnConfigurationError` when a keyed method runs without an API key.
- Retries on `429`, `503` and network errors for `GET`, `PUT`, `DELETE` and for `POST`s
  carrying an `idempotency_key`, honouring `Retry-After`; configurable with
  `RetryOptions`, or off with `retry=False`. A `Retry-After` longer than
  `max_retry_after` (such as the monthly quota's) raises at once instead of waiting, and
  conversions sent with `test_mode=True` are never retried, since the API doesn't
  deduplicate test events.
- Redirects are not followed: a `3xx` raises `ShortnAPIError`.
- Dates and datetimes in request bodies are sent as RFC 3339 UTC timestamps; naive
  datetimes are taken as UTC.
- `Authorization: Bearer` auth, sent only to keyed endpoints (never to the `public`
  helpers); `shortn-sdk-python/0.1.0` User-Agent; configurable base URL (validated as an
  `http`/`https` URL), timeout and transport.
- Offline unit tests for every method, and an opt-in smoke test against a live instance.
