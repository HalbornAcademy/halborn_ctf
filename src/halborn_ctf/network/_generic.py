import socket
import logging
import time

_logger = logging.getLogger(__name__)

__all__ = [
    'wait_for_port'
]

def wait_for_port(port: int, host: str = 'localhost', timeout: float = 5.0):
    """Wait until a port starts accepting TCP connections.

    Args:
        port (int): The port to wait for
        host (str, optional): The host where the port should be waited for. Defaults to 'localhost'.
        timeout (float, optional): The amount in seconds to wait for before exiting. Defaults to 5.0.

    Raises:
        TimeoutError: The port isn't accepting connection after time specified in ``timeout``.
    """
    _logger.info('Waiting for port on "{}:{}"'.format(host, port))
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                _logger.info('Port "{}" found'.format(port))
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                TimeoutError('Waited too long for port "{}" on host "{}" to start accepting connections.'.format(port, host))

from contextlib import closing

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
