"""Shared test fixtures."""
import pytest


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limiter storage before each test to prevent cross-test interference."""
    from backend.main import limiter as main_limiter
    from backend.routers.generate import limiter as router_limiter
    main_limiter.reset()
    router_limiter.reset()
    yield
    main_limiter.reset()
    router_limiter.reset()
