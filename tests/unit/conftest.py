"""Override the root-level autouse fixture so unit tests don't need backend.main."""
import pytest


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """No-op override: unit tests don't need rate-limiter resets."""
    yield
