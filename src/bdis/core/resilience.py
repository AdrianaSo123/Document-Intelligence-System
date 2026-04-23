import time
import logging
from functools import wraps
from typing import Callable, Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class CircuitBreakerError(Exception):
    """Raised when the circuit breaker is open."""
    pass

class CircuitBreaker:
    """
    Simple Circuit Breaker implementation.
    """
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit Breaker HALF_OPEN: Attempting recovery.")
                else:
                    raise CircuitBreakerError("Circuit is OPEN. Request blocked.")

            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failures = 0
                    logger.info("Circuit Breaker CLOSED: Recovery successful.")
                return result
            except Exception as e:
                self.failures += 1
                self.last_failure_time = time.time()
                if self.failures >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"Circuit Breaker OPEN: Failure threshold reached. Error: {e}")
                raise e
        return wrapper

# BREAKER REGISTRY: Ensures breakers are shared across calls to the same service
_breakers: Dict[str, CircuitBreaker] = {}

def get_breaker(name: str, threshold=5, timeout=30) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(threshold, timeout)
    return _breakers[name]

def resilience_wrapper(service_name: str):
    """
    Returns a decorator that applies Retry and a SHARED Circuit Breaker.
    """
    def decorator(func: Callable) -> Callable:
        # 1. Apply Retry Logic
        retrying_func = retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((Exception)),
            reraise=True
        )(func)

        # 2. Apply SHARED Circuit Breaker
        breaker = get_breaker(service_name)
        return breaker(retrying_func)
    
    return decorator
