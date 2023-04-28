import functools
import threading

class _PeriodicFunction():
    def __init__(self, function, every=0) -> None:
        self._function = function
        self.stopped = False

        if every <= 0:
            raise ValueError('Periodic time > 0')

        self._periodic_time = every

    def __call__(self, *args, **kwargs):
        if not self.stopped:
            threading.Timer(self._periodic_time, self, args=args, kwargs=kwargs).start()
            self._function(*args, **kwargs)

    def stop(self):
        self.stopped = True


def periodic(*, every):
    def decorator(function):
        periodicWrapper = _PeriodicFunction(function, every=1)
        @functools.wraps(function)
        def wrapper(self, *args, **kwargs):
            print(self, every, args, kwargs)
            periodicWrapper(self, *args, **kwargs)
        return wrapper
    return decorator
