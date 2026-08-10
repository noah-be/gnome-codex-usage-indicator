# Security policy

## Supported versions

Security fixes are applied to the latest release and the `main` branch.

## Reporting a vulnerability

Please use
[GitHub private vulnerability reporting](https://github.com/noah-be/gnome-codex-usage-indicator/security/advisories/new).
Do not open a public issue for a suspected vulnerability.

Include a concise impact description, affected version, reproduction steps,
and any suggested mitigation. Do not include live access tokens or credential
files. You should receive an acknowledgement within seven days.

## Sensitive data

This project should never require direct access to `~/.codex/auth.json` or raw
ChatGPT/OpenAI tokens. Reports and diagnostics must redact:

- Access and refresh tokens.
- ChatGPT account and organization identifiers.
- Email addresses.
- Private source paths or repository contents unrelated to the issue.
