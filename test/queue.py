import asyncio
import threading
import time


class QueueTest:
    def __init__(self):
        self.lock = threading.Lock()
        pass

    async def _consumer(self):
        while True:
            with self.lock:
                try:
                    self.queue.get_nowait()
                    await asyncio.sleep(1)
                    self.queue.task_done()
                except asyncio.QueueEmpty:
                    continue

    def producer(self):
        while True:
            self.queue.put_nowait(1)
            time.sleep(0.25)
            print(self.queue.qsize())


    async def _start_consumer(self):
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(maxsize=400000, loop=loop)
        await self._consumer()

    def start(self):
        self.thread = threading.Thread(target=asyncio.run, args=(self._start_consumer(),))
        self.thread.start()
        time.sleep(1)
        self.producer()



if __name__=="__main__":
    qt = QueueTest()
    qt.start()

    time.sleep(300)