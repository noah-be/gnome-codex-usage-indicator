#!/usr/bin/env python3
"""Small app-server double used by the integration test."""

from __future__ import annotations

import json
import sys


RATE_LIMIT_RESULT = {
    "rateLimits": {
        "limitId": "codex",
        "limitName": None,
        "primary": {
            "usedPercent": 25,
            "windowDurationMins": 10080,
            "resetsAt": 1786825903,
        },
        "planType": "plus",
    },
    "rateLimitsByLimitId": {},
    "rateLimitResetCredits": {"availableCount": 0},
}


def respond(message: dict[str, object]) -> None:
    method = message.get("method")
    if method == "initialize":
        response = {"id": message["id"], "result": {"userAgent": "fake-codex"}}
    elif method == "account/rateLimits/read":
        response = {"id": message["id"], "result": RATE_LIMIT_RESULT}
    else:
        return

    print(json.dumps(response), flush=True)


def main() -> int:
    if sys.argv[1:] != ["app-server", "--stdio"]:
        return 2

    for line in sys.stdin:
        message = json.loads(line)
        if isinstance(message, dict):
            respond(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
