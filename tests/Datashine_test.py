import asyncio
from DataShine import DataShine
import asyncUnittest
from asyncUnittest import AsyncTestCase
from DataShine.Gear import gears


class TestDataShine(AsyncTestCase):
    async def test_delete(self):
        ds = DataShine(self)
        self.assertIs(ds, gears[self])
        ds.delete()
        self.assertNotIn(self, gears.keys())

    async def test_data_multi_distribution(self):
        n = 4000

        async def shine():
            for i in range(n * 3):
                await DataShine(self).push_data(i + 1)

        async def period_change_remainder_waiter(remainder: int):
            nums = set()
            while True:
                new_data = await DataShine(self).wait_data_shine()
                if new_data % 3 == remainder:
                    nums.add(new_data)
                if new_data == 3 * n:
                    break

            return nums

        two_period_remainder_waiter_1_task = asyncio.create_task(period_change_remainder_waiter(1))
        two_period_remainder_waiter_2_task = asyncio.create_task(period_change_remainder_waiter(2))
        two_period_remainder_waiter_3_task = asyncio.create_task(period_change_remainder_waiter(0))

        asyncio.create_task(shine())
        self.assertEqual(await two_period_remainder_waiter_1_task, set(i for i in range(1, 3 * n + 1, 3)))
        self.assertEqual(await two_period_remainder_waiter_2_task, set(i for i in range(2, 3 * n + 1, 3)))
        self.assertEqual(await two_period_remainder_waiter_3_task, set(i for i in range(3, 3 * n + 1, 3)))


if __name__ == '__main__':
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncUnittest.run()
