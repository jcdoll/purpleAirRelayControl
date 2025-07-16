from utils import connection_retry


class _Flaky:
    def __init__(self, fail_times=1, return_value=10):
        self.fail_times = fail_times
        self.calls = 0
        self.return_value = return_value

    def __call__(self):
        if self.calls < self.fail_times:
            self.calls += 1
            raise RuntimeError("flaky")
        return self.return_value


def test_retry_operation_eventual_success():
    flaky = _Flaky(fail_times=2, return_value=99)
    result = connection_retry.retry_operation(
        flaky, max_attempts=5, delay_ms=0, context="flaky"
    )
    assert result == 99
    # Should have been called 3 times (2 failures + success)
    assert flaky.calls == 2  # fail_times only counts failures


def test_retry_operation_failure_returns_none():
    flaky = _Flaky(fail_times=5)
    result = connection_retry.retry_operation(
        flaky, max_attempts=3, delay_ms=0, context="flaky"
    )
    assert result is None


def test_connection_state_transitions():
    state = connection_retry.ConnectionState("wifi")
    assert not state.connected
    state.mark_success()
    assert state.connected
    assert state.failure_count == 0
    state.mark_failure()
    assert not state.connected
    assert state.failure_count == 1
    assert state.should_retry(max_failures=2)
    state.mark_failure()
    assert not state.should_retry(max_failures=2)
