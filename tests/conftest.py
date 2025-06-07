from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_now_hour():
    def create(hour):
        mock_now = Mock(hour=hour)
        return mock_now

    return create
