import asyncio
import pickle
import logging
import dill
from hashlib import md5

logger = logging.getLogger('cluster')
sentinel = md5(b'SENTINEL').hexdigest().encode() # eh what should this be


def dumps(x):
    """serialize python object(s)"""
    try:
        return dill.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        logger.info("Failed to serialize %s", x)
        logger.exception(e)
        raise


def loads(x):
    """deserialize python object(s)"""
    try:
        return dill.loads(x)
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

