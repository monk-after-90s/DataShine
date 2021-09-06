'''
Transfer an object to its gear, as an interface.
'''
import asyncio
import datetime
from copy import deepcopy

from ensureTaskCanceled import ensureTaskCanceled
from loguru import logger

gears = {}


class _LightGear:
    def __init__(self, obj):
        self.obj = obj
        self._unlocked = asyncio.Event()
        self._unlocked.set()
        self.assistant_tasks = []
        self.prev_period = None
        self.periods = []
        self._last_set_time: datetime.datetime = None
        self._period_change_event = asyncio.Event()

    def delete(self):
        '''
        Delete the gear. You'd better delete the gear when it is no more used.

        :return:
        '''
        if self.obj in gears.keys():
            gears.pop(self.obj)
        for task in self.assistant_tasks:
            asyncio.create_task(ensureTaskCanceled(task))

    def get_present_period(self):
        '''
        Get the present period of the target object.

        :return:
        '''
        if self.periods:
            return self.periods[-1]

    def last_set_time(self) -> datetime.datetime:
        '''
        Get the UTC datetime when the present period is set.

        :return:
        '''
        return self._last_set_time

    def get_periods(self):
        '''
        Get the periods of the target object.

        :return:
        '''
        return self.periods

    async def set_period(self, period_name: str):
        await asyncio.sleep(0)
        if self._unlocked.is_set():
            if self.get_present_period() == period_name:
                raise ValueError(f'The period_name={period_name} to be set is already set.')
            if period_name in self.periods:
                self.periods.remove(period_name)
            self.periods.append(period_name)
            self._last_set_time = datetime.datetime.now()
            logger.debug(f'Gear({repr(self.obj)}) is set to period {period_name}')
            self._period_change_event.clear()
            self._period_change_event.set()
            self._period_change_event.clear()
            await asyncio.sleep(0)
        else:
            raise PermissionError('The gear is locked.')

    async def wait_change_period(self):
        '''
        Wait for the instant when the period is changed.

        :return:
        '''
        await self._period_change_event.wait()

    async def wait_inside_period(self, period_name: str):
        '''
        Wait the time slot when the gear is inside period period_name. As logically, as long as the gear is inside period
        period_name, this coroutine is awaited immediately.

        :param period_name:
        :return:
        '''
        while self.get_present_period() != period_name:
            await self.wait_change_period()

    async def wait_outside_period(self, period_name: str):
        '''
        Wait the time slot when the gear is outside period period_name. As logically, as long as the gear is outside period
        period_name, this coroutine is awaited immediately.

        :param period_name:
        :return:
        '''
        while self.get_present_period() == period_name:
            await self.wait_change_period()

    async def wait_enter_period(self, period_name: str):
        '''
        Wait the instant when the gear enters period period_name.

        :param period_name:
        :return:
        '''
        if self.get_present_period() == period_name:
            await self.wait_outside_period(period_name)
        await self.wait_inside_period(period_name)

    async def wait_exit_period(self, period_name: str):
        '''
        Wait the instant when the gear exits period period_name.

        :param period_name:
        :return:
        '''
        if self.get_present_period() != period_name:
            await self.wait_inside_period(period_name)
        await self.wait_outside_period(period_name)

    def lock(self):
        '''
        Lock the period of the gear.

        :return:
        '''
        self._unlocked.clear()

    def unlock(self):
        '''
        Unlock the period of the gear after the gear is locked.

        :return:
        '''
        self._unlocked.set()

    async def wait_unlock(self):
        '''
        wait the gear to be unlocked.

        :return:
        '''
        await asyncio.create_task(self._unlocked.wait())


class _DataShine(_LightGear):
    def __init__(self, obj):
        super(_DataShine, self).__init__(obj)
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

    async def wait_data_shine(self):
        '''
        Wait the shined data.

        :return:
        '''
        await self._period_change_event.wait()
        return deepcopy(self._data_container)


def Gear(obj) -> _LightGear:
    if obj not in gears.keys():
        gears[obj] = _LightGear(obj)
    return gears[obj]


def DataShine(obj) -> _DataShine:
    if obj not in gears.keys():
        gears[obj] = _DataShine(obj)
    return gears[obj]


if __name__ == '__main__':
    async def test():
        pass


    loop = asyncio.get_event_loop()
    loop.create_task(test())
    loop.run_forever()
