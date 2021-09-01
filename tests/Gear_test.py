import asyncio
from AsyncGear import Gear
import asyncUnittest
from asyncUnittest import AsyncTestCase
from AsyncGear.Gear import gears
import datetime


class TestGear(AsyncTestCase):
    async def test_delete(self):
        g = Gear(self)
        self.assertIs(g, gears[self])
        g.delete()
        self.assertTrue(self not in gears.keys())

    async def test_get_present_period(self):
        g = Gear(self)
        self.assertIs(None, g.get_present_period())
        await g.set_period('sleep')
        self.assertIs('sleep', g.get_present_period())
        await g.set_period('awaken')
        self.assertIs('awaken', g.get_present_period())

    async def test_last_set_time(self):
        g = Gear(self)
        self.assertIs(None, g.last_set_time())
        await g.set_period('sleep')
        self.assertLessThan(g.last_set_time().timestamp() - datetime.datetime.now().timestamp(), 0.05)
        await asyncio.sleep(1)
        await g.set_period('awaken')
        self.assertLessThan(g.last_set_time().timestamp() - datetime.datetime.now().timestamp(), 0.05)

    async def test_get_periods(self):
        g = Gear(self)
        await g.set_period('sleep')
        self.assertEqual(g.get_periods(), ['sleep'])
        await asyncio.sleep(0.1)
        await g.set_period('awaken')
        self.assertEqual(g.get_periods(), ['sleep', 'awaken'])
        await asyncio.sleep(0.1)
        await g.set_period('sleep')
        self.assertEqual(g.get_periods(), ['awaken', 'sleep'])

    async def test_set_period_and_lock(self):
        g = Gear(self)
        await g.set_period('sleep')
        self.assertIs('sleep', g.get_present_period())
        g.lock()

        waited = False
        try:
            await g.set_period('awaken')
        except PermissionError:
            waited = True
        self.assertTrue(waited)
        g.unlock()
        await g.set_period('awaken')
        self.assertIs('awaken', g.get_present_period())

        waited = False
        try:
            await g.set_period('awaken')
        except ValueError:
            waited = True
        self.assertTrue(waited)

    async def test_wait_change_period(self):
        g = Gear(self)

        async def waiter():
            await g.wait_change_period()
            return g.get_present_period()

        waiter_task = asyncio.create_task(waiter())
        await asyncio.sleep(0.1)
        await g.set_period('sleep')
        waited = False
        try:
            await asyncio.wait_for(waiter_task, 0.01)
        except asyncio.TimeoutError:
            waited = True
        self.assertIs(False, waited)
        self.assertEqual('sleep', await waiter_task)

    async def test_wait_inside_period(self):
        g = Gear(self)
        waiter_task = asyncio.create_task(g.wait_inside_period('sleep'))
        await asyncio.wait([waiter_task], timeout=1)
        self.assertTrue(not waiter_task.done())
        t = asyncio.get_running_loop().time()
        await asyncio.create_task(g.set_period('sleep'))
        await waiter_task
        t2 = asyncio.get_running_loop().time()
        self.assertEqual(0, round(t2 - t, 2))
        t3 = asyncio.get_running_loop().time()
        await g.wait_inside_period('sleep')
        self.assertEqual('sleep', g.get_present_period())
        t4 = asyncio.get_running_loop().time()
        self.assertEqual(0, round(t4 - t3, 2))

    async def test_wait_outside_period(self):
        g = Gear(self)
        await asyncio.create_task(g.set_period('sleep'))
        waiter_task = asyncio.create_task(g.wait_outside_period('sleep'))
        await asyncio.wait([waiter_task], timeout=1)
        self.assertTrue(not waiter_task.done())
        t = asyncio.get_running_loop().time()
        await asyncio.create_task(g.set_period('awaken'))
        await waiter_task
        self.assertEqual('awaken', g.get_present_period())
        t2 = asyncio.get_running_loop().time()
        self.assertEqual(0, round(t2 - t, 2))
        t3 = asyncio.get_running_loop().time()
        await g.wait_outside_period('sleep')
        t4 = asyncio.get_running_loop().time()
        self.assertEqual(0, round(t4 - t3, 2))

    async def test_wait_enter_period(self):
        g = Gear(self)
        waiter_task = asyncio.create_task(g.wait_enter_period('sleep'))
        await asyncio.wait([waiter_task], timeout=1)
        self.assertTrue(not waiter_task.done())
        t = asyncio.get_running_loop().time()
        await asyncio.create_task(g.set_period('sleep'))
        await waiter_task
        t2 = asyncio.get_running_loop().time()
        self.assertEqual(0, round(t2 - t, 2))
        self.assertEqual('sleep', g.get_present_period())
        waiter_task = asyncio.create_task(g.wait_enter_period('sleep'))
        await asyncio.wait([waiter_task], timeout=1)
        self.assertTrue(not waiter_task.done())

    async def test_wait_exit_period(self):
        g = Gear(self)
        await asyncio.create_task(g.set_period('sleep'))

        waiter_task = asyncio.create_task(g.wait_exit_period('sleep'))
        await asyncio.wait([waiter_task], timeout=1)
        self.assertTrue(not waiter_task.done())
        t = asyncio.get_running_loop().time()
        await asyncio.create_task(g.set_period('awaken'))
        await waiter_task
        t2 = asyncio.get_running_loop().time()
        self.assertEqual(0, round(t2 - t, 2))
        waiter_task = asyncio.create_task(g.wait_exit_period('sleep'))
        await asyncio.wait([waiter_task], timeout=1)
        self.assertTrue(not waiter_task.done())

    async def test_lock(self):
        g = Gear(self)
        g.lock()
        waited = False
        try:
            await asyncio.create_task(g.set_period('sleep'))
        except PermissionError:
            waited = True
        self.assertTrue(waited)

        async def delay_unlock():
            await asyncio.sleep(1)
            g.unlock()

        asyncio.create_task(delay_unlock())
        t = asyncio.get_running_loop().time()

        await g.wait_unlock()
        t2 = asyncio.get_running_loop().time()
        self.assertEqual(1, round(t2 - t, 1))
        await asyncio.create_task(g.set_period('awaken'))

    async def test_handle_period_then_set_period(self):
        q = asyncio.Queue()

        async def worker(name: str):
            '''工人等self的test2时期，就工作，工作完再等'''
            while True:
                await asyncio.create_task(Gear(name).set_period('waiting'))
                await asyncio.create_task(Gear(self).wait_enter_period('test2'))
                q.put_nowait({"time": asyncio.get_running_loop().time(), 'msg': 'start to work'})
                await asyncio.create_task(Gear(name).set_period('working'))
                await asyncio.create_task(asyncio.sleep(1))  # simulate work
                q.put_nowait({"time": asyncio.get_running_loop().time(), 'msg': 'end working'})  # 测试间隔1s
                # 测试在0.5s之后是test1时期

        # 激活两工人
        worker1_task = asyncio.create_task(worker('worker1'))

        worker2_task = asyncio.create_task(worker('worker2'))

        async def wait_worker_accomplish_working_then_set_period_test1():
            '''等待工人干完活就设置self到周期test1'''
            while True:
                wait_worker1_exit_working_task = asyncio.create_task(
                    Gear('worker1').wait_exit_period('working'))
                wait_worker2_exit_working_task = asyncio.create_task(
                    Gear('worker2').wait_exit_period('working'))
                await asyncio.ensure_future(
                    asyncio.gather(wait_worker1_exit_working_task, wait_worker2_exit_working_task))
                await asyncio.create_task(Gear(self).set_period('test1'))

        wait_worker_accomplish_working_then_set_period_test1_task = \
            asyncio.create_task(wait_worker_accomplish_working_then_set_period_test1())

        async def noticing_in_test2():
            '''提醒工人干活的时期'''
            while True:
                await asyncio.create_task(Gear(self).wait_inside_period('test2'))
                q.put_nowait(
                    {"time": asyncio.get_running_loop().time(), 'msg': 'In test2, the workers should be working.'})

                await asyncio.create_task(asyncio.sleep(0.05))  # 测试是处于工作时期内

        noticing_in_test2_task = asyncio.create_task(noticing_in_test2())

        async def set_test2():
            '''只要离开test2时期就1s后设置到test2时期让工人干活'''
            while True:
                await asyncio.create_task(Gear(self).wait_outside_period('test2'))
                await asyncio.create_task(asyncio.sleep(1))
                asyncio.create_task(Gear(self).set_period('test2'))  # 测试休息1s

        set_test2_task = asyncio.create_task(set_test2())

        work_start_time = None
        work_end_time = None
        work_end_time_count = 0
        tasks = []
        init_time = asyncio.get_running_loop().time()
        while asyncio.get_running_loop().time() - init_time <= 5:
            new_msg = await asyncio.create_task(q.get())
            if new_msg['msg'] == 'start to work':
                work_start_time = new_msg['time']
                if work_end_time:
                    self.assertEqual(round(work_start_time - work_end_time), 1)

            elif new_msg['msg'] == 'end working':
                work_end_time = new_msg['time']
                self.assertEqual(round(work_end_time - work_start_time), 1)

                async def test_in_test1_period_after_end_working():
                    await asyncio.create_task(asyncio.sleep(0.5))
                    self.assertEqual('test1', Gear(self).get_present_period())

                tasks.append(asyncio.create_task(test_in_test1_period_after_end_working()))

                # 俩工人第一次完工，复位
                work_end_time_count += 1
                if work_end_time_count % 2 == 0:
                    work_start_time = work_end_time = None
            elif new_msg['msg'] == 'In test2, the workers should be working.':
                if work_start_time:
                    self.assertLessThan(new_msg['time'] - work_start_time, 1)
            q.task_done()
        [await task for task in tasks]

    async def test_simple_high_frequence(self):
        Gear(self).count = 10002

        async def shine():
            for i in range(Gear(self).count):
                if Gear(self).get_present_period() == 'test2':
                    Gear(self).count -= 1
                    await asyncio.create_task(Gear(self).set_period('test1'))
                else:
                    Gear(self).count -= 1
                    await asyncio.create_task(Gear(self).set_period('test2'))

        nums = set()
        asyncio.create_task(shine())
        while True:
            await Gear(self).wait_change_period()
            nums.add(Gear(self).count)
            if Gear(self).count == 0:
                break
        self.assertEqual(len(nums), 10002)
        self.assertEqual(set(i for i in range(10002)), nums)

    async def test_multi_high_frequence(self):
        n = 4000

        Gear(self).count = n * 3

        async def shine():
            for i in range(Gear(self).count):
                if Gear(self).get_present_period() == 'test2':
                    await asyncio.create_task(Gear(self).set_period('test1'))
                    Gear(self).count -= 1
                else:
                    await asyncio.create_task(Gear(self).set_period('test2'))
                    Gear(self).count -= 1

        asyncio.create_task(shine())

        async def period_change_remainder_waiter(remainder: int):
            nums = set()
            while True:
                await Gear(self).wait_change_period()
                if Gear(self).count % 3 == remainder:
                    nums.add(Gear(self).count)
                if Gear(self).count == 1:
                    break

            return nums

        two_period_remainder_waiter_1_task = asyncio.create_task(period_change_remainder_waiter(1))
        two_period_remainder_waiter_2_task = asyncio.create_task(period_change_remainder_waiter(2))
        two_period_remainder_waiter_3_task = asyncio.create_task(period_change_remainder_waiter(0))

        self.assertEqual(n,
                         len(await two_period_remainder_waiter_1_task),
                         len(await two_period_remainder_waiter_2_task),
                         len(await two_period_remainder_waiter_3_task))
        self.assertEqual(await two_period_remainder_waiter_1_task, set(i for i in range(1, 3 * n + 1, 3)))
        self.assertEqual(await two_period_remainder_waiter_2_task, set(i for i in range(2, 3 * n + 1, 3)))
        self.assertEqual(await two_period_remainder_waiter_3_task, set(i for i in range(3, 3 * n + 1, 3)))

    # async def test_bind_obj_has_dict_property(self):
    #     class C:
    #         a = {}
    #
    #     Gear(C).add_periods('1')
    #     Gear(C).add_periods('2')
    #     self.assertEqual('1', Gear(C).get_present_period())
    #     waiter = asyncio.create_task(Gear(C).wait_enter_period('2'))
    #     await Gear(C).set_period('2')
    #     await waiter
    #


if __name__ == '__main__':
    # asyncUnittest.run()
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncUnittest.run()
