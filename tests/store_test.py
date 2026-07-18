import time
from store import Store


def test_basic_set_get():
    s = Store()
    s.set("foo", b"bar")
    assert s.get("foo") == b"bar"
    print("test_basic_set_get OK")


def test_missing_key():
    s = Store()
    assert s.get("nope") is None
    print("test_missing_key OK")


def test_delete():
    s = Store()
    s.set("foo", b"bar")
    assert s.delete("foo") is True
    assert s.get("foo") is None
    assert s.delete("foo") is False  # already gone
    print("test_delete OK")


def test_passive_expiry():
    s = Store()
    s.set("foo", b"bar", px=50)  # 50ms TTL
    assert s.get("foo") == b"bar"  # not expired yet
    time.sleep(0.1)
    assert s.get("foo") is None  # passive check on access should evict it
    assert "foo" not in s.data
    print("test_passive_expiry OK")


def test_set_clears_previous_ttl():
    s = Store()
    s.set("foo", b"bar", px=50)
    s.set("foo", b"baz")  # no px this time
    time.sleep(0.1)
    assert s.get("foo") == b"baz"  # should NOT have expired
    print("test_set_clears_previous_ttl OK")


def test_expire_and_ttl():
    s = Store()
    s.set("foo", b"bar")
    assert s.ttl("foo") == -1  # no TTL set
    assert s.expire("foo", 100) == 1
    remaining = s.ttl("foo")
    assert 0 < remaining <= 100
    assert s.expire("missing", 100) == 0
    assert s.ttl("missing") == -2
    print("test_expire_and_ttl OK")


def test_active_expire_cycle():
    s = Store()
    s.set("a", b"1", px=10)
    s.set("b", b"2", px=10)
    time.sleep(0.05)
    s.active_expire_cycle()
    assert "a" not in s.data
    assert "b" not in s.data
    print("test_active_expire_cycle OK")


if __name__ == "__main__":
    test_basic_set_get()
    test_missing_key()
    test_delete()
    test_passive_expiry()
    test_set_clears_previous_ttl()
    test_expire_and_ttl()
    test_active_expire_cycle()
    print("all passed")
