from datetime import timedelta

from django.utils.dateparse import parse_datetime


def assert_datetimes_close(actual_str, expected_dt, delta=timedelta(seconds=1)):
    actual_dt = parse_datetime(actual_str)

    assert actual_dt is not None, "Datetime string could no be parsed"

    assert abs(actual_dt - expected_dt) <= delta
