"""
RazorShield AI — Pytest Compatibility Layer
Provides lightweight standard library fallbacks for pytest.raises and pytest.fixture
when external pytest package is unattached in the execution environment.
"""

from collections.abc import Callable
from typing import Any


class ExceptionContext:
    def __init__(self, expected_exception: type[BaseException]):
        self.expected_exception = expected_exception
        self.value: Any = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError(
                f"Expected exception {self.expected_exception.__name__} was not raised."
            )
        if issubclass(exc_type, self.expected_exception):
            self.value = exc_val
            return True  # Exception handled
        return False


class PytestCompat:
    @staticmethod
    def raises(expected_exception: type[BaseException]) -> ExceptionContext:
        return ExceptionContext(expected_exception)

    @staticmethod
    def fixture(func: Callable) -> Callable:
        return func


try:
    import pytest
except ImportError:
    pytest = PytestCompat()  # type: ignore
