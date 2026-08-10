# Development

## Tooling

Runtime requirements are Python 3.10+, GNOME Shell, GLib, and the Codex CLI.
Development additionally uses:

- GNU Make.
- `gnome-extensions` for packaging and installation.
- `glib-compile-schemas` for GSettings validation.
- Node.js when available for JavaScript syntax checks.

No Python virtual environment or package installation is required.

## Common targets

```console
make test       # Offline Python unit and JSONL integration tests
make validate   # Tests, metadata, schema, Python, and JavaScript checks
make pack       # Build the extension ZIP in dist/
make install    # Package and install into the current user account
make enable     # Enable the installed extension
make live-test  # Read the current authenticated account snapshot
make clean      # Remove generated packages and bytecode
```

`make validate` and `make pack` are account-independent. Only `make live-test`
starts the real Codex app-server.

## Running tests

```console
PYTHONWARNINGS=error::ResourceWarning make test
```

Add protocol fixtures to `tests/test_app_server.py`. Prefer the fake executable
in `tests/fake_codex.py` for handshake behavior so CI never needs credentials or
network access.

## Manual GNOME testing

Build and install the extension:

```console
make install
```

On Wayland, log out and back in. Then enable the extension:

```console
gnome-extensions enable codex-usage-indicator@noah-be.github.io
```

Inspect its state and errors:

```console
gnome-extensions info codex-usage-indicator@noah-be.github.io
journalctl --user -f -o cat
```

Use the indicator menu's **Refresh now** item while watching the journal.

## Packaging

`make pack` creates:

```text
dist/codex-usage-indicator@noah-be.github.io.shell-extension.zip
```

The packaging target explicitly includes the helper package and executable.
Check the archive when changing paths:

```console
unzip -l dist/codex-usage-indicator@noah-be.github.io.shell-extension.zip
```

The executable bit on `bin/codex-usage` must be preserved.

`bin/codex-usage-tray` is an AppIndicator fallback for testing in a running
Wayland session where a newly installed native extension cannot be reloaded.
It requires the Gtk 3 and AppIndicator 3 GObject-introspection bindings.

## Coding guidelines

- Keep authentication and network behavior inside the Codex CLI.
- Avoid invoking a shell; pass argument vectors to subprocess APIs.
- Keep the helper output backward-compatible and JSON-serializable.
- Treat missing or malformed protocol fields as errors.
- Add tests for every accepted app-server response shape.
- Remove GLib sources, signals, subprocesses, and cancellables during extension
  shutdown.

## Release checklist

1. Update `__version__` in `codex_usage_indicator/__init__.py`.
2. Increment the integer `version` in `metadata.json`.
3. Add the release date and changes to `CHANGELOG.md`.
4. Run `PYTHONWARNINGS=error::ResourceWarning make validate`.
5. Run `make live-test` against a ChatGPT-authenticated Codex CLI.
6. Run `make pack` and inspect the archive.
7. Commit, create an annotated `vX.Y.Z` tag, and attach the ZIP to the GitHub
   release.
