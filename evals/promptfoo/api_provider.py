"""Promptfoo provider for the VendorLens FastAPI endpoints.

The provider deliberately calls the application API instead of Azure OpenAI
directly. This keeps the evaluation representative of the actual product
workflow and avoids maintaining a second copy of the production prompts.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 90
_REVIEWER_TOKENS: dict[str, str] = {}
_APPLICATION_TOKENS: dict[str, str] = {}


def _config(options: dict[str, Any]) -> dict[str, Any]:
    configured = options.get("config") or {}
    return configured if isinstance(configured, dict) else {}


def _base_url(config: dict[str, Any]) -> str:
    return str(os.getenv("PROMPTFOO_BASE_URL") or config.get("base_url") or DEFAULT_BASE_URL).rstrip("/")


def _timeout(config: dict[str, Any]) -> float:
    try:
        return float(config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS


def _request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    timeout: float,
    *,
    token: str | None = None,
    allowed_statuses: set[int] | None = None,
) -> tuple[int, dict[str, Any]]:
    body = None
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return response.status, parsed if isinstance(parsed, dict) else {"data": parsed}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")[:500]
        try:
            details = json.loads(raw)
        except json.JSONDecodeError:
            details = {"detail": raw or exc.reason}
        if allowed_statuses and exc.code in allowed_statuses:
            return (
                exc.code,
                details if isinstance(details, dict) else {"data": details},
            )
        message = details.get("message") or details.get("detail") or str(exc.reason)
        raise RuntimeError(f"VendorLens API returned HTTP {exc.code}: {message}") from exc
    except URLError as exc:
        raise RuntimeError(f"VendorLens API is unreachable at {url}: {exc.reason}") from exc


def _token_from_response(response: dict[str, Any], role: str) -> str:
    token = response.get("token")
    if not isinstance(token, str) or not token:
        raise RuntimeError(f"VendorLens did not return a {role} session token.")
    return token


def _reviewer_token(config: dict[str, Any], timeout: float) -> str:
    direct = os.getenv("PROMPTFOO_REVIEWER_TOKEN") or config.get("reviewer_token")
    if direct:
        return str(direct)

    base_url = _base_url(config)
    if base_url not in _REVIEWER_TOKENS:
        _, response = _request_json(
            "POST",
            f"{base_url}/api/portal/auth/reviewer-demo",
            None,
            timeout,
        )
        _REVIEWER_TOKENS[base_url] = _token_from_response(response, "reviewer")
    return _REVIEWER_TOKENS[base_url]


def _local_base_url(base_url: str) -> bool:
    hostname = (urlparse(base_url).hostname or "").casefold()
    return hostname in {"localhost", "127.0.0.1", "::1"}


def _application_token(config: dict[str, Any], timeout: float) -> str:
    direct = os.getenv("PROMPTFOO_SUPPLIER_TOKEN") or config.get("supplier_token")
    if direct:
        return str(direct)

    base_url = _base_url(config)
    if base_url in _APPLICATION_TOKENS:
        return _APPLICATION_TOKENS[base_url]

    seed_enabled = str(config.get("seed_test_application", "false")).casefold() in {
        "1", "true", "yes",
    }
    email = os.getenv("PROMPTFOO_SUPPLIER_EMAIL") or config.get("supplier_email")
    password = os.getenv("PROMPTFOO_SUPPLIER_PASSWORD") or config.get("supplier_password")
    if not email or not password:
        if not seed_enabled:
            raise RuntimeError(
                "Set PROMPTFOO_SUPPLIER_TOKEN, supplier credentials, or "
                "seed_test_application=true for application-assistant tests."
            )
        if not _local_base_url(base_url):
            raise RuntimeError(
                "Automatic Promptfoo application seeding is restricted to localhost."
            )
        email = "promptfoo.cybersecurity@example.com"
        password = "VendorLensPromptfoo!2026"

    status, response = _request_json(
        "POST",
        f"{base_url}/api/portal/auth/register",
        {"email": str(email), "password": str(password)},
        timeout,
        allowed_statuses={409},
    )
    if status == 409:
        _, response = _request_json(
            "POST",
            f"{base_url}/api/portal/auth/login",
            {"email": str(email), "password": str(password)},
            timeout,
        )
    token = _token_from_response(response, "supplier")
    _APPLICATION_TOKENS[base_url] = token

    _request_json(
        "PATCH",
        f"{base_url}/api/portal/application",
        {
            "category": str(config.get("category", "TECH")),
            "subcategory": str(config.get("subcategory", "TECH-CYB")),
            "name": "Promptfoo Cybersecurity Evaluation Supplier Private Limited",
            "country": "India",
            "contact_email": str(email),
            "tax_reference": "29ABCDE1234F1Z5",
            "bank_account_number": "1234567890123456",
            "bank_ifsc": "HDFC0001234",
        },
        timeout,
        token=token,
        allowed_statuses={409},
    )
    return token


def _supplier_id(
    vars: dict[str, Any],
    config: dict[str, Any],
    timeout: float,
    reviewer_token: str,
) -> str:
    direct_id = vars.get("supplier_id") or config.get("supplier_id") or os.getenv("PROMPTFOO_SUPPLIER_ID")
    if direct_id:
        return str(direct_id)

    supplier_name = (
        vars.get("supplier_name")
        or config.get("supplier_name")
        or os.getenv("PROMPTFOO_SUPPLIER_NAME")
    )
    if not supplier_name:
        raise RuntimeError(
            "Set PROMPTFOO_SUPPLIER_ID or PROMPTFOO_SUPPLIER_NAME to a processed supplier."
        )

    _, suppliers = _request_json(
        "GET",
        f"{_base_url(config)}/api/suppliers",
        None,
        timeout,
        token=reviewer_token,
    )
    candidates = suppliers.get("suppliers", suppliers.get("items", suppliers.get("data", suppliers)))
    if not isinstance(candidates, list):
        raise RuntimeError("VendorLens supplier list response was not a list.")

    wanted = str(supplier_name).casefold().strip()
    for supplier in candidates:
        if isinstance(supplier, dict) and str(supplier.get("name", "")).casefold().strip() == wanted:
            return str(supplier["id"])
    raise RuntimeError(f"Processed supplier was not found: {supplier_name}")


def _provider_result(
    response: dict[str, Any],
    endpoint: str,
    started: float,
) -> dict[str, Any]:
    run = response.get("run") if isinstance(response.get("run"), dict) else {}
    latency_ms = run.get("latency_ms")
    if not isinstance(latency_ms, int):
        latency_ms = int((time.perf_counter() - started) * 1000)

    input_tokens = run.get("input_tokens") if isinstance(run.get("input_tokens"), int) else 0
    output_tokens = run.get("output_tokens") if isinstance(run.get("output_tokens"), int) else 0
    return {
        "output": json.dumps(response, ensure_ascii=False),
        "tokenUsage": {
            "total": input_tokens + output_tokens,
            "prompt": input_tokens,
            "completion": output_tokens,
            "numRequests": 1,
        },
        "latencyMs": latency_ms,
        "metadata": {
            "endpoint": endpoint,
            "model": run.get("model"),
            "prompt_version": run.get("prompt_version"),
            "retrieval_count": run.get("retrieval_count"),
            "information_found": response.get("information_found"),
        },
        "cached": False,
    }


def call_api(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Call the endpoint selected by the provider wrapper."""

    config = _config(options)
    vars = context.get("vars") if isinstance(context.get("vars"), dict) else {}
    mode = str(config.get("mode", "rag"))
    timeout = _timeout(config)
    started = time.perf_counter()

    try:
        if mode == "rag":
            reviewer_token = _reviewer_token(config, timeout)
            supplier_id = _supplier_id(vars, config, timeout, reviewer_token)
            endpoint = f"/api/suppliers/{quote(supplier_id, safe='')}/questions"
            url = f"{_base_url(config)}{endpoint}"
            _, response = _request_json(
                "POST",
                url,
                {"question": prompt.strip()},
                timeout,
                token=reviewer_token,
            )
        elif mode == "assistant":
            endpoint = "/api/assistant/chat"
            url = f"{_base_url(config)}{endpoint}"
            _, response = _request_json(
                "POST",
                url,
                {"messages": [{"role": "user", "content": prompt.strip()}]},
                timeout,
            )
        elif mode == "application_assistant":
            supplier_token = _application_token(config, timeout)
            endpoint = "/api/portal/application/assistant"
            url = f"{_base_url(config)}{endpoint}"
            _, response = _request_json(
                "POST",
                url,
                {"messages": [{"role": "user", "content": prompt.strip()}]},
                timeout,
                token=supplier_token,
            )
        else:
            raise RuntimeError(f"Unsupported VendorLens Promptfoo mode: {mode}")
        return _provider_result(response, endpoint, started)
    except Exception as exc:  # Promptfoo displays provider errors per test case.
        return {
            "output": "",
            "error": str(exc),
            "latencyMs": int((time.perf_counter() - started) * 1000),
            "metadata": {"mode": mode},
        }
