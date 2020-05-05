class PlayerConnectionThreadHandler:
    def __init__(self, thread, status):
        self.thread = thread
        self.status = status

    def start(self):
        self.thread.start()
