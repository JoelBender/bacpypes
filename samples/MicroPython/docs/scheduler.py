try:
    # import microsecond ticks from micropython utime module
    from utime import ticks_ms
except ImportError:
    # if running on standard python, create the ticks_ms functionality
    from time import time

    def ticks_ms():
        return time() * 1000

# enabling print functions for basic debugging
debug = True

"""
TODOs
- implement better solution for `function.__name__` support
- support for repeat functions that only repeat a certain number of times
- function to remove repeat task
- migrate to async when fully supported by mycropython
- implement support for watching UDP sockets for data and provide callbacks
"""


class Scheduler:
    """
    This is a scheduling program that allows tasks to be scheduled to be done in the future or on a repeat in
    a single threaded application.

    Watchdog timer: the watchdog parameter enables handlers for what to do if section of the code fail. This is
                    useful in a micropython device for resetting the device if there is an error.

    """
    def __init__(self, watchdog=False):
        self.tasks = []
        self.watchdog = watchdog

    def main_loop(self, func):
        """
        This is the main loop decorator that wraps the main program. It checks the list of tasks for anything
        that is due to be executed.
        """

        if debug: print("Scheduler started at", round(ticks_ms()))

        while True:
            try:
                if self.tasks:
                    for task in self.tasks:
                        if ticks_ms() >= task.exec_time:
                            if debug: print("\ntime for task:", task.name)
                            task.func()

                            if task.repeat:
                                if debug: print("\n", task.name, "tasks has repeat")
                                if debug: print(task.name, "task will be done again @", task.exec_time)
                                task.exec_time = round(ticks_ms() + (task.delay * 1000))

                            else:
                                if debug: print("deleting task:", task.name)
                                del self.tasks[self.tasks.index(task)]

            except Exception as err:
                if debug: print('Scheduler error:', err)
                # TODO: save exception to log
                # for now the watchdog just prints 'reboot'
                if self.watchdog: print('reboot')
            try:
                func()
            except Exception as err:
                if debug: print('Main function error:', err)
                # TODO: save exception to log
                # for now the watchdog just prints 'reboot'
                if self.watchdog: print("reboot")

    def add_task(self, task):
        """
        :param task:
            The task object to be added to the list of tasks
        :return:
            None
        """
        if debug: print("registering task:", task.name)
        self.tasks.append(task)

    class Task:
        """
        Task object holds the information about a task to be completed

        NOTE: micropython does not support the '__name__' attribute for functions so the name of the function has
            to be added manually. A better solution for this is on the TODO list.
        """
        def __init__(self, func, name, delay, repeat=False):
            """

            :param func:
                the function to be executed
            :param name:
                String: the name of the function
            :param delay:
                Int: the delay before the function is executed
            :param repeat:
                Bool: is this a repeating function or a one-shot
            """
            self.delay = delay
            self.func = func
            self.func_name = name
            self.repeat = repeat
            self.exec_time = round(ticks_ms() + (delay * 1000))
            if repeat:
                self.name = 'Do ' + name + ' every ' + str(delay)
            else:
                self.name = 'Do ' + name + ' @ ' + str(self.exec_time)

        def __str__(self):
            """ Make the printed object easier to read."""
            return '<' + self.__class__.__name__ + ': ' + self.name + '>\n  <delay: ' + \
                   str(self.delay) + '>\n  <func: ' + self.func_name + '>\n  <repeat: ' + str(self.repeat) + '>'


if __name__ == "__main__":
    """ TESTING """
    # function for task 1
    def bob():
        print("bob says hello")

    # function for task 2
    def mike():
        print("mike says hello")

    # create the scheduler
    sch = Scheduler()

    # create bob and mike tasks. Mike task is repeating
    bob_task = sch.Task(bob, 'bob', 2)
    mike_task = sch.Task(mike, 'mike', 5, repeat=True)

    # add tasks to list of tasks
    sch.add_task(bob_task)
    sch.add_task(mike_task)

    # create the main program and use the scheduler main_loop as a decorator.
    # NOTE: any `while`, `sleep` or other blocking function in here will throw off the scheduler
    @sch.main_loop
    def main():
        pass
