"""
Tests for per-API-key rate limiting bucket logic.

These tests exercise _get_tenant_identifier directly so they are fast and
require no HTTP stack, while a small integration test confirms the key
appears in the bucket string returned by the limiter's key_func.
"""

import pytest
from starlette.datastructures import Headers
from starlette.requests import Request

from app.utils.rate_limit import _get_tenant_identifier, limiter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(headers: dict) -> Request:
    """Build a minimal Starlette Request with the supplied headers."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": Headers(headers=headers).raw,
        # Provide a minimal client address so get_remote_address has something
        # to fall back on.
        "client": ("127.0.0.1", 9999),
    }
    return Request(scope)


# ---------------------------------------------------------------------------
# Unit tests for _get_tenant_identifier
# ---------------------------------------------------------------------------

class TestApiKeyBucket:
    def test_api_key_uses_key_prefix(self):
        """X-API-Key header → bucket is 'apikey:<first-12-chars>'."""
        key = "abcdefghijklmnopqrstuvwxyz"
        req = _make_request({"X-API-Key": key})
        bucket = _get_tenant_identifier(req)
        assert bucket == f"apikey:{key[:12]}"

    def test_api_key_prefix_exactly_12_chars(self):
        """A key exactly 12 characters long is accepted."""
        key = "123456789012"
        req = _make_request({"X-API-Key": key})
        bucket = _get_tenant_identifier(req)
        assert bucket == f"apikey:{key}"

    def test_api_key_shorter_than_12_falls_back_to_ip(self):
        """A key shorter than 12 characters is ignored; falls back to IP."""
        req = _make_request({"X-API-Key": "short"})
        bucket = _get_tenant_identifier(req)
        assert bucket == "127.0.0.1"

    def test_two_different_keys_produce_different_buckets(self):
        """Different API keys must map to different rate-limit buckets."""
        key_a = "AAAAAAAAAAAABBBBBBBB"
        key_b = "CCCCCCCCCCCCDDDDDDDD"
        req_a = _make_request({"X-API-Key": key_a})
        req_b = _make_request({"X-API-Key": key_b})
        assert _get_tenant_identifier(req_a) != _get_tenant_identifier(req_b)

    def test_two_keys_with_same_prefix_share_bucket(self):
        """
        Keys sharing the same first 12 chars share a bucket (by design — the
        prefix is the discriminator).
        """
        key_a = "AAAAAAAAAAAA_suffix1"
        key_b = "AAAAAAAAAAAA_suffix2"
        req_a = _make_request({"X-API-Key": key_a})
        req_b = _make_request({"X-API-Key": key_b})
        assert _get_tenant_identifier(req_a) == _get_tenant_identifier(req_b)

    def test_api_key_takes_priority_over_jwt(self):
        """
        When both X-API-Key and Authorization headers are present the API key
        bucket is used, not the tenant bucket.
        """
        import base64
        import json

        # Build a trivially-decodable JWT payload with a tenant_id
        payload_bytes = json.dumps({"tenant_id": "tenant-abc", "sub": "user-1"}).encode()
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode()
        fake_jwt = f"header.{payload_b64}.signature"

        key = "XXXXXXXXXXXX_extra"
        req = _make_request({
            "X-API-Key": key,
            "Authorization": f"Bearer {fake_jwt}",
        })
        bucket = _get_tenant_identifier(req)
        assert bucket.startswith("apikey:")
        assert "tenant" not in bucket

    def test_api_key_rate_limiting_independent_from_jwt(self):
        """
        An API key request and a JWT request for the same tenant use
        independent buckets.
        """
        import base64
        import json

        tenant_id = "tenant-xyz"
        payload_bytes = json.dumps({"tenant_id": tenant_id, "sub": "user-1"}).encode()
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode()
        fake_jwt = f"header.{payload_b64}.signature"

        api_key = "YYYYYYYYYYYY_extra"
        req_jwt = _make_request({"Authorization": f"Bearer {fake_jwt}"})
        req_key = _make_request({"X-API-Key": api_key})

        bucket_jwt = _get_tenant_identifier(req_jwt)
        bucket_key = _get_tenant_identifier(req_key)

        assert bucket_jwt == f"tenant:{tenant_id}"
        assert bucket_key == f"apikey:{api_key[:12]}"
        assert bucket_jwt != bucket_key

    def test_no_auth_falls_back_to_ip(self):
        """Requests with no auth header fall back to IP-based limiting."""
        req = _make_request({})
        bucket = _get_tenant_identifier(req)
        assert bucket == "127.0.0.1"


# ---------------------------------------------------------------------------
# Smoke test: limiter.key_func is wired to our function
# ---------------------------------------------------------------------------

class TestLimiterKeyFuncWiring:
    def test_limiter_uses_api_key_bucket(self):
        """The global limiter's key_func must honour X-API-Key."""
        key = "ZZZZZZZZZZZZ_extra"
        req = _make_request({"X-API-Key": key})
        bucket = limiter._key_func(req)
        assert bucket == f"apikey:{key[:12]}"
