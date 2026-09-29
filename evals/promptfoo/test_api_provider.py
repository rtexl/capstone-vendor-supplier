"""Offline contracts for the Promptfoo HTTP provider."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_provider as provider  # noqa: E402


class PromptfooProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        provider._REVIEWER_TOKENS.clear()
        provider._APPLICATION_TOKENS.clear()

    def test_reviewer_demo_token_is_cached(self) -> None:
        calls = []

        def request(method, url, payload, timeout, **kwargs):
            calls.append((method, url, payload, kwargs))
            return 200, {"token": "reviewer-session"}

        config = {"base_url": "http://localhost:8000"}
        with patch.object(provider, "_request_json", side_effect=request):
            self.assertEqual(provider._reviewer_token(config, 2), "reviewer-session")
            self.assertEqual(provider._reviewer_token(config, 2), "reviewer-session")

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "POST")
        self.assertTrue(calls[0][1].endswith("/api/portal/auth/reviewer-demo"))

    def test_application_auto_seed_rejects_nonlocal_base_url(self) -> None:
        config = {"base_url": "https://staging.example.test", "seed_test_application": True}
        with self.assertRaisesRegex(RuntimeError, "restricted to localhost"):
            provider._application_token(config, 2)

    def test_rag_call_uses_reviewer_token_for_protected_requests(self) -> None:
        requests = []

        def request(method, url, payload, timeout, **kwargs):
            requests.append((method, url, payload, kwargs))
            return 200, {
                "answer": "Grounded answer",
                "information_found": True,
                "citations": [],
                "run": {"latency_ms": 3, "input_tokens": 2, "output_tokens": 1},
            }

        config = {"base_url": "http://localhost:8000", "mode": "rag"}
        context = {"vars": {"supplier_id": "supplier-123"}}
        with (
            patch.object(provider, "_reviewer_token", return_value="reviewer-session"),
            patch.object(provider, "_supplier_id", return_value="supplier-123"),
            patch.object(provider, "_request_json", side_effect=request),
        ):
            result = provider.call_api("What is the legal name?", {"config": config}, context)

        self.assertNotIn("error", result)
        self.assertEqual(requests[0][0], "POST")
        self.assertEqual(requests[0][3]["token"], "reviewer-session")
        self.assertTrue(requests[0][1].endswith("/api/suppliers/supplier-123/questions"))

    def test_application_assistant_uses_supplier_token(self) -> None:
        requests = []

        def request(method, url, payload, timeout, **kwargs):
            requests.append((method, url, payload, kwargs))
            return 200, {"answer": "Draft state", "run": {"latency_ms": 2}}

        config = {"base_url": "http://localhost:8000", "mode": "application_assistant"}
        with (
            patch.object(provider, "_application_token", return_value="supplier-session"),
            patch.object(provider, "_request_json", side_effect=request),
        ):
            result = provider.call_api("Is my application complete?", {"config": config}, {"vars": {}})

        self.assertNotIn("error", result)
        self.assertEqual(requests[0][3]["token"], "supplier-session")
        self.assertTrue(requests[0][1].endswith("/api/portal/application/assistant"))


if __name__ == "__main__":
    unittest.main()
