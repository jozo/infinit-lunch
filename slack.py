from typing import Iterable


def format_msg(msg):
    if msg.startswith("https://"):
        return {
            "blocks": [
                {
                    "type": "image",
                    "image_url": msg,
                    "alt_text": "Restaurant menu.",
                }
            ]
        }
    else:
        return {"text": msg}


class Channel:
    """
    Represents one channel on a Slack team
    """

    def __init__(self, hook: str, aio_session) -> None:
        self.hook = hook
        self.aio_session = aio_session

    async def send(self, messages: Iterable):
        for msg in messages:
            await self.aio_session.post(self.hook, json=format_msg(msg))
