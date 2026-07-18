import resp


def test_full_command():
    buf = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
    args, consumed = resp.try_parse(buf)
    assert args == [b"SET", b"foo", b"bar"], args
    assert consumed == len(buf), consumed
    print("test_full_command OK")


def test_partial_buffer_returns_none():
    full = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
    for cut in range(1, len(full)):
        args, consumed = resp.try_parse(full[:cut])
        assert args is None and consumed == 0, f"failed at cut={cut}: {args}"
    print("test_partial_buffer_returns_none OK")


def test_two_commands_back_to_back():
    buf = b"*1\r\n$4\r\nPING\r\n" + b"*1\r\n$4\r\nPING\r\n"
    args1, c1 = resp.try_parse(buf)
    assert args1 == [b"PING"]
    args2, c2 = resp.try_parse(buf[c1:])
    assert args2 == [b"PING"]
    assert c1 + c2 == len(buf)
    print("test_two_commands_back_to_back OK")


def test_serializers():
    assert resp.simple_string("OK") == b"+OK\r\n"
    assert resp.error("ERR bad") == b"-ERR bad\r\n"
    assert resp.integer(42) == b":42\r\n"
    assert resp.bulk_string("hi") == b"$2\r\nhi\r\n"
    assert resp.bulk_string(None) == b"$-1\r\n"
    assert resp.array([resp.bulk_string("a"), resp.bulk_string(
        "b")]) == b"*2\r\n$1\r\na\r\n$1\r\nb\r\n"
    print("test_serializers OK")


if __name__ == "__main__":
    test_full_command()
    test_partial_buffer_returns_none()
    test_two_commands_back_to_back()
    test_serializers()
    print("all passed")
