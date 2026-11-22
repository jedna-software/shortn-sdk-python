from __future__ import annotations

import email.utils
import http.client
import json
import random
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Callable, Mapping, Optional, Tuple
from urllib import error as urlerror
from urllib import parse, request

from ._version import __version__
from .errors import ShortnAPIError, ShortnConfigurationError, ShortnError, ShortnNetworkError

DEFAULT_BASE_URL = "https://app.shortn.link"
DEFAULT_TIMEOUT = 30.0
USER_AGENT = f"shortn-sdk-python/{__version__}"

#: A transport sends one HTTP request and returns ``(status, headers, body)``.
#: It receives ``(method, url, headers, body, timeout)``; ``body`` is ``None`` when
#: the request has none. Raise ``OSError`` (or :class:`ShortnNetworkError`) when
#: no response arrives; return non-2xx responses instead of raising.
Transport = Callable[
    [str, str, Mapping[str, str], Optional[bytes], float],
    Tuple[int, Mapping[str, str], bytes],
]

_RETRY_STATUSES = frozenset({429, 503})
_SAFE_METHODS = frozenset({"GET", "HEAD", "PUT", "DELETE"})


@dataclass(frozen=True)
class RetryOptions:
    """When and how often the client retries a request.

    The client retries on ``429`` and ``503`` answers and on network errors, but only
    for ``GET``, ``PUT`` and ``DELETE`` requests and for ``POST`` requests whose body
    carries an ``idempotency_key``. A ``POST`` with ``test_mode`` set is never retried:
    the API doesn't deduplicate test events, so a retry could record one twice.

    ``Retry-After`` is honoured. When it asks for more than ``max_retry_after`` seconds
    (the monthly quota answers with days, for example), the error is raised at once
    instead of waiting.
    """

    max_retries: int = 2
    initial_delay: float = 0.5
    max_delay: float = 8.0
    backoff_factor: float = 2.0
    jitter: bool = True
    max_retry_after: float = 60.0
    enabled: bool = True


NO_RETRY = RetryOptions(enabled=False)


class Shortn:
    """Client for the Shortn API (``/api/v1``).

    Use it only in trusted server-side code: an API key must never reach a browser,
    a mobile app or any other client-controlled code.

    Args:
        api_key: A ``sk_live_...`` key. Optional only for the key-less helpers in
            :attr:`public`, which never send it.
        base_url: The app's origin, an ``http`` or ``https`` URL. The SDK appends
            ``/api/v1``.
        timeout: Seconds to wait for each HTTP attempt.
        retry: :class:`RetryOptions`, or ``False`` to turn retries off.
        user_agent: Appended to the ``shortn-sdk-python/<version>`` User-Agent.
        transport: Replaces the standard-library HTTP transport, for tests or a
            custom HTTP stack. See :data:`Transport`.

    Raises:
        ShortnConfigurationError: ``base_url`` isn't an ``http``/``https`` URL with a host.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        retry: RetryOptions | bool | None = None,
        user_agent: str | None = None,
        transport: Transport | None = None,
    ) -> None:
        from .resources import (
            AnalyticsResource,
            ConversionsResource,
            DestinationsResource,
            DomainsResource,
            LinksResource,
            PublicResource,
            ReportsResource,
            TagsResource,
            TeamsResource,
            UTMTemplatesResource,
            WorkspacesResource,
        )

        self.api_key = (api_key or "").strip()
        self.base_url = _normalize_base_url(base_url)
        self.timeout = timeout
        if retry is None or retry is True:
            self.retry = RetryOptions()
        elif retry is False:
            self.retry = NO_RETRY
        else:
            self.retry = retry
        self.user_agent = f"{USER_AGENT} {user_agent.strip()}" if user_agent and user_agent.strip() else USER_AGENT
        self.transport: Transport = transport or urllib_transport

        self.links = LinksResource(self)
        self.analytics = AnalyticsResource(self)
        self.workspaces = WorkspacesResource(self)
        self.tags = TagsResource(self)
        self.utm_templates = UTMTemplatesResource(self)
        self.destinations = DestinationsResource(self)
        self.teams = TeamsResource(self)
        self.domains = DomainsResource(self)
        self.reports = ReportsResource(self)
        self.conversions = ConversionsResource(self)
        self.public = PublicResource(self)

    def __repr__(self) -> str:
        return f"Shortn(base_url={self.base_url!r}, api_key={'set' if self.api_key else 'unset'})"

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        auth: bool = True,
        accept: str = "application/json",
        raw: bool = False,
    ) -> Any:
        """Send a request to ``/api/v1<path>`` and decode the answer.

        The resource methods use this; call it yourself for an endpoint the SDK
        doesn't cover yet. ``None`` values are left out of ``query`` and ``body``.
        The API key is sent only when ``auth`` is true. Dates and datetimes in ``body``
        are sent as RFC 3339 UTC timestamps (see :func:`_json_default`).
        Returns the decoded JSON (``None`` for an empty body), or the body bytes when
        ``raw`` is true.
        """
        method = method.upper()
        if auth and not self.api_key:
            raise ShortnConfigurationError(
                "This endpoint needs an API key: pass api_key to Shortn(...). Only client.public works without one."
            )
        url = self.base_url + "/api/v1" + path + _encode_query(query)
        payload = _encode_body(body) if body is not None else None
        headers = {"Accept": accept, "User-Agent": self.user_agent}
        if auth:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if payload is not None:
            headers["Content-Type"] = "application/json"

        retryable = _is_retryable_request(method, body)
        options = self.retry
        attempt = 0
        while True:
            try:
                status, response_headers, response_body = self.transport(method, url, headers, payload, self.timeout)
            except (OSError, http.client.HTTPException, ShortnNetworkError) as exc:
                if retryable and _can_retry(options, attempt):
                    _sleep(_backoff(options, attempt))
                    attempt += 1
                    continue
                if isinstance(exc, ShortnNetworkError):
                    raise
                raise ShortnNetworkError(f"Shortn request failed before a response arrived: {exc}") from exc

            response_headers = {str(k).lower(): str(v) for k, v in dict(response_headers).items()}
            if 200 <= status < 300:
                if raw:
                    return response_body
                return _decode_success(status, response_headers, response_body)

            error = _api_error(status, response_headers, response_body)
            if retryable and status in _RETRY_STATUSES and _can_retry(options, attempt):
                delay = _backoff(options, attempt)
                if error.retry_after is not None:
                    if error.retry_after > options.max_retry_after:
                        # Waiting that long (the monthly quota sends days) would hang the caller.
                        raise error
                    delay = error.retry_after
                _sleep(delay)
                attempt += 1
                continue
            raise error


class _NoRedirectHandler(request.HTTPRedirectHandler):
    """Leaves redirects unfollowed, so a ``3xx`` reaches the caller as an error.

    urllib would otherwise turn a redirected ``POST`` into a ``GET`` and send the
    ``Authorization`` header to the new location.
    """

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def _build_opener(*handlers: Any) -> request.OpenerDirector:
    return request.build_opener(_NoRedirectHandler, *handlers)


_OPENER = _build_opener()


def urllib_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes | None,
    timeout: float,
) -> tuple[int, Mapping[str, str], bytes]:
    """The default transport, built on :mod:`urllib.request`. It doesn't follow redirects."""
    req = request.Request(url, data=body, headers=dict(headers), method=method)
    try:
        with _OPENER.open(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers.items()), resp.read()
    except urlerror.HTTPError as exc:
        try:
            data = exc.read()
        finally:
            exc.close()
        return exc.code, dict(exc.headers.items()) if exc.headers else {}, data


def path(*segments: Any) -> str:
    """Join path segments, URL-escaping each one (``/`` included)."""
    parts = []
    for segment in segments:
        text = str(segment).strip() if segment is not None else ""
        if not text:
            raise ValueError("Path parameters must not be empty.")
        parts.append(parse.quote(text, safe=""))
    return "/" + "/".join(parts)


def _normalize_base_url(base_url: str) -> str:
    base = (base_url or DEFAULT_BASE_URL).strip().rstrip("/")
    if base.endswith("/api/v1"):
        base = base[: -len("/api/v1")]
    try:
        split = parse.urlsplit(base)
        host = split.hostname
    except ValueError:
        split, host = None, None
    if split is None or split.scheme not in ("http", "https") or not host:
        raise ShortnConfigurationError(
            f"base_url must be an http:// or https:// URL with a host, such as {DEFAULT_BASE_URL!r}; got {base_url!r}."
        )
    return base


def _query_value(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (list, tuple, set, frozenset)):
        return ",".join(_query_value(item) for item in value)
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _encode_query(query: Mapping[str, Any] | None) -> str:
    if not query:
        return ""
    items = [(key, _query_value(value)) for key, value in query.items() if value is not None]
    if not items:
        return ""
    return "?" + parse.urlencode(items, quote_via=parse.quote)


def _json_default(value: Any) -> Any:
    """Encode what :mod:`json` can't: dates as RFC 3339 UTC timestamps, sets as lists.

    The API needs RFC 3339 with an offset (``occurred_at``, ``starts_at``,
    ``expires_at``). An aware ``datetime`` is converted to UTC; a naive one is taken
    to be UTC already; a ``date`` becomes midnight UTC. All end in ``Z``.
    """
    if isinstance(value, datetime):
        if value.utcoffset() is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.replace(tzinfo=None).isoformat() + "Z"
    if isinstance(value, date):
        return value.isoformat() + "T00:00:00Z"
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _encode_body(body: Mapping[str, Any]) -> bytes:
    compact = {key: value for key, value in body.items() if value is not None}
    return json.dumps(compact, separators=(",", ":"), default=_json_default).encode("utf-8")


def _is_retryable_request(method: str, body: Mapping[str, Any] | None) -> bool:
    if method in _SAFE_METHODS:
        return True
    if method == "POST" and body is not None:
        if body.get("test_mode"):
            # The API never deduplicates test events, even with an idempotency_key.
            return False
        key = body.get("idempotency_key")
        return isinstance(key, str) and bool(key.strip())
    return False


def _can_retry(options: RetryOptions, attempt: int) -> bool:
    return options.enabled and attempt < options.max_retries


def _backoff(options: RetryOptions, attempt: int) -> float:
    delay = min(options.initial_delay * (options.backoff_factor**attempt), options.max_delay)
    if options.jitter and delay > 0:
        delay *= 0.5 + random.random() * 0.5
    return max(0.0, delay)


def _sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


def _decode_success(status: int, headers: Mapping[str, str], body: bytes) -> Any:
    if not body or not body.strip():
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ShortnError(f"Shortn answered {status} with a body that isn't JSON.") from exc


def _api_error(status: int, headers: Mapping[str, str], body: bytes) -> ShortnAPIError:
    parsed: Any = None
    if body:
        try:
            parsed = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            parsed = body.decode("utf-8", errors="replace")

    code = hint = field = request_id = None
    details: Any = None
    message = ""
    if isinstance(parsed, dict):
        message = _str_or_none(parsed.get("error")) or _str_or_none(parsed.get("message")) or ""
        code = _str_or_none(parsed.get("code"))
        hint = _str_or_none(parsed.get("hint"))
        details = parsed.get("details")
        if isinstance(details, dict):
            field = _str_or_none(details.get("field"))
        field = field or _str_or_none(parsed.get("field"))
        request_id = _str_or_none(parsed.get("request_id"))
    elif isinstance(parsed, str) and parsed.strip() and len(parsed) <= 200:
        message = parsed.strip()
    if not message:
        message = f"Shortn API request failed with status {status}"

    return ShortnAPIError(
        message,
        status=status,
        code=code,
        hint=hint,
        field=field,
        details=details,
        request_id=request_id or headers.get("shortn-request-id"),
        retry_after=_parse_retry_after(headers.get("retry-after")),
        body=parsed,
        raw_body=body or b"",
        headers=headers,
    )


def _str_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None
