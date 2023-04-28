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
        port: Port number.
        host: Host address on which the port should exist.
        timeout: In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connection after time specified in `timeout`.
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
                _logger.error('Waited too long for the port "{}" on host "{}" to start accepting connections.'.format(port, host))
                break
