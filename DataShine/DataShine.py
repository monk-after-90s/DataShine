import asyncio
import functools
from copy import deepcopy
from ensureTaskCanceled import ensureTaskCanceled


def _no_closed(method):
    '''
    Can not be run when closed.

    :return:
    '''
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        self = args[0]
        if self._closed:
            raise RuntimeError(f'{repr(self)} is already closed.')
        return method(*args, **kwargs)

    return wrapper


class DataShine:
    def __init__(self):
        self._unlocked = asyncio.Event()
        self._unlocked.set()
        self._period_change_event = asyncio.Event()
        self._data_container = None
        self._q = asyncio.Queue()
        self._q_hanler_task = asyncio.create_task(self._q_hanler())
        self._closed = False

    async def close(self):
        '''
        Close the DataShine instance.

        :return:
        '''
        await ensureTaskCanceled(self._q_hanler_task)
        self._closed = True

    async def _q_hanler(self):
        while True:
            new_data = await self._q.get()
            self._q.task_done()
            self._data_container = new_data
            self._period_change_event.clear()
            self._period_change_event.set()
            self._period_change_event.clear()
            await asyncio.sleep(0)

    @_no_closed
    async def push_data(self, data):
        '''
        Set the lamp to carry a data to be taken, and shine the data to notify monitors new data coming.

        :param data:
        :return:
        '''
        self._q.put_nowait(data)

    @property
    def data(self):
        '''
        Query the data last pushed.

        :return:
        '''
        return self._data_container

    @_no_closed
    async def wait_data_shine(self):
        '''
        Wait the shined data. If you wait too later, you will lose the chance to get the data. If you can not wait the data
        in time every time but have to handle all the data, you can cache data in a instance of asyncio.Queue.

        :return:
        '''
        await self._period_change_event.wait()
        return deepcopy(self._data_container)


if __name__ == '__main__':
    async def test():
        pass


    asyncio.create_task(test())
