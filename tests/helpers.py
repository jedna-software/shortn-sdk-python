from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib import parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shortn_sdk import RetryOptions, Shortn  # noqa: E402

BASE = "https://api.example.test"


class FakeTransport:
    """Records requests and answers them from a queue of responses.

    A response is ``(status, body)`` or ``(status, body, headers)``; ``body`` is
    JSON-encoded unless it's ``bytes``. An ``Exception`` instance is raised instead.
    """

    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses) or [(200, {})]
        self.requests: list[dict[str, Any]] = []

    def __call__(self, method, url, headers, body, timeout):
        split = parse.urlsplit(url)
        self.requests.append(
            {
                "method": method,
                "url": url,
                "path": split.path,
                "raw_query": split.query,
                "query": dict(parse.parse_qsl(split.query, keep_blank_values=True)),
                "headers": dict(headers),
                "raw_body": body,
                "body": json.loads(body.decode("utf-8")) if body else None,
                "timeout": timeout,
            }
        )
        response = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(response, BaseException):
            raise response
        status, payload = response[0], response[1]
        response_headers = response[2] if len(response) > 2 else {"Content-Type": "application/json"}
        if isinstance(payload, bytes):
            return status, response_headers, payload
        return status, response_headers, json.dumps(payload).encode("utf-8")

    @property
    def last(self) -> dict[str, Any]:
        return self.requests[-1]


def make_client(*responses: Any, api_key: str | None = "sk_live_test", **kwargs: Any) -> tuple[Shortn, FakeTransport]:
    transport = FakeTransport(*responses)
    kwargs.setdefault("retry", RetryOptions(initial_delay=0, max_delay=0, jitter=False))
    client = Shortn(api_key, base_url=BASE, transport=transport, **kwargs)
    return client, transport
