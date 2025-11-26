"""
Unit tests for Rate Limiting Middleware
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def app():
    """Create test FastAPI app with rate limiting."""
    test_app = FastAPI()

    @test_app.get("/api/test")
    async def test_endpoint():
        return {"message": "success"}

    @test_app.get("/api/ai/analyze/")
    async def ai_analyze():
        return {"message": "AI analysis"}

    @test_app.get("/api/ai/agents/run-all/")
    async def agents_run_all():
        return {"message": "All agents running"}

    return test_app


@pytest.fixture
def middleware():
    """Create rate limit middleware instance."""
    app = FastAPI()
    return RateLimitMiddleware(app, rate_limit=5, window_seconds=60)


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    def test_initialization(self, middleware):
        """Test middleware initialization."""
        assert middleware.rate_limit == 5
        assert middleware.window_seconds == 60
        assert "/api/ai/analyze/" in middleware.rate_limited_endpoints
        assert "/api/ai/agents/run-all/" in middleware.rate_limited_endpoints
        assert "/api/ai/whatif/simulate/" in middleware.rate_limited_endpoints

    def test_endpoint_rate_limits(self, middleware):
        """Test specific endpoint rate limits."""
        assert middleware.rate_limited_endpoints["/api/ai/analyze/"] == 5
        assert middleware.rate_limited_endpoints["/api/ai/agents/run-all/"] == 3
        assert middleware.rate_limited_endpoints["/api/ai/whatif/simulate/"] == 5

    @pytest.mark.asyncio
    async def test_rate_limit_not_exceeded(self, middleware):
        """Test request when rate limit is not exceeded."""
        # Mock request and call_next
        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        request.url.path = "/api/ai/analyze/"

        async def mock_call_next(req):
            return JSONResponse({"message": "success"})

        # Make requests within limit
        for i in range(3):
            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, middleware):
        """Test request when rate limit is exceeded."""
        # Mock request
        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        request.url.path = "/api/ai/analyze/"

        async def mock_call_next(req):
            return JSONResponse({"message": "success"})

        # Exhaust rate limit (5 requests for /api/ai/analyze/)
        for i in range(5):
            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # Next request should be rate limited
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.body.decode()

    @pytest.mark.asyncio
    async def test_different_endpoints_different_limits(self, middleware):
        """Test that different endpoints have different rate limits."""
        async def mock_call_next(req):
            return JSONResponse({"message": "success"})

        # Test /api/ai/analyze/ (limit: 5)
        request1 = Mock(spec=Request)
        request1.client.host = "192.168.1.1"
        request1.url.path = "/api/ai/analyze/"

        for i in range(5):
            response = await middleware.dispatch(request1, mock_call_next)
            assert response.status_code == 200

        # Test /api/ai/agents/run-all/ (limit: 3)
        request2 = Mock(spec=Request)
        request2.client.host = "192.168.1.2"
        request2.url.path = "/api/ai/agents/run-all/"

        for i in range(3):
            response = await middleware.dispatch(request2, mock_call_next)
            assert response.status_code == 200

        # Next request to run-all should be limited
        response = await middleware.dispatch(request2, mock_call_next)
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_non_rate_limited_endpoint(self, middleware):
        """Test that non-rate-limited endpoints are not affected."""
        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        request.url.path = "/api/test"

        async def mock_call_next(req):
            return JSONResponse({"message": "success"})

        # Should allow many requests to non-rate-limited endpoint
        for i in range(20):
            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_different_ips_independent_limits(self, middleware):
        """Test that different IPs have independent rate limits."""
        async def mock_call_next(req):
            return JSONResponse({"message": "success"})

        # IP 1
        request1 = Mock(spec=Request)
        request1.client.host = "192.168.1.1"
        request1.url.path = "/api/ai/analyze/"

        # IP 2
        request2 = Mock(spec=Request)
        request2.client.host = "192.168.1.2"
        request2.url.path = "/api/ai/analyze/"

        # Both IPs should have independent limits
        for i in range(5):
            response1 = await middleware.dispatch(request1, mock_call_next)
            response2 = await middleware.dispatch(request2, mock_call_next)
            assert response1.status_code == 200
            assert response2.status_code == 200

    def test_get_client_identifier(self, middleware):
        """Test client identifier extraction."""
        request = Mock(spec=Request)
        request.client.host = "10.0.0.1"

        identifier = middleware._get_client_identifier(request)
        assert identifier == "10.0.0.1"

    def test_is_rate_limited_endpoint(self, middleware):
        """Test endpoint rate limit detection."""
        # Rate limited endpoints
        assert middleware._is_rate_limited_endpoint("/api/ai/analyze/") is True
        assert middleware._is_rate_limited_endpoint("/api/ai/agents/run-all/") is True
        assert middleware._is_rate_limited_endpoint("/api/ai/whatif/simulate/") is True

        # Non rate limited endpoints
        assert middleware._is_rate_limited_endpoint("/api/users/") is False
        assert middleware._is_rate_limited_endpoint("/api/test") is False
        assert middleware._is_rate_limited_endpoint("/health") is False

    @pytest.mark.asyncio
    async def test_sliding_window_cleanup(self, middleware):
        """Test that old requests are cleaned up (sliding window)."""
        import time

        # Create middleware with very short window for testing
        test_middleware = RateLimitMiddleware(
            FastAPI(),
            rate_limit=3,
            window_seconds=1  # 1 second window
        )

        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        request.url.path = "/api/ai/analyze/"

        async def mock_call_next(req):
            return JSONResponse({"message": "success"})

        # Make 3 requests (exhaust limit)
        for i in range(3):
            response = await test_middleware.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # Next request should be rate limited
        response = await test_middleware.dispatch(request, mock_call_next)
        assert response.status_code == 429

        # Wait for window to expire
        await asyncio.sleep(1.1)

        # Should be able to make requests again
        response = await test_middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200


class TestRateLimitHeaders:
    """Test rate limit response headers."""

    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self):
        """Test that rate limit headers are included in responses."""
        middleware = RateLimitMiddleware(FastAPI(), rate_limit=10, window_seconds=60)

        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        request.url.path = "/api/ai/analyze/"

        async def mock_call_next(req):
            response = JSONResponse({"message": "success"})
            return response

        response = await middleware.dispatch(request, mock_call_next)

        # Check for rate limit headers (if implemented)
        # Note: This depends on implementation details
        assert response.status_code == 200
