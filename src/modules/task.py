import threading
from gi.repository import Gio

def Task(func):
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.start()
        return t

    return wrapper

class CTask(threading.Thread):
    def __init__(self, fn, cb=None, fn_args=[], cb_args=[]):
        super().__init__()

        self.fn = fn
        self.cb = cb or CTask.placeholder
        self.fn_args = fn_args
        self.cb_args = cb_args

    @staticmethod
    def placeholder(*_, **__):
        pass

    def run(self):
        self.fn(*self.fn_args)
        self.cb(*self.cb_args)