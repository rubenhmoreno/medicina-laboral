import re

from app.core.ids import new_uuid7


def test_uuid7_is_v7_and_unique():
    a = new_uuid7()
    b = new_uuid7()
    assert a != b
    assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}$", str(a))


def test_uuid7_is_time_ordered():
    ids = [new_uuid7() for _ in range(50)]
    assert ids == sorted(ids)
