from __future__ import annotations

from typing import Any, Mapping


class ShortnError(Exception):
    """Base class for every error the Shortn SDK raises."""


class ShortnConfigurationError(ShortnError):
    """Raised when the client is missing configuration, such as an API key."""


class ShortnNetworkError(ShortnError):
    """Raised when a request fails before an HTTP response arrives."""


class ShortnAPIError(ShortnError):
    """Raised for a non-2xx answer from the Shortn API.

    Attributes:
        status: HTTP status code.
        code: Stable error code (``"link_not_found"``), when the API sent one.
        message: Readable message (the API's ``error`` field).
        hint: Suggested fix, when present.
        field: The request field at fault (``details.field``), when present.
        details: The ``details`` object, when present.
        request_id: ``request_id`` or the ``Shortn-Request-Id`` header, when present.
        retry_after: Seconds from the ``Retry-After`` header, when present.
        body: The decoded JSON body, or the body text when it isn't JSON.
        raw_body: The undecoded response body.
        headers: Response headers, with lower-case names.

    Fields the API adds to an error, such as ``feature`` or ``required_plan`` on a
    ``plan_limit_exceeded`` answer, stay reachable through :attr:`body`.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: str | None = None,
        hint: str | None = None,
        field: str | None = None,
        details: Any = None,
        request_id: str | None = None,
        retry_after: float | None = None,
        body: Any = None,
        raw_body: bytes = b"",
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.hint = hint
        self.field = field
        self.details = details
        self.request_id = request_id
        self.retry_after = retry_after
        self.body = body
        self.raw_body = raw_body
        self.headers = dict(headers or {})

    @property
    def status_code(self) -> int:
        """Alias of :attr:`status`."""
        return self.status

    def __str__(self) -> str:
        if self.code:
            return f"{self.status} {self.code}: {self.message}"
        return f"{self.status}: {self.message}"

    def __repr__(self) -> str:
        return f"ShortnAPIError(status={self.status!r}, code={self.code!r}, message={self.message!r})"
