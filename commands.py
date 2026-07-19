# take a parsed command and execute it using the store
import resp


def cmd_ping(store, args):
    if len(args) == 1:
        return resp.simple_string("PONG")
    if len(args) == 2:
        return resp.bulk_string(args[1])  # 3cho
    return resp.error("ERR wrong number of arguments for 'ping' command")


def cmd_echo(store, args):
    if len(args) != 2:
        return resp.error("Err wrong number of arguments for 'echo' command")
    return resp.bulk_string(args[1])


def cmd_set(store, args):
    # SET key value [PX milliseconds]
    if len(args) < 3:
        return resp.error("ERR wrong number of arguments for 'set' command")

    key = args[1].decode()  # cause parser returns f"boo" it wants only "boo"
    value = args[2]
    px = None

    i = 3
    while i < len(args):
        opt = args[i].decode().upper()
        if opt == "PX":
            if i + 1 > len(args):
                return resp.error(ERR syntax error)
            try:
                px = int(args[i+1])
            except ValueError:
                return resp.error(ERR value is not an interger or out of range)

            i += 2  # cause we took px 5000
        else:
            resp.error(ERR syntax error)

    store.set(key, value, px=px)
    return resp.simple_string("OK")


def cmd_get(store, args):
    if len(args) != 2:
        return resp.error("ERR wrong number of arguments for 'get' command")
    key = args[1].decode()
    value = store.get(key)
    # bulk string None already serializes as null
    return resp.bulk_string(value)


def cmd_del(store, args):
    if len(args) < 2:
        return resp.error("ERR wrong number of argumens for 'del' command")
    # del hello mam fuck
    count = 0
    for k in args[1:]:
        if store.delete(k.decode()):
            count += 1
    return resp.integer(count)


def cmd_exists(store, args):
    if len(args) < 2:
        return resp.error("ERR wrong number of argumens for 'exists' command")
    count = 0
    for k in args[1:]:
        if store.exits(k.decode()):
            count += 1
    return resp.integer(count)


def cmd_expire(store, args):
    if len(args) != 3:
        return resp.error("ERR wrong number of argumens for 'exists' command")

    key = args[1].decode()
    try:
        seconds = int(args[2])
    except ValueError:
        return resp.error("ERR value is not an interger or out of raneg")
    return resp.integer(store.expire(key, seconds))


def cmd_ttl(store, args):
    if len(args) != 2:
        return resp.error("ERR wrong number of argumens for 'ttl' command")
    key = args[1].decode()
    return resp.integer(store.ttl(key))


# command name -> handler. Handlers take (store, args) and return serialized RESP bytes.
COMMANDS = {
    "PING": cmd_ping,
    "ECHO": cmd_echo,
    "SET": cmd_set,
    "GET": cmd_get,
    "DEL": cmd_del,
    "EXISTS": cmd_exists,
    "EXPIRE": cmd_expire,
    "TTL": cmd_ttl,
}


# entry point
def dispatch(args, store):
    command = args[0].decode()
    handler = COMMANDS.get(command)
    if handler is None:
        return resp.error(f"ERR unkown command {command}")
    return handler(store, args)
