import threading


class ThreadManager:
    def __init__(self):
        self.threadList = []

    def addProcess(self, func, threadName, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.checkAlive()
        thread = threading.Thread(target=func, name=threadName, args=args, kwargs=kwargs)
        thread.start()
        self.threadList.append(thread)

    def checkAlive(self):
        for process in self.threadList:
            if not process.is_alive():
                self.threadList.remove(process)

    def cleanup(self):
        for process in self.threadList:
            process.terminate()
