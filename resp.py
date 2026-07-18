class ProtocolError(Exception):
    pass


def try_parse(buf):
    """
    Try to pull one full command out of buf.
    Returns (args, consumed_bytes) if a complete command is present,
    or (None, 0) if buf doesn't yet contain a full command (need more data).
    args is a list of bytes objects, e.g. [b"SET", b"foo", b"bar"].
    """
    if not buf:
        return None, 0

    # redis clients send commands as RESP arrays. eg:
    # *2
    # $4
    # reject anything that isn't an array.
    # PING
    if buf[0:1] != b"*":
        # only supporting the array-of-bulk-strings form clients actually send
        raise ProtocolError("expected array")

    line_end = buf.find(b"\r\n")
    if line_end == -1:
        return None, 0  # haven't even got the array header yet

    num_args = int(buf[1:line_end])
    pos = line_end + 2
    args = []

    for _ in range(num_args):
        if pos >= len(buf) or buf[pos:pos + 1] != b"$":
            return None, 0  # next bulk string header hasn't arrived yet

        header_end = buf.find(b"\r\n", pos)
        if header_end == -1:
            return None, 0

        length = int(buf[pos + 1:header_end])
        value_start = header_end + 2
        value_end = value_start + length

        if value_end + 2 > len(buf):
            return None, 0  # value bytes or trailing CRLF not fully arrived
        # save argument
        args.append(buf[value_start:value_end])
        pos = value_end + 2  # skip past value + its CRLF

    # returns the parsed command and the number of bytes consumed
    return args, pos


# Serializers

# resp simple strings start with +
def simple_string(s):
    return b"+" + s.encode() + b"\r\n"

# resp erros start with -


def error(msg):
    return b"-" + msg.encode() + b"\r\n"

# resp integers start with :


def integer(n):
    return b":" + str(n).encode() + b"\r\n"


def bulk_string(s):
    if s is None:
        return b"$-1\r\n"

    # convert strings into bytes if needed
    b = s if isinstance(s, bytes) else s.encode()
    return b"$" + str(len(b)).encode() + b"\r\n" + b + b"\r\n"

# bulk_string("hello") becomes:
#
# $5
# hello
#
# where:
#   5 = number of bytes in the string
#   hello = the actual value


def array(items):
    # items is a list of already-serialized bytes (mix types freely)
    body = b"".join(items)
    return b"*" + str(len(items)).encode() + b"\r\n" + body


def null_array():
    return b"*-1\r\n"
