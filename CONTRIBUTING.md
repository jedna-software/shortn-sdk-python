# Contributing

Thanks for helping improve the Shortn Python SDK.

## Development

The SDK has no runtime dependencies. The test tools live in a virtual environment in
`.venv/` (ignored by git):

```sh
python3 -m venv .venv
.venv/bin/pip install build mypy

PYTHONPATH=src python -m unittest discover -s tests -v   # offline unit tests
.venv/bin/mypy src                                        # types, checked as Python 3.10
.venv/bin/python -m build                                 # sdist and wheel in dist/
```

Code must run on Python 3.10: no `typing.Self`, `NotRequired`, `except*` or other newer
syntax at runtime. `typing_extensions` may be imported only under `TYPE_CHECKING`.

## Tests

- `tests/test_resources.py` checks every SDK method's HTTP method, path, query and body
  against a fake transport. A new method needs a row in `CASES`.
- `tests/test_client.py` covers headers, configuration, error mapping and retry rules.
- `tests/test_smoke.py` runs against a live instance and is skipped unless
  `SHORTN_API_KEY`, `SHORTN_BASE_URL` and `SHORTN_SMOKE_WORKSPACE` are set (see
  `.env.example`). Point it at a development instance, never production. It creates
  everything with a random suffix inside `SHORTN_SMOKE_WORKSPACE`, removes it again, and
  sends conversions with `test_mode`.

```sh
set -a; . ./smoke.env; set +a
PYTHONPATH=src python -m unittest tests.test_smoke -v
```

## Pull requests

- Keep changes focused.
- Update README, GAP_LIST and CHANGELOG when behaviour changes.
- Add tests for new request and response behaviour.
- Do not commit secrets, env files or real customer data.
