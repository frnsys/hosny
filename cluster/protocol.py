import asyncio
import pickle
import logging
import cloudpickle
from hashlib import md5

logger = logging.getLogger(__name__)
sentinel = md5(b'7f57da0f9202f6b4df78e251058be6f0').hexdigest().encode()


def dumps(x):
    """serialize python object(s)"""
    try:
        return cloudpickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        logger.info("Failed to serialize %s", x)
        logger.exception(e)
        raise


def loads(x):
    """deserialize python object(s)"""
    try:
        return cloudpickle.loads(x)
    except Exception as e:
        logger.exception(e)
        raise


@asyncio.coroutine
def read(stream):
    """read data from a stream"""
    # hack for `stream.readuntil`
    buffer = b''
    while True:
        buffer += yield from stream.readexactly(1)
        if buffer.endswith(sentinel):
            break
    msg = buffer[:-len(sentinel)]
    msg = loads(msg)
    return msg


@asyncio.coroutine
def write(stream, msg):
    """write data to a stream"""
    msg = dumps(msg)
    yield stream.write(msg + sentinel)

