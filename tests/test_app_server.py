"""Unit tests for app-server response normalization."""

from __future__ import annotations

import unittest
from pathlib import Path

from codex_usage_indicator.app_server import (
    CodexUsageError,
    fetch_usage,
    normalize_usage,
    select_rate_limit,
)


RESPONSE = {
    "rateLimits": {
        "limitId": "codex",
        "limitName": None,
        "primary": {
            "usedPercent": 42,
            "windowDurationMins": 10080,
            "resetsAt": 1786825903,
        },
        "planType": "pro",
    },
    "rateLimitsByLimitId": {
        "codex_spark": {
            "limitId": "codex_spark",
            "limitName": "Codex Spark",
            "primary": {
                "usedPercent": 5.5,
                "windowDurationMins": 10080,
                "resetsAt": 1786947268,
            },
            "planType": "pro",
        },
        "codex": {
            "limitId": "codex",
            "limitName": None,
            "primary": {
                "usedPercent": 42,
                "windowDurationMins": 10080,
                "resetsAt": 1786825903,
            },
            "planType": "pro",
        },
    },
    "rateLimitResetCredits": {"availableCount": 1},
}


class SelectRateLimitTests(unittest.TestCase):
    def test_selects_main_codex_limit(self) -> None:
        selected = select_rate_limit(RESPONSE, "codex")
        self.assertEqual(selected["limitId"], "codex")

    def test_selects_named_secondary_limit(self) -> None:
        selected = select_rate_limit(RESPONSE, "codex_spark")
        self.assertEqual(selected["limitName"], "Codex Spark")

    def test_rejects_unknown_limit(self) -> None:
        with self.assertRaisesRegex(CodexUsageError, "not returned"):
            select_rate_limit(RESPONSE, "missing")


class NormalizeUsageTests(unittest.TestCase):
    def test_normalizes_main_window(self) -> None:
        snapshot = normalize_usage(RESPONSE, retrieved_at=1234)

        self.assertEqual(snapshot.used_percent, 42)
        self.assertEqual(snapshot.remaining_percent, 58)
        self.assertEqual(snapshot.window_minutes, 10080)
        self.assertEqual(snapshot.resets_at, 1786825903)
        self.assertEqual(snapshot.retrieved_at, 1234)
        self.assertEqual(snapshot.available_reset_credits, 1)
        self.assertEqual(snapshot.plan_type, "pro")

    def test_clamps_remaining_percentage(self) -> None:
        response = {
            "rateLimits": {
                "limitId": "codex",
                "primary": {
                    "usedPercent": 110,
                    "windowDurationMins": 10080,
                    "resetsAt": 1786825903,
                },
            },
        }
        snapshot = normalize_usage(response, retrieved_at=1234)
        self.assertEqual(snapshot.remaining_percent, 0)

    def test_rejects_incomplete_window(self) -> None:
        response = {
            "rateLimits": {
                "limitId": "codex",
                "primary": {"usedPercent": 10},
            },
        }
        with self.assertRaisesRegex(CodexUsageError, "incomplete"):
            normalize_usage(response)


class AppServerIntegrationTests(unittest.TestCase):
    def test_fetches_usage_over_jsonl_stdio(self) -> None:
        fake_codex = Path(__file__).with_name("fake_codex.py")
        snapshot = fetch_usage(codex_binary=str(fake_codex), timeout=2)

        self.assertEqual(snapshot.used_percent, 25)
        self.assertEqual(snapshot.remaining_percent, 75)
        self.assertEqual(snapshot.window_minutes, 10080)
        self.assertEqual(snapshot.plan_type, "plus")


if __name__ == "__main__":
    unittest.main()
