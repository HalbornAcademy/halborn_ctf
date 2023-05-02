import types
import functools
import threading
from typing import Any

class _PeriodicFunction():
    def __init__(self, function, every=0) -> None:
        self._function = function
        self.stopped = False

        if every <= 0:
            raise ValueError('Periodic time > 0')

        self._periodic_time = every

    def __get__(self, obj, objtype):
        return types.MethodType(self, obj)

    def __call__(self, *args, **kwargs):
        if not self.stopped:
            threading.Timer(self._periodic_time, self, args=args, kwargs=kwargs).start()
            self._function(*args, **kwargs)

    def stop(self):
        self.stopped = True

def periodic(*, every: int):
    """It allows executing a function as a periodic function in a thread on the background.

    Args:
        every (int): The amount of seconds to wait to execute the function again. It should be bigger than 0.

    Example:

        .. code::

            @periodic(every=1)
            def function():
                print("HI")

            function() # Does start printing "HI" every 1 second

            function.stop() # Does stop the function execution

    Raises:
        ValueError: If the ``every`` parameter is set to 0.
    """
    def decorator(function):
        return _PeriodicFunction(function, every=every)
    return decorator
