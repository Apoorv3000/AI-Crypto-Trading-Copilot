"""Test configuration."""

import pytest


@pytest.fixture
def sample_prices():
    """Sample price data for testing."""
    return [100, 101, 102, 103, 104, 105, 104, 103, 102, 103, 104, 105, 106]


@pytest.fixture
def sample_volumes():
    """Sample volume data for testing."""
    return [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500, 1450, 1600, 1550]
