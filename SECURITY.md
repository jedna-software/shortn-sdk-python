# Security

## Reporting a Vulnerability

Email security reports to support@shortn.link with "Security" in the subject. Do not open a public issue with exploit details, API keys, tokens, customer data, or logs containing secrets.

Include:

- A clear description of the issue.
- A minimal reproduction, if safe to share.
- The SDK version and Python version.
- Whether any credentials or customer data may have been exposed.

## API Key Safety

This package is a server-side SDK. Do not expose a Shortn API key in browser code, mobile apps, public static sites, or any client-controlled runtime. The client never includes the key in `repr()` or error messages; don't log request headers.

For browser click capture, use the Shortn capture script and forward its events to your backend, which calls the conversions API with this SDK.
