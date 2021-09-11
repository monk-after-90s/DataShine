import asyncio
from DataShine import DataShine
import asyncUnittest
from asyncUnittest import AsyncTestCase


class TestDataShine(AsyncTestCase):
    async def test_simple_usage(self):
        ds = DataShine()

        async def push_loop():
            n = 0
            while n < 10:
                await ds.push_data(n)
                n += 1
                await asyncio.sleep(0.1)

        asyncio.create_task(push_loop())

        data_set = []

        async def waiter():
            while True:
                data_set.append(await ds.wait_data_shine())
                self.assertEqual(data_set[-1], ds.data)

        await asyncio.wait([waiter()], timeout=1)
        self.assertEqual(data_set, [i for i in range(10)])

    async def test_closed(self):
        ds = DataShine()
        await ds.close()
        error_waited = False
        try:
            await ds.push_data('')
        except RuntimeError:
            error_waited = True
        self.assertTrue(error_waited)

        error_waited = False
        try:
            await ds.wait_data_shine()
        except RuntimeError:
            error_waited = True
        self.assertTrue(error_waited)

    async def test_data_multi_distribution(self):
        n = 10
        ds = DataShine()

        async def shine():
            for i in range(n * 3):
                await ds.push_data(i + 1)

        async def period_change_remainder_waiter(remainder: int):
            nums = set()
            while True:
                new_data = await ds.wait_data_shine()
                self.assertEqual(new_data, ds.data)
                if new_data % 3 == remainder:
                    nums.add(new_data)
                if new_data == 3 * n:
                    break
                self.assertEqual(new_data, ds.data)

            return nums

        two_period_remainder_waiter_1_task = asyncio.create_task(period_change_remainder_waiter(1))
        two_period_remainder_waiter_2_task = asyncio.create_task(period_change_remainder_waiter(2))
        two_period_remainder_waiter_3_task = asyncio.create_task(period_change_remainder_waiter(0))

        asyncio.create_task(shine())
        self.assertEqual(await two_period_remainder_waiter_1_task, set(i for i in range(1, 3 * n + 1, 3)))
        self.assertEqual(await two_period_remainder_waiter_2_task, set(i for i in range(2, 3 * n + 1, 3)))
        self.assertEqual(await two_period_remainder_waiter_3_task, set(i for i in range(3, 3 * n + 1, 3)))

    async def test_compressed_push_data(self):
        ds = DataShine()

        async def push_loop():
            for i in range(10):
                asyncio.create_task(ds.push_data(i))

        asyncio.create_task(push_loop())

        data_set = set()

        async def waiter():
            while True:
                data_set.add(await ds.wait_data_shine())

        await asyncio.wait([waiter()], timeout=1)
        self.assertEqual(data_set, {i for i in range(10)})


if __name__ == '__main__':
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncUnittest.run()
