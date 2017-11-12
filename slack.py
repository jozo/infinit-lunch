import asyncio
from typing import Iterable


class Channel:
    """
    Represents one channel on a Slack team
    """

    def __init__(self, hook: str, aio_session) -> None:
        self.hook = hook
        self.aio_session = aio_session

    async def send(self, messages: Iterable):
        msgs = iter(messages)
        await self.aio_session.post(self.hook, json={'text': next(msgs)})

        futures = [self.aio_session.post(self.hook, json={'text': msg}) for msg in msgs]
        for future in asyncio.as_completed(futures):
            await future
