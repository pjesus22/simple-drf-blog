from datetime import timedelta

from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware


def assert_datetimes_close(actual_str, expected_dt, delta=timedelta(seconds=1)):
    actual_dt = parse_datetime(actual_str)

    assert actual_dt is not None, "Datetime string could no be parsed"

    if not is_aware(expected_dt):
        expected_dt = make_aware(expected_dt)

    assert abs(actual_dt - expected_dt) <= delta
