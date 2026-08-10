# GNOME Codex Usage Indicator

[![CI](https://github.com/noah-be/gnome-codex-usage-indicator/actions/workflows/ci.yml/badge.svg)](https://github.com/noah-be/gnome-codex-usage-indicator/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A small GNOME Shell extension that keeps the remaining Codex usage window in
the top panel.

The indicator reads the authenticated account's rate-limit snapshot through
the local Codex CLI. It does not scrape a website, inspect browser storage, or
read authentication tokens directly.

## Features

- Shows the remaining or used percentage in the GNOME top panel.
- Optionally appends the reset day and local time.
- Refreshes automatically, with a configurable interval from 1 to 60 minutes.
- Shows the full reset time, window duration, plan type, and last update in its
  menu.
- Uses warning colors at 25% and 10% remaining.
- Provides a standalone `codex-usage` command for diagnostics and scripts.
- Uses only the Python standard library at runtime.

## Requirements

- GNOME Shell 45 through 50.
- Python 3.10 or newer.
- A recent `codex` CLI available in `PATH`, `~/.local/bin`, `/usr/local/bin`, or
  `/usr/bin`.
- Codex logged in with the ChatGPT account whose usage should be displayed.

Check the login before installing:

```console
codex login status
```

## Install from source

```console
git clone https://github.com/noah-be/gnome-codex-usage-indicator.git
cd gnome-codex-usage-indicator
make install
```

GNOME on Wayland does not support reloading Shell in place. Log out and back in
after the first installation, then enable the extension:

```console
make enable
```

Open its settings through the Extensions application or from a terminal:

```console
gnome-extensions prefs codex-usage-indicator@noah-be.github.io
```

### Start immediately without logging out

GNOME Wayland cannot reload a newly installed native Shell extension in place.
If AppIndicator support is already active, start the included temporary tray
process instead:

```console
./bin/codex-usage-tray
```

It shows the same remaining percentage immediately and exits automatically
when the desktop session ends. Select **Quit temporary indicator** from its
menu once the native extension is available after a later login. Its
**Refresh interval** submenu offers 1, 2, 5, 10, 15, 30, or 60 minutes and
stores the selection for the native extension as well.

To update an existing checkout:

```console
git pull --ff-only
make install
```

Log out and back in if GNOME continues to use the previous version.

## Test the account connection

The bundled helper can be run without installing the Shell extension:

```console
./bin/codex-usage
./bin/codex-usage --format json --pretty
```

Example text output:

```text
Codex 64% remaining · resets Fri 2026-08-14 09:30 CEST
```

The helper also accepts `--codex PATH`, `--limit-id ID`, and `--timeout
SECONDS`. Run `./bin/codex-usage --help` for the complete interface.

## How it works

The extension starts a short-lived helper process on each refresh. The helper
starts `codex app-server --stdio`, completes the required JSONL initialization
handshake, requests `account/rateLimits/read`, normalizes the primary `codex`
window, and exits.

OpenAI documents both the app-server JSONL protocol and the
`account/rateLimits/read` method in the
[Codex App Server documentation](https://learn.chatgpt.com/docs/app-server).
The interface can evolve with Codex releases, so this project validates the
response and fails closed when required fields are missing.

See [Architecture](docs/ARCHITECTURE.md) for the component boundaries and data
flow.

## Privacy and security

- The extension never opens or parses `~/.codex/auth.json`.
- Authentication and token refresh remain owned by the Codex CLI.
- Only the normalized limit identifier, percentages, window duration, reset
  time, plan type, and reset-credit count are emitted by the helper.
- The extension has no telemetry and makes no independent network requests.

The Codex app-server still uses the existing Codex login and contacts OpenAI in
the same way as other Codex clients. See [Security](SECURITY.md) for reporting
security problems.

## Development

```console
make validate
make pack
make live-test
```

The test suite includes response-normalization tests and a JSONL integration
test using a local fake app-server. `make live-test` is the only target that
contacts the authenticated Codex service.

See [Development](docs/DEVELOPMENT.md),
[Troubleshooting](docs/TROUBLESHOOTING.md), and
[Contributing](CONTRIBUTING.md) for more detail.

## Project status

This is an independent community project and is not affiliated with or
endorsed by OpenAI. “OpenAI”, “ChatGPT”, and “Codex” are trademarks of their
respective owner.

## License

[MIT](LICENSE)
