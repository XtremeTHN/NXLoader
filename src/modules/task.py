import threading
from threading import Event

from gi.repository import Gio

class Task(threading.Thread):
    unfinished_stoppable_tasks = []
    def __init__(self, func=None, args=[], kwargs=[]):
        """
        Initializes a Task object.
        This class is used to run a function in a separate thread.

        Args:
            func: The function to be called when the task is run.
            args: A list of arguments to be passed to the function.
            kwargs: A dictionary of keyword arguments to be passed to the function.

        """
        
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

def task(func):
    """
    Decorator to run a function asynchronously in a separate thread.

    Args:
        func: The function to be executed in a background thread.

    Returns:
        A wrapper function that, when called, will execute the given
        function in a new Task thread.
    """

    def wrapper(*args, **kwargs):
        t = Task(func=func, args=args, kwargs=kwargs)
        # Task.unfinished_stoppable_tasks.append(t)
        t.start()
    
    return wrapper

class CallbackTask(threading.Thread):
    def __init__(self, fn, cb, fn_args=[], fn_kwargs={}, cb_args=[], cb_kwargs={}):
        """
        This class executes a function in a separate thread and calls a callback function when the task is finished.

        Args:
            fn: The function to be executed in the thread.
            cb: The callback function to be executed after the task is finished.
            fn_args: A list of arguments to be passed to the function.
            cb_args: A list of arguments to be passed to the callback.
        """
        super().__init__()

        self.fn = fn
        self.cb = cb
        self.fn_args = fn_args
        self.fn_kwargs = fn_kwargs
        self.cb_args = cb_args
        self.cb_kwargs = cb_kwargs

    def run(self):
        self.fn(*self.fn_args, **self.fn_kwargs)
        self.cb(*self.cb_args, **self.cb_kwargs)

class RepeatTask(Task):
    """
        Repeat a function in a thread until the stop method is called
    """
    def __init__(self, function, args=[], kwargs={}):
        super().__init__(args=args, kwargs=kwargs)

        self.func = function
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
            self.func(*self.args, **self.kwargs)
        
        Task.unfinished_stoppable_tasks.remove(self)