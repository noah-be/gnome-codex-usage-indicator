# Architecture

## Goals

The project keeps one account-level Codex rate-limit window visible without
handling credentials itself. The design favors a small permission surface,
short-lived processes, and components that can be tested without a live
account.

## Components

### GNOME Shell extension

`extension.js` owns the panel button, popup menu, refresh timer, warning state,
and error presentation. It invokes the helper with `Gio.Subprocess` and accepts
only a JSON object with `ok: true` and the normalized usage fields.

`prefs.js` exposes four GSettings values:

- `display-mode`: remaining or used percentage.
- `show-reset-time`: whether the compact panel label includes the reset time.
- `show-icon`: whether the symbolic icon is visible.
- `refresh-interval`: automatic refresh period in seconds.

### Command-line helper

`bin/codex-usage` is a thin entry point into the
`codex_usage_indicator` Python package. The package has no third-party runtime
dependencies.

`app_server.py` is responsible for:

1. Locating the Codex CLI in both terminal and graphical-session environments.
2. Starting `codex app-server --stdio`.
3. Sending `initialize` and waiting for its response.
4. Sending the `initialized` notification.
5. Requesting `account/rateLimits/read`.
6. Selecting and validating the requested limit window.
7. Terminating the short-lived app-server process.

The client uses an overall deadline rather than a timeout per read. Standard
output and standard error are consumed with a selector, preventing either pipe
from blocking the process.

### Tests

`tests/test_app_server.py` covers snapshot selection, normalization, malformed
responses, and percentage boundaries. `tests/fake_codex.py` implements enough
of the JSONL protocol to exercise the complete subprocess handshake without a
network connection or Codex account.

## Data flow

```text
GNOME panel timer or manual refresh
              |
              v
      bin/codex-usage
              |
              v
   codex app-server --stdio
              |
              v
 account/rateLimits/read response
              |
              v
 validated, normalized JSON
              |
              v
 panel label and detail menu
```

The extension does not persist snapshots. A failed refresh changes the panel
to `Codex !` and preserves no stale percentage, making unavailable data
visibly different from current data.

## Security boundaries

- Codex CLI owns authentication and networking.
- The helper does not read credential files or environment tokens.
- The GNOME process receives only normalized usage metadata.
- No shell is involved when the extension starts the helper.
- The helper validates timing and percentage fields before emitting them.
- The app-server process is terminated after every request.

## Compatibility policy

The GNOME JavaScript follows the extension module API introduced with GNOME
Shell 45. Supported Shell versions are declared in `metadata.json`.

The Codex app-server protocol is versioned with the installed CLI and may
change. Protocol-specific parsing is isolated in `app_server.py`; new response
variants should be accompanied by fixtures and tests before changing the UI.
