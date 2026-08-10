"""Minimal client for the Codex app-server account rate-limit endpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import time
from typing import Any, Mapping


DEFAULT_LIMIT_ID = "codex"
DEFAULT_TIMEOUT_SECONDS = 15.0
CLIENT_INFO = {
    "name": "gnome_codex_usage_indicator",
    "title": "GNOME Codex Usage Indicator",
    "version": "0.1.0",
}


class CodexUsageError(RuntimeError):
    """Raised when Codex usage information cannot be retrieved or parsed."""


@dataclass(frozen=True, slots=True)
class UsageSnapshot:
    """Normalized usage information consumed by the GNOME extension."""

    limit_id: str
    limit_name: str | None
    plan_type: str | None
    used_percent: float
    remaining_percent: float
    window_minutes: int
    resets_at: int
    retrieved_at: int
    available_reset_credits: int

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-serializable representation."""

        return {"ok": True, **asdict(self)}


def resolve_codex_binary(explicit_path: str | None = None) -> str:
    """Locate Codex in a terminal or a typical graphical-session environment."""

    candidates: list[str | None] = [
        explicit_path,
        shutil.which("codex"),
        str(Path.home() / ".local" / "bin" / "codex"),
        "/usr/local/bin/codex",
        "/usr/bin/codex",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    raise CodexUsageError(
        "Codex CLI was not found. Install it or pass its path with --codex.")


def select_rate_limit(
    result: Mapping[str, Any],
    limit_id: str = DEFAULT_LIMIT_ID,
) -> Mapping[str, Any]:
    """Select one rate-limit snapshot from an app-server response."""

    by_id = result.get("rateLimitsByLimitId")
    if isinstance(by_id, Mapping):
        selected = by_id.get(limit_id)
        if isinstance(selected, Mapping):
            return selected

    primary = result.get("rateLimits")
    if isinstance(primary, Mapping):
        actual_id = primary.get("limitId")
        if actual_id == limit_id or (limit_id == DEFAULT_LIMIT_ID and actual_id is None):
            return primary
        if limit_id == DEFAULT_LIMIT_ID:
            # Older protocol versions expose only the main snapshot here.
            return primary

    raise CodexUsageError(f"Rate limit {limit_id!r} was not returned by Codex.")


def normalize_usage(
    result: Mapping[str, Any],
    limit_id: str = DEFAULT_LIMIT_ID,
    *,
    retrieved_at: int | None = None,
) -> UsageSnapshot:
    """Validate and normalize an account/rateLimits/read result."""

    snapshot = select_rate_limit(result, limit_id)
    window = snapshot.get("primary")
    if not isinstance(window, Mapping):
        raise CodexUsageError("Codex returned no primary rate-limit window.")

    try:
        used_percent = float(window["usedPercent"])
        window_minutes = int(window["windowDurationMins"])
        resets_at = int(window["resetsAt"])
    except (KeyError, TypeError, ValueError) as error:
        raise CodexUsageError("Codex returned an incomplete rate-limit window.") from error

    if window_minutes <= 0 or resets_at <= 0:
        raise CodexUsageError("Codex returned invalid rate-limit timing data.")

    reset_credits = result.get("rateLimitResetCredits")
    available_reset_credits = 0
    if isinstance(reset_credits, Mapping):
        try:
            available_reset_credits = max(0, int(reset_credits.get("availableCount", 0)))
        except (TypeError, ValueError):
            available_reset_credits = 0

    return UsageSnapshot(
        limit_id=str(snapshot.get("limitId") or limit_id),
        limit_name=_optional_string(snapshot.get("limitName")),
        plan_type=_optional_string(snapshot.get("planType")),
        used_percent=max(0.0, used_percent),
        remaining_percent=max(0.0, min(100.0, 100.0 - used_percent)),
        window_minutes=window_minutes,
        resets_at=resets_at,
        retrieved_at=int(time.time()) if retrieved_at is None else retrieved_at,
        available_reset_credits=available_reset_credits,
    )


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _encode_message(message: Mapping[str, Any]) -> bytes:
    return (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")


class _AppServerProcess:
    """Own one short-lived stdio app-server session."""

    def __init__(self, codex_binary: str, timeout: float) -> None:
        self._deadline = time.monotonic() + timeout
        try:
            self._process = subprocess.Popen(
                [codex_binary, "app-server", "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as error:
            raise CodexUsageError(f"Could not start Codex CLI: {error}") from error

        if self._process.stdin is None or self._process.stdout is None or \
                self._process.stderr is None:
            self.close()
            raise CodexUsageError("Could not open Codex app-server pipes.")

        self._selector = selectors.DefaultSelector()
        self._selector.register(self._process.stdout, selectors.EVENT_READ, "stdout")
        self._selector.register(self._process.stderr, selectors.EVENT_READ, "stderr")
        self._stdout_buffer = bytearray()
        self._stderr_tail = bytearray()

    def send(self, message: Mapping[str, Any]) -> None:
        if self._process.stdin is None:
            raise CodexUsageError("Codex app-server input is unavailable.")
        try:
            self._process.stdin.write(_encode_message(message))
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            raise CodexUsageError("Codex app-server closed its input unexpectedly.") from error

    def wait_for_response(self, request_id: int) -> Mapping[str, Any]:
        while True:
            response = self._take_response(request_id)
            if response is not None:
                if "error" in response:
                    error = response.get("error")
                    message = error.get("message") if isinstance(error, Mapping) else error
                    raise CodexUsageError(f"Codex app-server error: {message}")
                result = response.get("result")
                if not isinstance(result, Mapping):
                    raise CodexUsageError("Codex returned a malformed app-server response.")
                return result

            remaining = self._deadline - time.monotonic()
            if remaining <= 0:
                raise CodexUsageError("Timed out while waiting for Codex usage data.")

            events = self._selector.select(remaining)
            if not events:
                continue

            for key, _mask in events:
                try:
                    chunk = os.read(key.fileobj.fileno(), 65536)
                except OSError as error:
                    raise CodexUsageError(f"Could not read from Codex: {error}") from error

                if key.data == "stderr":
                    self._stderr_tail.extend(chunk)
                    del self._stderr_tail[:-8192]
                elif chunk:
                    self._stdout_buffer.extend(chunk)
                elif self._process.poll() is not None:
                    detail = self.stderr_text
                    suffix = f": {detail}" if detail else ""
                    raise CodexUsageError(f"Codex app-server exited unexpectedly{suffix}")

    def _take_response(self, request_id: int) -> Mapping[str, Any] | None:
        while True:
            newline = self._stdout_buffer.find(b"\n")
            if newline < 0:
                return None

            raw_line = bytes(self._stdout_buffer[:newline])
            del self._stdout_buffer[:newline + 1]
            if not raw_line.strip():
                continue

            try:
                message = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(message, Mapping) and message.get("id") == request_id:
                return message

    @property
    def stderr_text(self) -> str:
        return self._stderr_tail.decode("utf-8", errors="replace").strip()

    def close(self) -> None:
        selector = getattr(self, "_selector", None)
        if selector is not None:
            selector.close()

        process = getattr(self, "_process", None)
        if process is None:
            return

        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError:
                pass

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1.0)

        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()

    def __enter__(self) -> _AppServerProcess:
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()


def fetch_usage(
    *,
    codex_binary: str | None = None,
    limit_id: str = DEFAULT_LIMIT_ID,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> UsageSnapshot:
    """Fetch the selected ChatGPT rate-limit window through Codex app-server."""

    if timeout <= 0:
        raise CodexUsageError("Timeout must be greater than zero.")

    executable = resolve_codex_binary(codex_binary)
    with _AppServerProcess(executable, timeout) as server:
        server.send({
            "method": "initialize",
            "id": 0,
            "params": {"clientInfo": CLIENT_INFO},
        })
        server.wait_for_response(0)
        server.send({"method": "initialized", "params": {}})
        server.send({
            "method": "account/rateLimits/read",
            "id": 1,
            "params": {},
        })
        result = server.wait_for_response(1)

    return normalize_usage(result, limit_id)
