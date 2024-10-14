import asyncio
import threading
from asgiref.sync import sync_to_async

def run_delayed(task, delay):
    """
    Delay a task by a specified amount of time, and then run it synchronously.
    """
    async def async_task():
        await asyncio.sleep(delay)
        if asyncio.iscoroutinefunction(task):
            await task()
        else:
            await sync_to_async(task)()
    def run_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_task())
    threading.Thread(target=run_task).start()

        # async def my_async_function(current_hand):
        #     print("Starting async function...")
        #     await asyncio.sleep(5)
        #     await sync_to_async(deal_new_hand)(game=current_hand.game)
        #     print("Async function completed!")
        # # Run the async function in the background without waiting
        # def run_async_function():
        #     loop = asyncio.new_event_loop()  # Create a new event loop
        #     asyncio.set_event_loop(loop)
        #     loop.run_until_complete(my_async_function(current_hand))

        # threading.Thread(target=run_async_function).start()