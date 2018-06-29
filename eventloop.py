# Written by s4y @  https://github.com/s4y/runloop.py  -- license unknown

try:
    from queue import Queue
except ImportError:
    from Queue import Queue
from collections import namedtuple

Invocation = namedtuple('Invocation', ('fn', 'args', 'kwargs'))


class RunLoop:
    def __init__(self):
        self.queue = Queue()
        self.running = False

    def add(self, fn, args=(), kwargs={}):
        self.queue.put(Invocation(fn, args, kwargs))

    def every(self, fn, interval, args=(), kwargs={}):
        import threading
        invocation = Invocation(fn, args, kwargs)

        def do_repeat():
            event = threading.Event()
            while True:
                event.wait(interval)
                self.queue.put(invocation)

        thread = threading.Thread(target=do_repeat)
        thread.daemon = True
        thread.start()

    def run(self):
        self.running = True
        while self.running:
            inv = self.queue.get()
            inv.fn(*inv.args, **inv.kwargs)

    def stop(self):
        self.running = False

        def nop():  # no operation (like assembler instruction) does nothing
            pass

        self.add(nop)  # to make queue.get() call in run method quit and let while-loop stop

    def onLoop(self, fn):
        from functools import wraps
        @wraps(fn)
        def wrapper(*args, **kwargs):
            self.add(fn, args, kwargs)

        return wrapper
