import threading
from threading import Event

from gi.repository import Gio

class Task(threading.Thread):
    unfinished_stoppable_tasks = []
    def __init__(self, func=None, args=[], kwargs=[]):
        super().__init__()
        
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def set_function(self, func, args=[], kwargs={}):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        self.func(*self.args, **self.kwargs)
    
    @staticmethod
    def stop_unfinished_tasks():
        for t in Task.unfinished_stoppable_tasks:
            t.stop()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            self.set_function(func, args=args, kwargs=kwargs)
            self.start()
            return self
        
        return wrapper

# TODO: Change name
class CallbackTask(threading.Thread):
    def __init__(self, fn, cb=None, fn_args=[], cb_args=[]):
        super().__init__()

        self.fn = fn
        self.cb = cb or CallbackTask.placeholder
        self.fn_args = fn_args
        self.cb_args = cb_args

    @staticmethod
    def placeholder(*_, **__):
        pass

    def run(self):
        self.fn(*self.fn_args)
        self.cb(*self.cb_args)

class RepeatTask(Task):
    def __init__(self, callback):
        super().__init__()

        self.cb = callback
        self.stop_flag = threading.Event()
    
    def start(self):
        self.stop_flag.clear()
        Task.unfinished_stoppable_tasks.append(self)
        try:
            super().start()
        except RuntimeError:
            pass
    
    def stop(self):
        self.stop_flag.set()
    
    def run(self):
        while self.stop_flag.is_set() is False:
            self.cb()