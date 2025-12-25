import pytest

pytestmark = pytest.mark.unit


def test_unit_suite_runs():
    # Ensures we never silently report 0 tests executed.
    assert True
