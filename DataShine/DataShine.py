import asyncio
from copy import deepcopy


class DataShine:
    def __init__(self):
        self._unlocked = asyncio.Event()
        self._unlocked.set()
        self._period_change_event = asyncio.Event()
        self._data_container = None

    async def push_data(self, data):
        '''
        Set the gear to carry a data to be taken, and shine the data to notify monitors new data coming.

        :param data:
        :return:
        '''
        self._data_container = data

        self._period_change_event.clear()
        self._period_change_event.set()
        self._period_change_event.clear()
        await asyncio.sleep(0)

    @property
    def data(self):
        return self._data_container

    async def wait_data_shine(self):
        '''
        Wait the shined data.

        :return:
        '''
        await self._period_change_event.wait()
        return deepcopy(self._data_container)
