# Troubleshooting

## The panel shows `Codex !`

Run the helper directly:

```console
./bin/codex-usage --format json --pretty
```

The returned `error` field normally identifies the missing binary, login
problem, timeout, or protocol mismatch.

Verify the Codex login:

```console
codex login status
```

The account rate-limit endpoint is intended for a ChatGPT-authenticated Codex
session. An API-key-only login uses API rate limits and may not provide the
ChatGPT weekly window.

## Codex is not found

Graphical sessions sometimes have a smaller `PATH` than interactive shells.
The helper checks these locations automatically:

```text
PATH
~/.local/bin/codex
/usr/local/bin/codex
/usr/bin/codex
```

For diagnosis, pass an explicit path:

```console
./bin/codex-usage --codex /path/to/codex
```

## The extension is installed but absent

Confirm that GNOME can see it:

```console
gnome-extensions info codex-usage-indicator@noah-be.github.io
```

GNOME Wayland sessions require a logout and login before newly installed or
updated extension code is loaded. Afterwards run:

```console
gnome-extensions enable codex-usage-indicator@noah-be.github.io
```

## The percentage is stale

Select **Refresh now** from the indicator menu. The preferences window allows
an automatic interval between 60 and 3600 seconds. Very frequent polling is
unnecessary because usage changes only after Codex activity.

## Inspect GNOME Shell errors

```console
journalctl --user -f -o cat
```

Reproduce the problem and look for messages mentioning
`codex-usage-indicator` or `gnome-shell`.

## Report a protocol regression

Include:

- GNOME Shell version.
- Codex CLI version.
- Python version.
- The helper's error message.
- Whether `codex login status` reports a ChatGPT login.

Do not attach `~/.codex/auth.json`, access tokens, or unredacted logs containing
credentials. Open a bug using the repository's issue template.
