import asyncio

import asyncUnittest
from Gear_test import TestGear
from Datashine_test import TestDataShine
# from method_run_when_test import TestInstance_run_when
from run_when_test import TestRunWhen

import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
asyncUnittest.run()
