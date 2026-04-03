"""
Tests for the Redis CacheService.

Redis is NOT available in the test environment, so every test verifies
graceful degradation (no errors, sensible defaults) as well as correct
behaviour of helper logic (key formatting, factory invocation, etc.).
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.cache_service import CacheService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def cache_no_redis():
    """CacheService instance with Redis explicitly unavailable."""
    svc = CacheService.__new__(CacheService)
    svc.redis = None
    return svc


@pytest.fixture()
def mock_redis():
    """A MagicMock that stands in for a live Redis client."""
    return MagicMock()


@pytest.fixture()
def cache_with_redis(mock_redis):
    """CacheService instance backed by a MagicMock Redis client."""
    svc = CacheService.__new__(CacheService)
    svc.redis = mock_redis
    return svc


# ── Graceful-degradation tests (no Redis) ────────────────────────────────────

class TestGracefulDegradation:
    def test_available_false_when_no_redis(self, cache_no_redis):
        assert cache_no_redis.available is False

    def test_get_returns_none(self, cache_no_redis):
        result = cache_no_redis.get("ns", "tenant-1", "key")
        assert result is None

    def test_set_does_not_raise(self, cache_no_redis):
        cache_no_redis.set("ns", "tenant-1", "key", {"data": 1})  # must not raise

    def test_get_or_set_calls_factory_and_returns_value(self, cache_no_redis):
        factory = MagicMock(return_value={"answer": 42})
        result = cache_no_redis.get_or_set("ns", "tenant-1", "key", factory)
        factory.assert_called_once()
        assert result == {"answer": 42}

    def test_invalidate_returns_zero(self, cache_no_redis):
        assert cache_no_redis.invalidate("ns", "tenant-1") == 0
        assert cache_no_redis.invalidate("ns", "tenant-1", key="specific") == 0

    def test_invalidate_tenant_returns_zero(self, cache_no_redis):
        assert cache_no_redis.invalidate_tenant("tenant-1") == 0


# ── Key-generation tests ──────────────────────────────────────────────────────

class TestKeyGeneration:
    def test_key_format(self, cache_no_redis):
        key = cache_no_redis._key("settings", "tenant-abc", "config")
        assert key == "cache:settings:tenant-abc:config"

    def test_key_with_uuid_tenant(self, cache_no_redis):
        tid = str(uuid.uuid4())
        key = cache_no_redis._key("usage", tid, "stats")
        assert key == f"cache:usage:{tid}:stats"


# ── Behaviour tests with mocked Redis ────────────────────────────────────────

class TestWithMockedRedis:
    def test_available_true_when_redis_set(self, cache_with_redis):
        assert cache_with_redis.available is True

    def test_get_hit_returns_deserialized_value(self, cache_with_redis, mock_redis):
        import json
        mock_redis.get.return_value = json.dumps({"x": 1})
        with patch("app.utils.metrics.CACHE_HITS") as mock_hits, \
             patch("app.utils.metrics.CACHE_MISSES"):
            result = cache_with_redis.get("ns", "t1", "k1")
        assert result == {"x": 1}
        mock_redis.get.assert_called_once_with("cache:ns:t1:k1")

    def test_get_miss_returns_none(self, cache_with_redis, mock_redis):
        mock_redis.get.return_value = None
        with patch("app.utils.metrics.CACHE_HITS"), \
             patch("app.utils.metrics.CACHE_MISSES"):
            result = cache_with_redis.get("ns", "t1", "k1")
        assert result is None

    def test_set_calls_setex_with_correct_args(self, cache_with_redis, mock_redis):
        import json
        cache_with_redis.set("ns", "t1", "k1", {"v": 2}, ttl=120)
        mock_redis.setex.assert_called_once_with(
            "cache:ns:t1:k1",
            120,
            json.dumps({"v": 2}, default=str),
        )

    def test_set_uses_default_ttl_when_none(self, cache_with_redis, mock_redis):
        cache_with_redis.set("ns", "t1", "k1", "hello")
        _, ttl_arg, _ = mock_redis.setex.call_args[0]
        assert ttl_arg == CacheService.DEFAULT_TTL

    def test_get_or_set_returns_cached_value_without_calling_factory(self, cache_with_redis, mock_redis):
        import json
        mock_redis.get.return_value = json.dumps("cached_value")
        factory = MagicMock()
        with patch("app.utils.metrics.CACHE_HITS"), \
             patch("app.utils.metrics.CACHE_MISSES"):
            result = cache_with_redis.get_or_set("ns", "t1", "k1", factory)
        assert result == "cached_value"
        factory.assert_not_called()

    def test_get_or_set_calls_factory_on_miss_and_stores(self, cache_with_redis, mock_redis):
        import json
        mock_redis.get.return_value = None
        factory = MagicMock(return_value={"fresh": True})
        with patch("app.utils.metrics.CACHE_HITS"), \
             patch("app.utils.metrics.CACHE_MISSES"):
            result = cache_with_redis.get_or_set("ns", "t1", "k1", factory, ttl=30)
        assert result == {"fresh": True}
        factory.assert_called_once()
        mock_redis.setex.assert_called_once_with(
            "cache:ns:t1:k1",
            30,
            json.dumps({"fresh": True}, default=str),
        )

    def test_invalidate_specific_key(self, cache_with_redis, mock_redis):
        mock_redis.delete.return_value = 1
        count = cache_with_redis.invalidate("ns", "t1", key="config")
        mock_redis.delete.assert_called_once_with("cache:ns:t1:config")
        assert count == 1

    def test_invalidate_namespace_pattern(self, cache_with_redis, mock_redis):
        mock_redis.scan_iter.return_value = ["cache:ns:t1:a", "cache:ns:t1:b"]
        mock_redis.delete.return_value = 2
        count = cache_with_redis.invalidate("ns", "t1")
        mock_redis.scan_iter.assert_called_once_with(match="cache:ns:t1:*", count=100)
        assert count == 2

    def test_invalidate_namespace_no_keys(self, cache_with_redis, mock_redis):
        mock_redis.scan_iter.return_value = []
        count = cache_with_redis.invalidate("ns", "t1")
        mock_redis.delete.assert_not_called()
        assert count == 0

    def test_invalidate_tenant(self, cache_with_redis, mock_redis):
        mock_redis.scan_iter.return_value = ["cache:ns1:t1:k", "cache:ns2:t1:k"]
        mock_redis.delete.return_value = 2
        count = cache_with_redis.invalidate_tenant("t1")
        mock_redis.scan_iter.assert_called_once_with(match="cache:*:t1:*", count=500)
        assert count == 2

    def test_redis_exception_in_get_returns_none(self, cache_with_redis, mock_redis):
        mock_redis.get.side_effect = Exception("connection error")
        result = cache_with_redis.get("ns", "t1", "k1")
        assert result is None

    def test_redis_exception_in_set_does_not_raise(self, cache_with_redis, mock_redis):
        mock_redis.setex.side_effect = Exception("connection error")
        cache_with_redis.set("ns", "t1", "k1", "value")  # must not raise

    def test_redis_exception_in_invalidate_returns_zero(self, cache_with_redis, mock_redis):
        mock_redis.delete.side_effect = Exception("connection error")
        result = cache_with_redis.invalidate("ns", "t1", key="k")
        assert result == 0


# ── Integration: TenantSettingsService works without Redis ───────────────────

class TestTenantSettingsServiceWithoutRedis:
    """
    Verify TenantSettingsService behaves correctly when Redis is unavailable.
    Uses the real HTTP test client so the full FastAPI stack is exercised.
    """

    def test_register_and_usage_endpoint(self, client):
        from tests.conftest import auth_header, register_tenant

        user, token = register_tenant(client)
        resp = client.get("/api/v1/admin/settings/usage", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "documents" in data

    def test_invite_user_still_works(self, client):
        from tests.conftest import auth_header, register_tenant

        _, token = register_tenant(client)
        uid = uuid.uuid4().hex[:6]
        resp = client.post(
            "/api/v1/users/invite",
            json={
                "username": f"member_{uid}",
                "email": f"member_{uid}@test.com",
                "password": "Password1234!",
                "role": "member",
            },
            headers=auth_header(token),
        )
        assert resp.status_code == 201

    def test_settings_service_get_or_create_directly(self, db):
        from uuid import uuid4

        from app.services.tenant_settings_service import TenantSettingsService

        # We need a real tenant in DB — create a minimal one
        from app.models.tenant import Tenant

        tenant = Tenant(
            name="Cache Test Tenant",
            slug=f"cache-test-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        svc = TenantSettingsService(db)
        settings = svc.get_or_create(tenant.id)
        assert settings is not None
        assert settings.tenant_id == tenant.id

        # Calling again should return the same record (no duplicate)
        settings2 = svc.get_or_create(tenant.id)
        assert settings2.id == settings.id

    def test_get_usage_directly(self, db):
        from uuid import uuid4

        from app.models.tenant import Tenant
        from app.services.tenant_settings_service import TenantSettingsService

        tenant = Tenant(
            name="Usage Test Tenant",
            slug=f"usage-test-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        svc = TenantSettingsService(db)
        usage = svc.get_usage(tenant.id)
        assert usage["users"]["current"] == 0
        assert "documents" in usage
        assert "features" in usage
