import json
from typing import Iterable


class Channel:
    """
    Represents one channel on a Slack team
    """

    def __init__(self, hook: str, http) -> None:
        self.hook = hook
        self.http = http

    def send(self, messages: Iterable):
        for msg in messages:
            self.http.post(self.hook, data=json.dumps({'text': msg}))
