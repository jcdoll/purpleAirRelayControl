import time

from utils import connection_retry


def test_retry_operation_failure_then_success(monkeypatch):
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("boom")
        return "ok"

    start = time.time()
    result = connection_retry.retry_operation(
        flaky, max_attempts=5, delay_ms=0, context="flaky"
    )
    duration = time.time() - start
    assert result == "ok"
    assert len(calls) == 3
    # ensure back-off delay didn't sleep long (delay_ms=0)
    assert duration < 0.1


def test_retry_with_timeout(monkeypatch):
    calls = []

    def slow():
        calls.append(1)
        time.sleep(0.05)
        return "done"

    # Should succeed on first call within timeout
    result = connection_retry.retry_with_timeout(
        slow, timeout_sec=1, max_attempts=2, context="slow"
    )
    assert result == "done"

    # Simulate exceeding timeout by monkeypatching time.time()
    original_time = time.time

    def fake_time():
        return original_time() + 2  # pretend 2 seconds passed instantly

    monkeypatch.setattr(connection_retry.time, "time", fake_time)

    # Force timeout by using very small timeout_sec
    result = connection_retry.retry_with_timeout(
        lambda: "x", timeout_sec=0, max_attempts=1, context="too_slow"
    )
    assert result is None


def test_wait_for_condition_success():
    t0 = time.time()
    flag = {"ready": False}

    def condition():
        return flag["ready"]

    # flip flag after short delay
    def flip():
        flag["ready"] = True

    connection_retry.time.sleep(0.01)
    flip()

    assert connection_retry.wait_for_condition(
        condition, timeout_sec=1, check_interval=0.01
    )
    assert time.time() - t0 < 1


def test_connection_state():
    cs = connection_retry.ConnectionState("wifi")
    assert not cs.connected
    cs.mark_success()
    assert cs.connected and cs.failure_count == 0
    cs.mark_failure()
    assert not cs.connected and cs.failure_count == 1
    assert cs.should_retry(max_failures=2)
    cs.mark_failure()
    assert not cs.should_retry(max_failures=2)
    status = cs.get_status()
    assert status["name"] == "wifi" and status["total_attempts"] == 3
